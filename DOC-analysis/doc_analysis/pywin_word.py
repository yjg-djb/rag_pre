import os
import win32com.client
import logging
from pathlib import Path
import subprocess
import sys

# 配置日志（控制台+文件输出）
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler("word_convert.log", encoding="utf-8")]
)


def clean_word_processes():
    """清理残留Word进程"""
    try:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/f", "/im", "WINWORD.EXE"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10
            )
        logging.info("已清理残留Word进程")
    except Exception as e:
        logging.warning(f"清理进程失败：{e}")


def batch_doc_to_docx(input_dir, output_dir=None, max_retries=2):
    """批量转换doc→docx（保留格式，简化版）"""
    word = None
    try:
        # 初始化Word（静默模式）
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0
        word.AutomationSecurity = 3

        # 路径处理
        input_path = Path(input_dir)
        if not input_path.is_dir():
            logging.error(f"输入目录无效：{input_dir}")
            return
        output_dir = output_dir or str(input_path)
        output_path = Path(output_dir).mkdir(parents=True, exist_ok=True)  # 确保输出目录存在
        output_path = Path(output_dir)

        # 递归收集所有.doc文件（排除隐藏文件、快捷方式）
        doc_files = [
            str(p) for p in input_path.rglob("*.doc")
            if p.is_file() and not p.name.startswith(".") and not p.name.endswith(".lnk")
        ]

        if not doc_files:
            logging.warning("未找到可转换的.doc文件")
            return
        logging.info(f"发现 {len(doc_files)} 个待转换文件")

        # 批量转换+重试机制
        success = 0
        for doc_path in doc_files:
            doc_obj = Path(doc_path)
            docx_path = output_path / doc_obj.with_suffix(".docx").name

            if docx_path.exists():
                logging.info(f"跳过：{doc_obj.name}（目标已存在）")
                success += 1
                continue

            retry = 0
            converted = False
            while retry <= max_retries and not converted:
                try:
                    doc = word.Documents.Open(doc_path, Encoding=1252, ConfirmConversions=False)
                    doc.SaveAs(str(docx_path), FileFormat=12)  # 12对应docx格式
                    doc.Close(SaveChanges=0)
                    logging.info(f"转换成功：{doc_obj.name}")
                    success += 1
                    converted = True
                except Exception as e:
                    if retry < max_retries:
                        retry += 1
                        logging.warning(f"重试{retry}/{max_retries}：{doc_obj.name} 错误：{e}")
                        if 'doc' in locals():
                            doc.Close(SaveChanges=0)
                    else:
                        logging.error(f"转换失败：{doc_obj.name} 错误：{e}")

        # 转换统计
        total = len(doc_files)
        logging.info(f"\n完成：总{total} | 成功{success} | 失败{total - success} | 输出：{output_dir}")

    except Exception as e:
        logging.error(f"程序异常：{e}")
    finally:
        if word:
            word.Quit(SaveChanges=0)
        clean_word_processes()


if __name__ == "__main__":
    INPUT_FOLDER = r"D:\code\project\result\input_docs"
    OUTPUT_FOLDER = r"D:\code\project\soffice\output"
    batch_doc_to_docx(INPUT_FOLDER, OUTPUT_FOLDER)