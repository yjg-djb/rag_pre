import logging
from logging.handlers import RotatingFileHandler
import os

def init_logger():
    # 1. 创建日志器（root logger 或自定义 logger）
    logger = logging.getLogger("data_process_ocr")
    logger.setLevel(logging.DEBUG)  # 全局日志级别（低于此级别的日志不输出）
    logger.propagate = False  # 避免重复输出到控制台

    # 2. 定义日志格式（时间戳-级别-模块-信息-堆栈）
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"  # 时间格式
    )

    # 3. 配置文件处理器（按大小滚动：单个文件100MB，最多保留5个备份）
    log_abs_dir = os.path.dirname(__file__) # 日志目录
    log_dir = os.path.join(log_abs_dir, "logs")

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    file_handler = RotatingFileHandler(
        filename=os.path.join(log_dir, "data_process_ocr.log"),
        maxBytes=100 * 1024 * 1024,  # 100MB
        backupCount=5,  # 最多保留5个日志文件（app.log.1 ~ app.log.5）
        encoding="utf-8"  # 避免中文乱码
    )
    file_handler.setLevel(logging.INFO)  # 文件输出级别（仅输出INFO及以上）
    file_handler.setFormatter(formatter)

    # 4. （可选）配置控制台处理器（开发环境用）
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)  # 控制台输出DEBUG及以上
    console_handler.setFormatter(formatter)

    # 5. 给日志器添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

# 初始化日志器（程序启动时执行一次）
logger = init_logger()