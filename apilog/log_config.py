"""日志配置：控制台 + 轮转文件。"""
import logging
import os
from logging.handlers import RotatingFileHandler

from security.setting import settings


def ensure_log_directory() -> None:
    os.makedirs(os.path.dirname(settings.log_file) or ".", exist_ok=True)


def setup_logging() -> logging.Logger:
    """配置并返回全局 api_logger。"""
    ensure_log_directory()

    logger = logging.getLogger("api_logger")
    logger.setLevel(logging.INFO)
    # 防止重复添加 handler (uvicorn reload 时会触发)
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        settings.log_file,
        maxBytes=settings.log_max_bytes,
        backupCount=settings.log_backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.propagate = False
    return logger


class SensitiveKeys:
    """需要脱敏的敏感字段（统一小写匹配）。"""

    KEYS = {
        "password",
        "passwd",
        "pwd",
        "token",
        "access_token",
        "refresh_token",
        "secret",
        "api_key",
        "apikey",
        "credit_card",
        "ssn",
        "authorization",
    }


class LoggedPaths:
    """需要详细记录请求/响应体的路径列表。"""

    PATHS = [
        "/api/login",
        "/api/protected-data",
        "/users/me/",
        "/token",
    ]
