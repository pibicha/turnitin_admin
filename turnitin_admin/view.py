import logging
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST
from django.http import JsonResponse, HttpResponseBadRequest, FileResponse
from django.conf import settings
from api.models import WebUser, WebUserAssignments
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from pypinyin import lazy_pinyin
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import transaction
from pathlib import Path
from django.http import StreamingHttpResponse

from asgiref.sync import sync_to_async
from asgiref.sync import sync_to_async, async_to_sync
from .service.turnitin_service import TurnitinService  
from django_q.tasks import async_task

import os
import re
import traceback
import asyncio
import redis

# 配置日志记录器
logger = logging.getLogger(__name__)

redis_client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0, decode_responses=True)


def log_exception(e, request=None, extra_context=None):
    """统一的异常日志记录函数"""
    error_trace = traceback.format_exc()
    error_context = {
        'exception_type': type(e).__name__,
        'exception_message': str(e),
        'stack_trace': error_trace,
    }
    
    if request:
        error_context.update({
            'path': request.path,
            'method': request.method,
            'user': getattr(request, 'user', None),
            'params': dict(request.GET) if request.method == 'GET' else dict(request.POST)
        })
    
    if extra_context:
        error_context.update(extra_context)
    
    logger.error(
        "Exception occurred: %s",
        str(e),
        exc_info=True,
        extra={'error_context': error_context}
    )

def home_view(request, user_id=None):
    try:
        if user_id and user_id.strip():
            web_user = WebUser.objects.get(uid=user_id)
            if not web_user:
                remaining_checks = 0
                language = 'cn'
                jobs = []
            else:
                remaining_checks = web_user.available_cnt
                language = web_user.language
                jobs = []
            logger.info(f"用户 {user_id} 访问首页，剩余次数 {remaining_checks}")
        else:
            remaining_checks = 0
            language = 'zh'
            jobs = []
            logger.warning("匿名用户访问首页")

        context = {
            'title': '我的 Django 首页',
            'user_id': user_id if user_id else 'anonymous',
            'language': language,
            'remaining_checks': remaining_checks,
            'jobs': jobs
        }
        return render(request, 'home/index.html', context)
        
    except Exception as e:
        return render(request, 'home/index.html', {
            'title': '我的 Django 首页',
            'user_id': 'anonymous',
            'language': 'zh',
            'remaining_checks': 0,
            'jobs': []
        }, status=200)


@require_POST
@transaction.atomic
def upload_file(request):
    file = None  # 初始化 file 变量
    try:
        # 1. 请求验证
        if request.method != 'POST':
            raise ValueError("仅允许 POST 请求")

        # 2. 获取并验证用户
        user_id = request.POST.get('user_id')
        if not user_id:
            raise ValueError("缺少 user_id 参数")
            
        web_user = WebUser.objects.get(uid=user_id)
        logger.debug(f"用户 {user_id} 开始文件上传")

        # 3. 检查可用次数
        if web_user.available_cnt <= 0:
            raise PermissionError("无剩余检查次数")

        # 4. 文件验证
        if 'document' not in request.FILES:
            raise ValueError("未上传文件")

        file = request.FILES['document']
        
        # 文件类型验证
        allowed_extensions = {'.doc', '.docx', '.pdf'}
        file_ext = Path(file.name).suffix.lower()
        if file_ext not in allowed_extensions:
            raise ValueError(f"无效文件格式。允许的格式: {allowed_extensions}")

        # 文件大小验证 (15MB限制)
        if file.size > 15 * 1024 * 1024:
            raise ValueError("文件大小超过 15MB")

        # 5. 使用 Redis 锁防止重复提交
        lock_key = f"upload_lock:{user_id}"
        if redis_client.setnx(lock_key, "locked"):
            redis_client.expire(lock_key, 10)  # 10秒后自动释放锁
        else:
            raise ValueError("请勿重复提交相同文件，10秒内请勿重复操作")

        # 6. 文件名处理
        origin_title = file.name
        base_name = Path(origin_title).stem
        
        cleaned_name = re.sub(r'[【】\\\/:*?"<>|]', '', base_name)  # 去特殊字符
        cleaned_name = ''.join(lazy_pinyin(cleaned_name))  # 中文转拼音
        cleaned_name = re.sub(r'\.+', '', cleaned_name)  # 去掉多余的.

        # 7. 构造存储路径
        storage_dir = os.path.join(user_id)
        storage_path = os.path.join(storage_dir, f"{cleaned_name}{file_ext}")
        full_path = os.path.join(settings.MEDIA_ROOT, storage_path)

        # 8. 确保目录存在并可写
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        if not os.access(os.path.dirname(full_path), os.W_OK):
            raise PermissionError(f"目录 {os.path.dirname(full_path)} 无写权限")

        logger.debug(f"MEDIA_ROOT: {settings.MEDIA_ROOT}")
        logger.debug(f"Storage path: {storage_path}")
        logger.debug(f"Full path: {full_path}")

        # 9. 高效文件保存（分块写入）
        try:
            with default_storage.open(storage_path, 'wb') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
                destination.flush()
                logger.debug(f"文件写入完成: {storage_path}")

            # 验证文件是否保存成功
            if not default_storage.exists(full_path):
                raise FileNotFoundError(f"文件未成功保存到 {storage_path}")

            # 10. 创建初始数据库记录
            initial_assignment = WebUserAssignments.objects.create(
                user_id=web_user.uid,
                uid=web_user.uid,
                filename=storage_path,
                title=cleaned_name,
                origin_title=origin_title,
                assignment_id="",
                status=WebUserAssignments.Status.SUBMITTED,
                filepath=storage_path,
                create_datetime=timezone.now(),
                update_datetime=timezone.now()
            )

            # 11. 更新用户次数
            web_user.available_cnt -= 1
            web_user.save()

            # 12. 调度异步任务上传到 Turnitin
            # async_task(
            #     'turnitin_admin.tasks.upload_to_turnitin_task',
            #     task_name=f"turnitin_upload_{initial_assignment.id}",
            #     group=f"turnitin_{web_user.uid}"
            # )
            # logger.info(f"异步任务已调度: user_id={web_user.uid}, assignment_id={initial_assignment.id}")

            # 13. 立即返回响应
            return JsonResponse({
                'message': '文件上传成功，处理中',
                'job_id': initial_assignment.id,
                'filename': storage_path,
                'status': initial_assignment.get_status_display(),
                'timestamp': timezone.now().isoformat()
            })

        except Exception as e:
            # if default_storage.exists(storage_path):
            #     default_storage.delete(storage_path)
            raise RuntimeError('上传失败，请重试')
            

    except Exception as e:
        extra_context = {
            'storage_path': storage_path if 'storage_path' in locals() else None,
            'media_root': settings.MEDIA_ROOT
        }
        if file is not None:
            extra_context.update({
                'file_name': file.name,
                'file_size': file.size
            })
        log_exception(e, request, extra_context)
        return JsonResponse({
            'error': '文件上传失败',
            'details': str(e),
            'status': 'error',
            'timestamp': timezone.now().isoformat()
        }, status=500)
    finally:
        # 确保锁在任何情况下都被释放
        lock_key = f"upload_lock:{user_id}"
        if redis_client.get(lock_key):
            redis_client.delete(lock_key)

@require_GET
def get_web_user_assignments(request):
    return async_to_sync(_get_web_user_assignments)(request)


async def _get_web_user_assignments(request):
    try:
        user_id = request.GET.get('user_id')
        if not user_id:
            raise ValueError("缺少 user_id 参数")

        # Fetch assignments asynchronously
        assignments = await sync_to_async(
            lambda: list(WebUserAssignments.objects.filter(uid=user_id).exclude(
                     status=WebUserAssignments.Status.DELETED))
        )()
        
        web_user = await sync_to_async(lambda: WebUser.objects.get(uid=user_id))()

        # Prepare response data
        jobs_status = [
            {
                'job_id': assignment.id,
                'status': assignment.status,
                'title': assignment.title,
                'upload_time': assignment.create_datetime.isoformat()
            }
            for assignment in assignments
        ]

        logger.info(f"检查用户 {user_id} 的作业状态，作业数量: {len(jobs_status)}")
        return JsonResponse({
            'status': 'success',
            'jobs': jobs_status,
            'user_id': user_id,
            'remaining_checks': web_user.available_cnt,
            'timestamp': timezone.now().isoformat()
        })

    except Exception as e:
        log_exception(e, request)
        return JsonResponse({
            'status': 'error',
            'jobs': [],
            'user_id': user_id,
            'timestamp': timezone.now().isoformat(),
            'details': str(e)
        }, status=500)

@require_POST
def delete_job(request):
    try:
        user_id = request.POST.get('user_id')
        job_id = request.POST.get('job_id')
        
        if not all([user_id, job_id]):
            raise ValueError("缺少必要参数")

        assignment = WebUserAssignments.objects.get(user_id=user_id, id=job_id)
        if assignment.filepath and default_storage.exists(assignment.filepath):
            default_storage.delete(assignment.filepath)
        assignment.mark_delete()
        assignment.save()
        
        logger.info(f"用户 {user_id} 删除作业 {job_id}")
        return JsonResponse({
            'message': '作业删除成功',
            'job_id': job_id,
            'user_id': user_id,
            'timestamp': timezone.now().isoformat(),
            'status': 'success'
        })
        
    except ObjectDoesNotExist as e:
        log_exception(e, request)
        return JsonResponse({
            'error': '资源不存在',
            'details': str(e),
            'status': 'error'
        }, status=404)
        
    except Exception as e:
        log_exception(e, request)
        return JsonResponse({
            'error': '内部服务器错误',
            'details': str(e),
            'status': 'error'
        }, status=500)



@require_GET
def download_file(request):
    try:
        user_id = request.GET.get('user_id')
        job_id = request.GET.get('job_id')
        report_type = request.GET.get('type')  # 'report' 或 'ai'

        if not all([user_id, job_id, report_type]):
            raise ValueError("缺少 user_id、job_id 或 type 参数")

        # 使用主键查找对应记录
        assignment = WebUserAssignments.objects.get(id=job_id)
        if assignment.uid != user_id:
            raise PermissionError("用户无权访问该作业")

        # 根据 report_type 确定文件路径
        base_path = Path(assignment.filepath)
        if report_type == 'report':
            file_path = base_path.with_name(base_path.stem + '_plagiarism.pdf')
        elif report_type == 'ai':
            file_path = base_path.with_name(base_path.stem + '_ai.pdf')
        else:
            raise ValueError("无效的 report_type 参数")

        if not default_storage.exists(file_path):
            raise FileNotFoundError(f"文件 {file_path} 不存在")

        download_filename = f"{assignment.title}_{report_type}_{timezone.now().strftime('%Y%m%d_%H%M%S')}{file_path.suffix}"
        file = default_storage.open(file_path, 'rb')
        response = FileResponse(file, as_attachment=True, filename=download_filename)
        logger.info(f"用户 {user_id} 下载作业 {job_id} 的文件: {download_filename}")
        return response
        
    except ObjectDoesNotExist as e:
        log_exception(e, request)
        return JsonResponse({
            'error': '资源不存在',
            'details': str(e),
            'status': 'error'
        }, status=404)
        
    except PermissionError as e:
        log_exception(e, request)
        return JsonResponse({
            'error': '权限不足',
            'details': str(e),
            'status': 'error'
        }, status=403)
        
    except FileNotFoundError as e:
        log_exception(e, request)
        return JsonResponse({
            'error': '文件不存在',
            'details': str(e) + "\n1. 字数未在330-30000字之间\n2. 语言不是英语\n3. 格式不是word或者pdf\n具体可联系客服帮助解决",
            'status': 'error'
        }, status=404)
        
    except Exception as e:
        log_exception(e, request)
        return JsonResponse({
            'error': '内部服务器错误',
            'details': str(e),
            'status': 'error'
        }, status=500)