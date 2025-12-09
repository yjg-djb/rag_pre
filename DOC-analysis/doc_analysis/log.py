# logger.py
import logging
from datetime import datetime
from pathlib import Path
from config import LOG_DIR, ERROR_LOG  # 从配置文件导入路径

def init_logger():
    """初始化日志系统（文件+控制台输出）"""
    # 确保日志目录存在
    Path(LOG_DIR).mkdir(parents=True, exist_ok=True)

    # 备份旧日志
    if Path(ERROR_LOG).exists():
        backup_log = ERROR_LOG.replace(".log", f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        Path(ERROR_LOG).rename(backup_log)  # 替代shutil.move，更轻量

    # 配置日志格式
    log_format = "[%(asctime)s] [%(levelname)s] %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(log_format, datefmt=date_format)

    # 文件处理器
    file_handler = logging.FileHandler(ERROR_LOG, encoding="utf-8")
    file_handler.setFormatter(formatter)

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # 全局logger配置
    logger = logging.getLogger("docx_processor")
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.propagate = False  # 避免重复输出

    return logger

# 初始化全局logger（其他脚本直接导入使用）
logger = init_logger()