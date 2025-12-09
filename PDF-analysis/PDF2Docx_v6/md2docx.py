import re
import os
import json
from docx import Document
from aw_llm import get_image_discription
from bank_ocr import predict
from logs import logger
import base64



# ------------------- 文件自动清理函数 -------------------
def auto_clean_files(
        enable_clean: bool,
        file_paths: list[str]
) -> None:
    """
    自动清理指定文件（支持开关控制，跳过不存在的文件）

    Args:
        enable_clean: 是否启用清理功能（True=清理，False=不清理）
        file_paths: 需要清理的文件路径列表（支持多文件批量删除）
    """
    if not enable_clean:
        return

    for file_path in file_paths:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f'已删除：{file_path}')
            except Exception as e:
                logger.warning(f'无法删除文件 {file_path}，原因：{str(e)}')
        else:
            logger.warning(f'文件不存在，跳过删除：{file_path}')


def process_markdown_file(
        file_path: str,
        abs_dir: str,
        output_docx_path: str,
        md_file_prefix: str,
        enable_clean: bool = False,  # 新增：清理功能开关
        encoding: str = 'utf-8'
) -> None:
    """
    按顺序读取单个Markdown文件，多张图片按原顺序OCR识别，每张/每页生成独立JSON（带MD前缀），
    识别结果按原文档顺序写入同名docx（过滤空行），支持自动清理中间文件
    新增：根据图片命名自动选择OCR模型（含"表格"关键词用PaddleOCRVL，否则用PaddleOCR）

    Args:
        enable_clean: 是否启用清理功能（True=清理图片、JSON、MD，False=保留）
    """
    image_pattern = re.compile(r'!\[.*?\]\((?:["\']?)(.*?)(?:["\']?)\)')
    doc = Document()


    def replace_image_with_ocr(match: re.Match) -> str:

        img_rel_path = match.group(1).strip()
        print(f'图片路径：{img_rel_path}')

        # 获取图片文件名（用于判断是否为表格图片）
        img_filename = os.path.basename(img_rel_path)
        print(f'图片名字：{img_filename}')

        img_abs_path = os.path.join(abs_dir, 'md_data', img_rel_path)
        logger.info(f'原始路径：{img_rel_path} -> 绝对路径：{img_abs_path}')

        if not os.path.exists(img_abs_path):
            logger.warning(f'图片文件不存在：{img_abs_path}，跳过该图片')
            return '【图片开始】OCR识别失败：图片文件不存在【图片结束】'

        try:
            with open(img_abs_path, 'rb') as f:
                img_base64 = base64.b64encode(f.read()).decode('utf-8')
            ocr_results = predict(img_filename, img_base64)

        except Exception as e:
            logger.error(f'图片OCR识别失败：{img_abs_path}，原因：{str(e)}')
            return f'【图片开始】识别失败：识别过程出错【图片结束】'

        json_save_dir = os.path.join(abs_dir, 'json_data')
        os.makedirs(json_save_dir, exist_ok=True)
        img_basename = os.path.splitext(os.path.basename(img_abs_path))[0]
        all_page_texts = []

        # 获取当前json文件名和json存储的绝对路径
        json_filename = f'{md_file_prefix}_img_{img_basename}.json'
        json_abs_path = os.path.join(json_save_dir, json_filename)

        # 保存json文件
        with open(json_abs_path, 'w', encoding='utf-8') as f:
            json.dump(ocr_results, f, ensure_ascii=False, indent=4)
        logger.info(f'已保存JSON文件：{json_abs_path}')

        # ------------------ 获取json中的文本内容 -------------------
        with open(json_abs_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)

        json_data = json_data['body']['data'][0]['generalTextList']
        for item in json_data:
            all_page_texts.append(item['value'])
        print(all_page_texts)
        logger.info(f'成功获取当前图片json中的文本内容：{all_page_texts}')

        # ------------------ 对文本内容进行拼接 -------------------
        total_img_text = ','.join(all_page_texts)

        # ------------------- 调用大模型生成描述 -------------------
        total_img_text = get_image_discription(total_img_text)

        # ------------------- 清理当前图片的JSON和原图 -------------------
        json_files_to_clean = [
            os.path.join(json_save_dir,
                         f'{md_file_prefix}_img_{img_basename}.json')
            for page_idx in range(1, len(ocr_results) + 1)]
        files_to_clean = json_files_to_clean + [img_abs_path]
        auto_clean_files(enable_clean=enable_clean, file_paths=files_to_clean)

        # ------------------- 返回图片描述结果 -------------------
        return f'【图片开始】{total_img_text}【图片结束】'

    try:
        with open(file_path, 'r', encoding=encoding) as md_file:
            lines = md_file.readlines()

        for line in lines:
            processed_line = image_pattern.sub(replace_image_with_ocr, line)
            allowed_chars = r'[^\u4e00-\u9fa5a-zA-Z0-9。，.！？；：""''（）【】《》、·…—-]'
            cleaned_line = re.sub(allowed_chars, '', processed_line.rstrip('\n'))
            if cleaned_line.strip():
                doc.add_paragraph(cleaned_line)

        doc.save(output_docx_path)
        logger.info(f'\n[文件处理完成] 结果已保存到：{output_docx_path}')

        # ------------------- 清理原MD文件 -------------------
        auto_clean_files(enable_clean=enable_clean, file_paths=[file_path])

    except FileNotFoundError:
        logger.error(f'[错误] 找不到Markdown文件：{file_path}，请检查路径')
    except UnicodeDecodeError:
        logger.error(f'文件编码不匹配（当前使用{encoding}），中文乱码可尝试 encoding="gbk"')
    except Exception as e:
        logger.error(f'处理文件 {os.path.basename(file_path)} 时异常：{str(e)}')
        doc.save(output_docx_path)
        logger.error(f'[紧急保存] 已保存部分处理结果到：{output_docx_path}')


# ------------------- 批量处理入口 -------------------
if __name__ == "__main__":
    abs_dir = os.path.dirname(os.path.abspath(__file__))
    MD_FOLDER = os.path.join(abs_dir, "md_data")
    OUTPUT_DOCX_FOLDER = os.path.join(abs_dir, "docx_result")
    JSON_SAVE_DIR = os.path.join(abs_dir, "json_data")

    os.makedirs(OUTPUT_DOCX_FOLDER, exist_ok=True)
    os.makedirs(JSON_SAVE_DIR, exist_ok=True)


    # ------------------- 清理中间文件功能开关（核心控制） -------------------
    ENABLE_CLEAN = True  # True=启用清理，False=保留所有文件

    md_files = [f for f in os.listdir(MD_FOLDER) if f.endswith('.md')]
    if not md_files:
        print(f'[警告] {MD_FOLDER} 文件夹下未找到任何.md文件，请检查目录！')
        logger.warning(f'未找到MD文件：{MD_FOLDER}')
        exit(1)

    print(f'[批量处理开始] 共发现 {len(md_files)} 个MD文件，清理功能：{"启用" if ENABLE_CLEAN else "禁用"}\n')
    logger.info(f'批量处理开始，共{len(md_files)}个MD文件，清理功能：{"启用" if ENABLE_CLEAN else "禁用"}')

    for idx, md_filename in enumerate(md_files, start=1):
        md_file_path = os.path.join(MD_FOLDER, md_filename)
        md_file_prefix = os.path.splitext(md_filename)[0]
        output_docx_path = os.path.join(OUTPUT_DOCX_FOLDER, f'{md_file_prefix}.docx')

        print(f'{"=" * 60}')
        print(f'[正在处理 {idx}/{len(md_files)}] 文件名：{md_filename}')
        print(f'[输出路径] DOCX：{output_docx_path}')
        print(f'{"=" * 60}')
        logger.info(f'正在处理第{idx}/{len(md_files)}个文件：{md_filename}，输出路径：{output_docx_path}')

        # 传递清理开关参数
        process_markdown_file(
            file_path=md_file_path,
            abs_dir=abs_dir,
            output_docx_path=output_docx_path,
            md_file_prefix=md_file_prefix,
            enable_clean=ENABLE_CLEAN,  # 启用/禁用清理
            encoding='utf-8'
        )

    print(f'\n{"=" * 60}')
    print(f'[批量处理结束] 所有文件处理完成！')
    print(f'[结果汇总]')
    print(f' - MD文件目录：{MD_FOLDER}')
    print(f' - DOCX输出目录：{OUTPUT_DOCX_FOLDER}')
    print(f' - JSON输出目录：{JSON_SAVE_DIR}')
    print(f' - 清理功能状态：{"已启用（中间文件已删除）" if ENABLE_CLEAN else "已禁用（所有文件保留）"}')
    print(f' - 模型选择规则：含"表格"关键词图片使用PaddleOCRVL，普通图片使用PaddleOCR')
    print(f'{"=" * 60}')
    logger.info('批量处理结束，所有文件已处理完成')