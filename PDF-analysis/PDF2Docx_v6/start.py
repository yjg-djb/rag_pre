import os
from pdf2md import batch_pdf_to_md
from logs import logger
import time
import atexit

def start():
    # 获取当前脚本所在路径
    abs_path = os.path.dirname(__file__)
    logger.info(f"当前脚本所在路径：{abs_path}")

    # 批量处理配置（修改这里的路径即可）
    BATCH_CONFIG = {
        "abs_dir": abs_path,
        "pdf_dir": os.path.join(abs_path, "pdf_data"),  # 所有PDF文件所在的目录
        "md_dir": os.path.join(abs_path, "md_data"),  # MD文件输出目录
        "json_dir": os.path.join(abs_path, "json_data"),
        "docx_dir": os.path.join(abs_path, "docx_result"),
        "img_dir": "images",  # 图片输出目录（相对于md_dir）
        "enable_clean":True  # True=启用清理，False=保留所有文件
    }

    # 执行批量处理
    batch_pdf_to_md(
        abs_dir=BATCH_CONFIG["abs_dir"],
        pdf_dir=BATCH_CONFIG["pdf_dir"],
        md_dir=BATCH_CONFIG["md_dir"],
        json_dir=BATCH_CONFIG["json_dir"],
        docx_dir=BATCH_CONFIG["docx_dir"],
        img_dir=BATCH_CONFIG["img_dir"],
        enable_clean=BATCH_CONFIG["enable_clean"]
    )

if __name__ == '__main__':
    # 记录程序开始时间
    start_time = time.time()

    start()

    # 记录程序结束时间
    end_time = time.time()

    # 记录到日志
    logger.info(f'程序运行花费时间为{end_time - start_time}秒')
