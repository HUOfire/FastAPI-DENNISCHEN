import logging
import os
from logging.handlers import RotatingFileHandler

class LogConfig:
    """日志配置类"""

    def __init__(self):
        self.log_dir = "./logs"
        self.ensure_log_directory()

    def ensure_log_directory(self):
        """确保日志目录存在"""
        os.makedirs(self.log_dir, exist_ok=True)

    def setup_logging(self):
        """配置日志系统"""

        # 基础配置
        logging.basicConfig(
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            level=logging.INFO,
            handlers=[logging.StreamHandler()]
        )

        # 创建记录器
        logger = logging.getLogger("uvicorn")
        logger.setLevel(logging.INFO)

        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # 文件处理器 - 按天轮转，保留7天
        file_handler = RotatingFileHandler(
            f"{self.log_dir}/app.log",
            maxBytes=1024 * 1024 * 5,  # 5MB
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setLevel(logging.INFO)

        # 设置格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        # 添加处理器
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

        return logger



