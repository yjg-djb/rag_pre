# config.py
import os
from pathlib import Path

from pywin_word import batch_doc_to_docx

# 基础目录配置（集中管理目录名称）
CONFIG = {
    "input": "input_docs",       # 原始文档目录
    "output": "output_flattened", # 输出文档目录
    "images": "images",           # 过程材料：图片
    "ocr": "ocr_results",         # 过程材料：OCR结果
    "log_file": "log_file",       # 日志文件目录
    "log": "batch_processing_errors.log"  # 错误日志文件名
}

# 大模型配置
LLM_CONFIG = {
    "api_url": os.getenv('LLM_API_URL'),
    "headers": {"Authorization": os.getenv('LLM_API_KEY')},
    "timeout": 10  # 超时时间（秒）
}

# 自动生成所有目录的绝对路径（基于脚本所在目录的上级目录）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # 当前脚本（config.py）所在目录
INPUT_DIR = os.path.abspath(os.path.join(BASE_DIR, f"../{CONFIG['input']}"))
OUTPUT_DIR = os.path.abspath(os.path.join(BASE_DIR, f"../{CONFIG['output']}"))
IMAGE_DIR = os.path.abspath(os.path.join(BASE_DIR, f"../{CONFIG['images']}"))
OCR_DIR = os.path.abspath(os.path.join(BASE_DIR, f"../{CONFIG['ocr']}"))
LOG_DIR = os.path.abspath(os.path.join(BASE_DIR, f"../{CONFIG['log_file']}"))
ERROR_LOG = os.path.abspath(os.path.join(LOG_DIR, CONFIG['log']))
print(f"脚本目录: {BASE_DIR}")
print(f"输入目录: {INPUT_DIR}")
print(f"输出目录: {OUTPUT_DIR}")
print(f"图片目录: {IMAGE_DIR}")
print(f"OCR结果目录: {OCR_DIR}")
print(f"日志目录: {LOG_DIR}")
print(f"日志文件: {ERROR_LOG}")
for dir_path in [INPUT_DIR, OUTPUT_DIR, IMAGE_DIR, OCR_DIR, LOG_DIR]:
    Path(dir_path).mkdir(parents=True, exist_ok=True)

batch_doc_to_docx(INPUT_DIR,INPUT_DIR)