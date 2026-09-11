import logging
import os
from logging.handlers import RotatingFileHandler


log_dir = "./apilog"


def ensure_log_directory():
    """确保日志目录存在"""
    os.makedirs(log_dir, exist_ok=True)

def setup_logging():
    """配置日志系统"""
    # 创建记录器
    logger = logging.getLogger("api_logger")
    logger.setLevel(logging.INFO)

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # 文件处理器 - 按天轮转，保留7天
    file_handler = RotatingFileHandler(
        f"{log_dir}/app.log",
        maxBytes=1024 * 1024 * 5,  # 5MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)

    # 设置格式
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # 添加处理器
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


class Sensitive_Keys:
    """
    数据脱敏的基础数据
    """
    SENSITIVE_KEYS = {
        "password",
        "passwd",
        "pwd",
        "token",
        "access_token",
        "secret",
        "api_key",
        "credit_card",
        "ssn"
    }


class Logged_Paths:
    """
    定义需要记录详细日志的路径列表
    """
    LOGGED_PATHS = ["/api/login",
                    "/users/me/",
                    "/api/protected-data"
                    ]
