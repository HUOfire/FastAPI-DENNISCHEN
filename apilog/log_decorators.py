import functools
import logging
from typing import Any, Callable

logger = logging.getLogger("uvicorn")


def log_decorator(save_response: bool = False):
    """日志记录装饰器"""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            func_name = func.__name__

            try:
                logger.info(f"函数 {func_name} 开始执行")

                result = await func(*args, **kwargs)

                if save_response:
                    logger.info(f"函数 {func_name} 执行完成，响应数据: {result}")
                else:
                    logger.info(f"函数 {func_name} 执行完成")

                return result

            except Exception as e:
                logger.error(f"函数 {func_name} 执行异常: {str(e)}")
                raise

        return wrapper

    return decorator


def record_log(params: Any, msg: str = ""):
    """记录日志方法"""
    logger.error(f"参数: {params}, 错误信息: {msg}")
