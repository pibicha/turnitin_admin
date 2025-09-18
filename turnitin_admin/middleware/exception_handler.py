# turnitin_admin/middleware/exception_handler.py
import logging
import traceback
from django.http import JsonResponse

logger = logging.getLogger(__name__)

class GlobalExceptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        logger.critical("===== 中间件初始化成功 =====")

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        # 获取完整错误堆栈
        error_trace = traceback.format_exc()
        
        # 强制打印到控制台（测试用）
        print("\n" + "="*50)
        print(f"异常类型: {type(exception)}")
        print(f"异常信息: {str(exception)}")
        print(f"堆栈跟踪:\n{error_trace}")
        print("="*50 + "\n")

        # 记录到日志文件
        logger.error(
            "路径: %s | 方法: %s | 异常: %s\n堆栈:\n%s",
            request.path,
            request.method,
            str(exception),
            error_trace
        )

        return JsonResponse(
            {"error": "Internal Server Error", "details": str(exception)},
            status=500
        )