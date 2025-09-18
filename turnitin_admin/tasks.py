from django.utils import timezone
from api.models import WebUser, WebUserAssignments
from .service.turnitin_service import TurnitinService
from django.db import transaction
from asgiref.sync import async_to_sync
from django.core.files.storage import default_storage
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import timedelta
from django.conf import settings
from sqlalchemy import or_
from django.db.models import Q

import os
import logging
import redis
import threading

logger = logging.getLogger(__name__)

# 全局共享线程池
MAX_WORKERS = 1  # 可根据服务器性能调整
executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

# Redis 客户端配置（需在 settings.py 中定义 REDIS_HOST 和 REDIS_PORT）
redis_client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0, decode_responses=True)
# 内存锁作为后备
memory_lock = threading.Lock()

def acquire_lock(assignment_id):
    """尝试获取锁，返回是否成功"""
    lock_key = f"lock:assignment:{assignment_id}"
    # 尝试使用 Redis 锁（5秒超时）
    if redis_client.set(lock_key, "locked", nx=True, ex=1800):
        return True
    # Redis 锁失败，尝试内存锁
    with memory_lock:
        if not redis_client.get(lock_key):
            if redis_client.set(lock_key, "locked", nx=True, ex=1800):
                return True
    return False

def release_lock(assignment_id):
    """释放锁"""
    lock_key = f"lock:assignment:{assignment_id}"
    redis_client.delete(lock_key)

def download_reports():
    """Download AI and plagiarism reports for all assignments."""
    if True: #with transaction.atomic():
        assignments = WebUserAssignments.objects.filter(status=WebUserAssignments.Status.ANALYSING)
        for assignment in assignments:
            with transaction.atomic():
                if WebUserAssignments.objects.filter(id=assignment.id) == WebUserAssignments.Status.FAILED:continue
            try:
                assignment_id = assignment.assignment_id
                if not acquire_lock(assignment_id):
                    logger.info(f"作业 {assignment_id} 已被其他进程锁定，跳过")
                    continue

                user_id = assignment.uid
                title = assignment.title
                storage_dir = os.path.dirname(assignment.filepath) if assignment.filepath else settings.MEDIA_ROOT

                # 移除 UTC 转换
                current_time = timezone.now()
                create_time = assignment.create_datetime

                time_diff = (current_time - create_time).total_seconds() / 60  # 分钟差
                is_saved = False
            

                with transaction.atomic():
                    if time_diff <= 10:
                        # 在10分钟以内，尝试下载 AI 报告
                        logger.info(f"作业 {assignment_id} 在10分钟内，尝试下载AI报告")
                        turnitin_service = TurnitinService()
                        async_to_sync(turnitin_service.initialize)()
                        ai_content = turnitin_service.download_ai_file(
                            assignment_id,
                            assignment.filename.split("/")[-1]
                        )

                        if not ai_content:
                            logger.info(f"作业 {assignment_id} AI报告下载失败或不存在，保持 ANALYSING 状态")
                            release_lock(assignment_id)
                            continue  # 10分钟内 AI 失败，不更改状态，等待下次任务

                        # AI 下载成功，尝试下载重复率报告
                        plagiarism_content = turnitin_service.download_plagiarism_file(assignment_id, user_id)

                        ai_file_path = os.path.join(storage_dir, f"{title}_ai.pdf")
                        plagiarism_file_path = os.path.join(storage_dir, f"{title}_plagiarism.pdf")
                        full_ai_path = os.path.join(settings.MEDIA_ROOT, ai_file_path)
                        full_plagiarism_path = os.path.join(settings.MEDIA_ROOT, plagiarism_file_path)

                        # 保存 AI 报告
                        if ai_content:
                            with default_storage.open(ai_file_path, 'wb') as destination:
                                os.makedirs(os.path.dirname(full_ai_path), exist_ok=True)
                                destination.write(ai_content)
                                destination.flush()
                            logger.info(f"作业 {assignment_id} AI 报告已保存至 {ai_file_path}")

                        # 保存重复率报告
                        if plagiarism_content:
                            with default_storage.open(plagiarism_file_path, 'wb') as destination:
                                os.makedirs(os.path.dirname(full_plagiarism_path), exist_ok=True)
                                destination.write(plagiarism_content)
                                destination.flush()
                            logger.info(f"作业 {assignment_id} 重复率报告已保存至 {plagiarism_file_path}")
                        else:
                            continue

                        # AI 和重复率报告都成功，更新状态
                        assignment.mark_downloaded()
                        assignment.save()
                        is_saved = True
                        logger.info(f"作业 {assignment_id} AI和重复率报告下载完成，状态更新为 DOWNLOADED")

                    else:
                        # 超过10分钟，跳过 AI 报告，直接下载重复率报告
                        logger.info(f"作业 {assignment_id} 超过10分钟，跳过AI下载，直接尝试下载重复率报告")
                        turnitin_service = TurnitinService()
                        async_to_sync(turnitin_service.initialize)()
                        plagiarism_content = turnitin_service.download_plagiarism_file(assignment_id, user_id)

                        if plagiarism_content:
                            plagiarism_file_path = os.path.join(storage_dir, f"{title}_plagiarism.pdf")
                            full_plagiarism_path = os.path.join(settings.MEDIA_ROOT, plagiarism_file_path)
                            with default_storage.open(plagiarism_file_path, 'wb') as destination:
                                os.makedirs(os.path.dirname(full_plagiarism_path), exist_ok=True)
                                destination.write(plagiarism_content)
                                destination.flush()
                            logger.info(f"作业 {assignment_id} 重复率报告已保存至 {plagiarism_file_path}")
                            assignment.mark_downloaded()
                            assignment.save()
                            is_saved = True
                        else:
                            logger.error(f"作业 {assignment_id} 重复率报告下载失败")
                            raise RuntimeError('超过10分钟 没有重复率和AI')

            except Exception as e:
                error_context = {
                    'assignment_id': assignment_id,
                    'user_id': user_id,
                    'storage_dir': storage_dir,
                    'exception_type': type(e).__name__,
                    'exception_message': str(e)
                }
                logger.error(
                    f"后台下载任务失败: assignment_id={assignment_id}, user_id={user_id}, 错误: {str(e)}",
                    exc_info=True,
                    extra={'error_context': error_context}
                )
            finally:
                release_lock(assignment_id)

def _upload_to_turnitin_task():
    """异步任务：将文件上传到 Turnitin 并更新数据库"""
    if True:#with transaction.atomic():
        assignments = WebUserAssignments.objects.filter(status=WebUserAssignments.Status.SUBMITTED)
        for assignment in assignments:
            with transaction.atomic():
                if WebUserAssignments.objects.filter(id=assignment.id) == WebUserAssignments.Status.FAILED:continue
            try:
                assignment_id = assignment.id  # 使用数据库主键 id 作为锁键
                if not acquire_lock(assignment_id):
                    logger.info(f"作业 {assignment_id} 已被其他进程锁定，跳过")
                    continue

                user_id = assignment.uid
                cleaned_name = assignment.title
                storage_path = assignment.filepath if assignment.filepath else ""

                full_storage_path = os.path.join(settings.MEDIA_ROOT, storage_path) if storage_path else ""
                logger.debug(f"Full storage path: {full_storage_path}")

                # 移除 UTC 转换
                current_time = timezone.now()
                create_time = assignment.create_datetime
                
                if current_time - create_time > timedelta(minutes=10):
                    release_lock(assignment_id)
                    raise RuntimeError('timeout')
                
                if not storage_path or not default_storage.exists(full_storage_path):
                    logger.error(f"作业 {assignment_id} 文件路径无效或文件不存在: {full_storage_path}")
                    release_lock(assignment_id)
                    raise RuntimeError(f"作业 {assignment_id} 文件路径无效或文件不存在: {full_storage_path}")

                    

                is_saved = False
                
                turnitin_service = TurnitinService()
                async_to_sync(turnitin_service.initialize)()

                with default_storage.open(storage_path, 'rb') as source_file:
                    userfile_content = b''.join(source_file.chunks())

                result = turnitin_service.submit(
                    assignment_ids=[],
                    title=cleaned_name,
                    filename=storage_path,
                    userfile=userfile_content,
                    open_id=user_id,
                    assign_id_in_db=assignment.id,
                    last_assignment_id = '' if assignment.review == None else assignment.review
                )

                if 'assignment_id' in result.get('metadata', {}):
                    with transaction.atomic():
                        # 更新现有记录，而不是创建新记录
                        assignment = WebUserAssignments.objects.get(id=assignment.id)
                        assignment.assignment_id = result['metadata']['assignment_id']
                        assignment.mark_analysising()
                        assignment.save()
                        is_saved = True
                        logger.info(f"异步上传成功: user_id={user_id}, assignment_id={assignment.id}, turnitin_assignment_id={result['metadata']['assignment_id']}")

            except Exception as e:
                logger.error(
                    f"异步上传失败: assignment_id={assignment_id}, user_id={user_id}, 错误: {str(e)}",
                    exc_info=True
                )
                if 'current_time' in locals() and 'create_time' in locals():
                    with transaction.atomic():
                        assignment.review = str(e) if assignment.review  is None else assignment.review + ';' + str(e)
                        assignment.save()
            finally:
                release_lock(assignment_id)

def scan_reports():
    """定时任务，提交下载任务"""
    logger.info(f"开始执行 scan_reports 任务，时间: {timezone.now()}")
    download_reports()
    logger.info(f"scan_reports 任务完成，时间: {timezone.now()}")

def upload_to_turnitin_task():
    """定时任务，提交上传任务"""
    logger.info(f"开始执行 upload_to_turnitin_task 任务，时间: {timezone.now()}")
    _upload_to_turnitin_task()
    logger.info(f"upload_to_turnitin_task 任务完成，时间: {timezone.now()}")
    
def failed_task():
    with transaction.atomic():
        assignments = WebUserAssignments.objects.filter(
            Q(status=WebUserAssignments.Status.SUBMITTED.value) |
            Q(status=WebUserAssignments.Status.ANALYSING.value)
        ).select_for_update()
    
        for assignment in assignments:
            assignment_id = assignment.id  # 使用数据库主键 id 作为锁键
            if not acquire_lock(str(assignment_id) + '_to_failed'):
                logger.info(f"作业 {assignment_id} 已被其他进程锁定，跳过")
                continue

            user_id = assignment.uid

            # 移除 UTC 转换
            current_time = timezone.now()
            create_time = assignment.create_datetime
            
            if current_time - create_time > timedelta(minutes=15):
                logger.error(f"作业 {assignment_id} 上传超时，上传时间：{assignment.update_datetime}")
                assignment.mark_failed()
                assignment.save()
                web_user = WebUser.objects.get(uid=user_id)
                web_user.available_cnt += 1
                web_user.save()
            release_lock(str(assignment_id) + '_to_failed')