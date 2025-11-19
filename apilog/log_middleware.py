import logging
import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class LoggerRecord:
    """日志记录器管理类"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("uvicorn")


    def start(self):
        """启动日志记录器"""
        self.logger.info("日志系统初始化完成")

    def stop(self):
        """停止日志记录器"""
        self.logger.info("日志系统关闭")


class LogMiddleware(BaseHTTPMiddleware):
    """日志中间件"""

    def __init__(self, app):
        super().__init__(app)
        # 在初始化时设置 logger 属性
        self.logger = logging.getLogger("uvicorn")

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        try:
            # 记录请求信息
            self.logger.info(f"请求开始: {request.method} {request.url}")

            response = await call_next(request)

            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)

            # 记录响应信息
            self.logger.info(
                f"请求完成: {request.method} {request.url} "
                f"状态码: {response.status_code} 耗时: {process_time:.2f}s"
            )

            return response
        except Exception as e:
            self.logger.error(f"中间件处理异常: {str(e)}")
            raise


def log_record(request: Request, call_next):
    """日志记录中间件函数"""
    middleware = LogMiddleware(app = None)
    return middleware.dispatch(request, call_next)


