import logging
import sys
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler


def setup_logger(name: str = "kb-jx", log_dir: str = "logs") -> logging.Logger:
    """
    配置日志系统
    
    Args:
        name: 日志记录器名称
        log_dir: 日志文件目录
    
    Returns:
        配置好的 Logger 对象
    """
    # 创建日志目录
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # 创建 Logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # 避免重复添加 handler
    if logger.handlers:
        return logger
    
    # ========== 格式化器 ==========
    # 详细格式（文件）
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(funcName)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 简洁格式（控制台）
    console_formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # ========== 控制台 Handler ==========
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # ========== 文件 Handler - 所有日志 ==========
    all_log_file = log_path / f"app_{datetime.now().strftime('%Y%m%d')}.log"
    all_file_handler = RotatingFileHandler(
        all_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    all_file_handler.setLevel(logging.DEBUG)
    all_file_handler.setFormatter(detailed_formatter)
    logger.addHandler(all_file_handler)
    
    # ========== 文件 Handler - 错误日志 ==========
    error_log_file = log_path / f"error_{datetime.now().strftime('%Y%m%d')}.log"
    error_file_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(detailed_formatter)
    logger.addHandler(error_file_handler)
    
    return logger


# 创建全局 logger 实例
logger = setup_logger()


from typing import Optional


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    获取 Logger 实例
    
    Args:
        name: 子模块名称
    
    Returns:
        Logger 对象
    """
    if name:
        return logging.getLogger(f"kb-jx.{name}")
    return logger
