import fitz  # PyMuPDF的别名
import os
import re
import camelot
import pandas as pd
from md2docx import process_markdown_file
from pathlib import Path
from logs import logger
import shutil
import tempfile
import atexit
import time
from typing import Optional


# ----------------原有功能----------------------
def clean_filename(filename):
    """清理文件名中的非法字符，确保文件名合法"""
    illegal_chars = r'[<>:"/\\|?*]'
    cleaned = re.sub(illegal_chars, '_', filename)
    cleaned = cleaned.strip().strip('.')
    return cleaned if cleaned else "untitled"


def format_img_pages(img_pages):
    """格式化图片所在页码（仅去重、排序，不合并连续页码，完整显示所有页码）"""
    if not img_pages:
        return "无图片"

    # 去重 → 排序 → 转为字符串列表 → 用连字符连接
    sorted_unique_pages = sorted(list(img_pages))
    return "-".join(map(str, sorted_unique_pages)) + "页"


def format_page_nums(page_set):
    """格式化页码集合为“X页_Y页”的格式（去重、排序），用于文件名生成"""
    if not page_set:
        return ""
    sorted_nums = sorted(list(page_set))
    return "_".join([f"{num}页" for num in sorted_nums])


# 新增：表格文本清理函数（来自用户提供的代码）
def clean_table_text(text):
    """清理表格文本（去除换行符、多余空格、统一特殊符号）"""
    if pd.isna(text) or text == '' or str(text).lower() == 'nan':
        return "无"
    # 转换为字符串并处理
    clean_str = str(text)
    # 去除换行符、制表符
    clean_str = re.sub(r'[\n\t]', '', clean_str)
    # 去除多余空格（连续空格合并为一个）
    clean_str = re.sub(r'\s+', ' ', clean_str).strip()
    # 中文句号「．」转英文句号「.」，避免格式混乱
    clean_str = clean_str.replace('．', '.')
    return clean_str


# 新增：处理单个表格，转换为文本描述
def process_table_to_text(table):
    """将camelot提取的表格转换为自然语言文本描述"""
    try:
        df = table.df  # 获取当前表格的DataFrame
        table_texts = []

        # 处理两种常见表格结构：
        # 1. 列名是数字索引（说明第一行是实际特征名）
        # 2. 列名已经是特征名（直接使用）
        if all(isinstance(col, (int, float)) for col in df.columns):
            # 情况1：第一行作为特征名，样本从第二行开始
            features = df.iloc[0].apply(clean_table_text).tolist()  # 清理特征名
            # 修正：DataFrame切片需先转values再tolist()
            samples = df.iloc[1:].values.tolist()
            # 处理空特征名（替换为"特征X"，确保不重复）
            feat_counter = 1
            cleaned_features = []
            for feat in features:
                if feat != "无" and feat not in cleaned_features:
                    cleaned_features.append(feat)
                else:
                    while f"特征{feat_counter}" in cleaned_features:
                        feat_counter += 1
                    cleaned_features.append(f"特征{feat_counter}")
                    feat_counter += 1
            features = cleaned_features
        else:
            # 情况2：直接使用columns作为特征名
            features = [clean_table_text(col) for col in df.columns]  # 清理特征名
            samples = df.values.tolist()  # 正确用法：DataFrame.values.tolist()
            # 处理空特征名（替换为"特征X"，确保不重复）
            feat_counter = 1
            cleaned_features = []
            for feat in features:
                if feat != "无" and feat not in cleaned_features:
                    cleaned_features.append(feat)
                else:
                    while f"特征{feat_counter}" in cleaned_features:
                        feat_counter += 1
                    cleaned_features.append(f"特征{feat_counter}")
                    feat_counter += 1
            features = cleaned_features

        # 遍历每个样本，生成句子
        for sample_idx, sample in enumerate(samples, start=1):
            # 配对特征和值，过滤空特征（避免多余的「：无」）
            key_value_pairs = []
            for feat, val in zip(features, sample):
                clean_val = clean_table_text(val)
                clean_feat = feat.strip() if feat.strip() else f"特征{len(key_value_pairs) + 1}"
                # 只保留有意义的配对（避免特征名空或值为空且无意义的情况）
                if clean_feat != "无" and (clean_val != "无" or len(key_value_pairs) < len(features)):
                    key_value_pairs.append(f"{clean_feat}：{clean_val}")

            # 拼接成完整句子（避免空句子）
            if key_value_pairs:
                sentence = "，".join(key_value_pairs)
                table_texts.append(f"{sentence}")

        # 如果有表格内容，返回格式化的文本
        if table_texts:
            return "\n\n".join(table_texts)
        else:
            return "该表格无有效数据"
    except Exception as e:
        logger.warning(f"表格转换为文本失败：{str(e)}")
        return "该表格处理失败，无法显示数据"


def pdf_to_md_with_images(pdf_file_path, md_dir, img_dir):
    """处理单个PDF文件转换（兼容低版本PyMuPDF，仅识别有边框表格并转为文本描述）"""
    pdf_filename = os.path.basename(pdf_file_path)
    pdf_name_without_ext = os.path.splitext(pdf_filename)[0]
    cleaned_pdf_name = clean_filename(pdf_name_without_ext)

    # 提前创建输出目录
    os.makedirs(md_dir, exist_ok=True)
    os.makedirs(img_dir, exist_ok=True)

    # 打开PDF文档（供PyMuPDF使用）
    doc = fitz.open(pdf_file_path)
    total_pages = len(doc)

    # 使用camelot提取表格（仅用lattice模式，只识别有边框表格）
    try:
        # 仅使用lattice模式（专门识别有边框表格，准确率更高）
        camelot_tables = camelot.read_pdf(pdf_file_path, pages='all', flavor='lattice')
        logger.info(f"lattice模式成功提取到 {len(camelot_tables)} 个有边框表格")
    except Exception as e:
        logger.warning(f"lattice模式提取有边框表格失败：{str(e)}，将不处理表格，直接提取原文")
        camelot_tables = []

    # 表格相关记录（去重页码、总数量）
    table_pages = set()  # 表格所在页码（去重）
    img_pages = set()  # 图片所在页码（去重）
    markdown_content = []
    page_img_total = 0
    total_text_blocks = 0
    total_tables = len(camelot_tables)  # 总表格数（仅含边框表格）

    # 构建表格页码映射（页码→表格列表）
    table_page_map = {}
    for table in camelot_tables:
        page_num = table.page  # camelot的页码从1开始
        if page_num not in table_page_map:
            table_page_map[page_num] = []
        table_page_map[page_num].append(table)
        table_pages.add(page_num)

    for page_num, page in enumerate(doc):
        current_page = page_num + 1  # 转为1-based页码
        logger.info(f"处理页面 {current_page}/{total_pages}")

        # 步骤0：获取当前页的有边框表格（来自camelot）
        current_page_tables = table_page_map.get(current_page, [])
        page_table_count = len(current_page_tables)
        table_elements = []  # 存储表格元素（用于排序）
        all_blocks = page.get_text("blocks", sort=True)  # 提前获取所有文本块（用于表格标题提取）

        for table_idx, table in enumerate(current_page_tables):
            # 获取表格的边界框（兼容camelot新旧版本：旧版用bbox，新版用_bbox）
            page_height = page.rect.height
            page_width = page.rect.width
            try:
                # 旧版camelot（0.8.x及以下）：公开属性bbox
                camelot_bbox = table.bbox
            except AttributeError:
                try:
                    # 新版camelot（0.10.x及以上）：私有属性_bbox（实际存储边界框）
                    camelot_bbox = table._bbox
                except AttributeError:
                    # 极端情况：无法获取边界框，用全页面默认值（不影响后续处理）
                    logger.warning(f"表格{table_idx+1}（页面{current_page}）无法获取边界框，将正常保留文本内容")
                    camelot_bbox = (0, 0, page_width, page_height)

            # 转换为PyMuPDF的坐标系统（y轴向上为正），同时确保坐标合法
            x1, y1, x2, y2 = camelot_bbox
            # 修正超出页面范围的坐标（避免异常）
            x1 = max(0, min(x1, page_width))
            y1 = max(0, min(y1, page_height))
            x2 = max(x1, min(x2, page_width))
            y2 = max(y1, min(y2, page_height))

            table_bbox = fitz.Rect(
                x1,
                page_height - y2,  # 转换y轴方向（camelot向下为正，PyMuPDF向上为正）
                x2,
                page_height - y1
            )

            # 提取表格上方的文本作为标题（搜索表格上方50px内的文本块）
            table_title = "无标题表格"
            for block in all_blocks:
                block_content = block[4].strip()
                if not block_content:
                    continue
                block_bbox = fitz.Rect(block[0], block[1], block[2], block[3])
                # 检查文本块是否在表格上方（y坐标差小于50px，且x范围重叠）
                if (block_bbox[3] < table_bbox[1] < block_bbox[3] + 50 and
                    block_bbox[0] < table_bbox[2] and block_bbox[2] > table_bbox[0]):
                    table_title = clean_text(block_content)
                    break

            # 处理表格为文本描述
            table_text = process_table_to_text(table)

            table_elements.append({
                "type": "table",
                "y0": table_bbox[1],  # 表格顶部y坐标（用于排序）
                "info": {
                    "bbox": table_bbox,
                    "table_idx": table_idx + 1,
                    "table_title": table_title,
                    "table_text": table_text
                }
            })

        # 步骤1：提取当前页所有图片（原有逻辑优化，转为元素存储）
        raw_images = page.get_images(full=True)
        page_images = []
        for img_idx, img_info in enumerate(raw_images):
            xref = img_info[0]
            img_rects = page.get_image_rects(xref)
            if not img_rects:
                continue
            img_rect = img_rects[0]
            page_images.append({
                "xref": xref,
                "rect": img_rect,
                "img_idx": img_idx + 1
            })
        page_images.sort(key=lambda x: x["rect"][1])
        page_img_count = len(page_images)
        page_img_total += page_img_count
        img_elements = []  # 存储图片元素（用于排序）

        for img in page_images:
            img_elements.append({
                "type": "image",
                "y0": img["rect"][1],  # 图片顶部y坐标（用于排序）
                "info": img
            })

        # 记录图片所在页码（去重）
        if page_img_count > 0:
            img_pages.add(current_page)

        # 步骤2：提取当前页所有文本块（排除表格区域的文本）
        text_elements = []  # 存储文本元素（用于排序）

        for block in all_blocks:
            block_content = block[4]
            block_type = block[5]
            block_bbox = fitz.Rect(block[0], block[1], block[2], block[3])  # 文本块边界框
            block_y0 = block[1]

            # 过滤无效文本块（原有逻辑保留）
            if not block_content:
                continue
            if block_content.lstrip('-').isdigit() and block_type == 1:
                continue

            # 排除表格区域内的文本（避免表格文字重复提取）
            overlap_with_table = False
            for table_elem in table_elements:
                table_bbox = table_elem["info"]["bbox"]
                if block_bbox.intersects(table_bbox):
                    overlap_with_table = True
                    break
            if overlap_with_table:
                continue

            # 清理文本并添加到元素列表
            cleaned_text = clean_text(block_content)
            if cleaned_text:
                text_elements.append({
                    "type": "text",
                    "y0": block_y0,
                    "content": cleaned_text
                })
                total_text_blocks += 1  # 统计有效文本块

        # 步骤3：合并所有元素（表格、图片、文本），按页面从上到下排序
        all_elements = table_elements + img_elements + text_elements
        all_elements.sort(key=lambda x: x["y0"])  # 按顶部y坐标排序

        # 步骤4：依次处理排序后的元素
        for elem in all_elements:
            if elem["type"] == "table":
                # 处理表格：添加【表格开始】【表格结束】标记
                table_info = elem["info"]
                table_idx = table_info["table_idx"]
                table_title = table_info["table_title"]
                table_text = table_info["table_text"]

                # 新增：表格前后添加标记
                # markdown_content.append(f"### 表格{table_idx}（{table_title}，页面{current_page}）\n\n")
                markdown_content.append("【表格开始】\n\n")  # 表格开始标记
                markdown_content.append(table_text)
                markdown_content.append("\n\n【表格结束】\n\n")  # 表格结束标记

            elif elem["type"] == "image":
                # 处理图片（原有逻辑保留，增加错误捕获）
                try:
                    img_info = elem["info"]
                    xref = img_info["xref"]
                    img_idx = img_info["img_idx"]

                    base_image = doc.extract_image(xref)
                    if base_image and "image" in base_image:
                        img_bytes = base_image["image"]
                        img_ext = base_image["ext"]
                        img_filename = f"{cleaned_pdf_name}_page{current_page}_img{img_idx}.{img_ext}"
                        img_path = os.path.join(img_dir, img_filename)

                        with open(img_path, "wb") as f:
                            f.write(img_bytes)

                        relative_img_path = os.path.relpath(img_path, md_dir)
                        markdown_content.append(
                            f"![{cleaned_pdf_name} 页面{current_page}图片{img_idx}]({relative_img_path})\n\n")
                    else:
                        logger.warning(f"页面{current_page}图片{img_idx}提取失败：未获取到图片数据")
                except Exception as e:
                    logger.warning(f"页面{current_page}图片{img_idx}处理失败：{str(e)}")

            elif elem["type"] == "text":
                # 处理文本（原有逻辑保留）
                markdown_content.append(elem["content"])
                markdown_content.append("\n")

        # 页面分隔线（最后一页不添加）
        if page_num < total_pages - 1:
            markdown_content.append("\n\n")

    # 按新规则生成MD文件名（核心功能保留）
    # 处理表格部分
    if table_pages:
        table_part = f"表格_{format_page_nums(table_pages)}"
    else:
        table_part = "无表格"

    # 处理图片部分
    if img_pages:
        img_part = f"图片_{format_page_nums(img_pages)}"
    else:
        img_part = "无图片"

    md_filename = f"{cleaned_pdf_name}-{table_part}-{img_part}.md"
    md_path = os.path.abspath(os.path.join(md_dir, md_filename))

    # 保存MD文件
    with open(md_path, "w", encoding="utf-8") as f:
        final_content = "".join(markdown_content).rstrip("---\n\n")
        f.write(final_content)

    doc.close()

    # 返回结果（包含表格相关信息）
    return {
        "pdf_filename": pdf_filename,
        "md_filename": md_filename,
        "total_pages": total_pages,
        "table_pages": sorted(list(table_pages)) if table_pages else [],
        "img_pages": sorted(list(img_pages)) if img_pages else [],
        "total_text_blocks": total_text_blocks,
        "total_images": page_img_total,
        "total_tables": total_tables,
        "md_path": md_path
    }


def clean_text(text):
    """轻度清理，保留所有有效文本，仅去除无效字符"""
    text = re.sub(r'\r\n?', '\n', text)
    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f]', '', text)
    text = text.replace('\u3000', ' ')
    text = re.sub(r'\n{4,}', '\n\n\n', text)
    return text


def batch_pdf_to_md(abs_dir, pdf_dir, md_dir, json_dir, docx_dir, img_dir="images", enable_clean=True):
    """批量处理PDF文件夹下的所有PDF文件（仅识别有边框表格）"""
    pdf_dir = os.path.abspath(pdf_dir)
    md_dir = os.path.abspath(md_dir)
    img_dir = os.path.abspath(os.path.join(md_dir, img_dir))
    docx_dir = os.path.abspath(docx_dir)
    json_dir = os.path.abspath(json_dir)

    # 提前创建所有输出目录（只创建一次，提升效率）
    os.makedirs(md_dir, exist_ok=True)
    os.makedirs(img_dir, exist_ok=True)
    os.makedirs(docx_dir, exist_ok=True)
    os.makedirs(json_dir, exist_ok=True)

    if not os.path.exists(pdf_dir):
        logger.error(f"错误：PDF目录不存在 - {pdf_dir}")
        return

    # 预加载所有PDF文件路径（避免循环中重复IO）
    pdf_files = [
        os.path.join(pdf_dir, f)
        for f in os.listdir(pdf_dir)
        if f.lower().endswith('.pdf')
    ]
    total_pdfs = len(pdf_files)

    if not pdf_files:
        logger.warning(f"在PDF目录 {pdf_dir} 中未找到任何PDF文件")
        return

    processed_pdfs = 0
    failed_pdfs = []
    total_stats = {
        "total_pages": 0,
        "total_text_blocks": 0,
        "total_images": 0,
        "total_tables": 0,
        "total_table_pages": set(),
        "total_img_pages": set()
    }

    logger.info(f"=== 批量处理PDF转Markdown（仅识别有边框表格并转为文本描述，兼容低版本PyMuPDF）===")
    logger.info(f"PDF目录：{pdf_dir}")
    logger.info(f"MD输出目录：{md_dir}")
    logger.info(f"图片输出目录：{img_dir}")
    logger.info(f"DOCX输出目录：{docx_dir}")
    logger.info(f"找到PDF文件总数：{total_pdfs}\n")

    for idx, pdf_file_path in enumerate(pdf_files, 1):
        pdf_filename = os.path.basename(pdf_file_path)
        logger.info(f"[{idx}/{total_pdfs}] 正在处理：{pdf_filename}")

        try:
            result = pdf_to_md_with_images(pdf_file_path, md_dir, img_dir)

            # 更新统计信息
            processed_pdfs += 1
            total_stats["total_pages"] += result["total_pages"]
            total_stats["total_text_blocks"] += result["total_text_blocks"]
            total_stats["total_images"] += result["total_images"]
            total_stats["total_tables"] += result["total_tables"]
            if result["table_pages"]:
                total_stats["total_table_pages"].update(result["table_pages"])
            if result["img_pages"]:
                total_stats["total_img_pages"].update(result["img_pages"])

            # 打印单个文件处理结果（新增表格信息）
            table_pages_str = ", ".join(map(str, result["table_pages"])) if result["table_pages"] else "无"
            img_pages_str = ", ".join(map(str, result["img_pages"])) if result["img_pages"] else "无"
            logger.info(f"  ✅ 处理成功！")
            logger.info(f"    - PDF总页数：{result['total_pages']}页")
            logger.info(f"    - 有边框表格所在页码：{table_pages_str}")
            logger.info(f"    - 图片所在页码：{img_pages_str}")
            logger.info(f"    - 提取文本块：{result['total_text_blocks']}个")
            logger.info(f"    - 提取图片：{result['total_images']}张")
            logger.info(f"    - 提取有边框表格（转为文本）：{result['total_tables']}个")
            logger.info(f"    - 生成MD文件：{result['md_filename']}")
            print()

            # MD转DOCX处理（只处理当前PDF生成的MD文件，避免重复转换）
            logger.info(f"开始处理MD转DOCX：{result['md_filename']}")
            md_file_path = result["md_path"]  # 直接使用当前PDF生成的MD路径
            if not os.path.exists(md_file_path):
                logger.error(f'[警告] 未找到生成的MD文件：{md_file_path}')
            else:
                md_file_prefix = os.path.splitext(result["md_filename"])[0]
                output_docx_path = os.path.join(docx_dir, f'{md_file_prefix}.docx')

                logger.info(f'{"=" * 60}')
                logger.info(f'[MD转DOCX] 文件名：{result["md_filename"]}')
                logger.info(f'[输出路径] DOCX：{output_docx_path}')
                logger.info(f'{"=" * 60}')

                process_markdown_file(
                    file_path=md_file_path,
                    abs_dir=abs_dir,
                    output_docx_path=output_docx_path,
                    md_file_prefix=md_file_prefix,
                    enable_clean=enable_clean,
                    encoding='utf-8'
                )
                logger.info(f'\n[MD转DOCX完成] 文件已输出到：{output_docx_path}\n')

        except Exception as e:
            logger.error(f"处理 {pdf_filename} 时出错：{str(e)}")
            failed_pdfs.append((pdf_filename, str(e)))
            print()

    # 格式化总体统计信息
    total_table_pages_formatted = format_page_nums(total_stats["total_table_pages"]).replace("_", "、") or "无"
    total_img_pages_formatted = format_page_nums(total_stats["total_img_pages"]).replace("_", "、") or "无"

    logger.info(f"=== 批量处理完成 ===")
    logger.info(f"总文件数：{total_pdfs}")
    logger.info(f"成功处理：{processed_pdfs}个")
    logger.info(f"处理失败：{len(failed_pdfs)}个")
    logger.info(f"\n总体统计：")
    logger.info(f"  - 总PDF页数：{total_stats['total_pages']}页")
    logger.info(f"  - 所有有边框表格所在页码（去重）：{total_table_pages_formatted}")
    logger.info(f"  - 所有图片所在页码（去重）：{total_img_pages_formatted}")
    logger.info(f"  - 总文本块：{total_stats['total_text_blocks']}个")
    logger.info(f"  - 总图片数：{total_stats['total_images']}张")
    logger.info(f"  - 总有边框表格数（转为文本）：{total_stats['total_tables']}个")
    logger.info(f"\n输出目录：")
    logger.info(f"  - MD文件：{md_dir}")
    logger.info(f"  - 图片文件：{img_dir}")
    logger.info(f"  - DOCX文件：{docx_dir}")

    if failed_pdfs:
        logger.info(f"\n❌ 处理失败的文件列表：")
        for pdf_name, error_msg in failed_pdfs:
            logger.error(f"  - {pdf_name}：{error_msg[:100]}...")

if __name__ == "__main__":


    # 获取当前脚本所在路径
    abs_path = os.path.dirname(__file__)
    print(f"当前脚本所在路径：{abs_path}")

    # 批量处理配置（修改这里的路径即可）
    BATCH_CONFIG = {
        "abs_dir": abs_path,
        "pdf_dir": os.path.join(abs_path, "pdf_data"),  # 所有PDF文件所在的目录
        "md_dir": os.path.join(abs_path, "md_data"),  # MD文件输出目录
        "json_dir": os.path.join(abs_path, "json_data"),
        "docx_dir": os.path.join(abs_path, "docx_result"),  # DOCX文件输出目录
        "img_dir": "images",  # 图片输出目录（相对于md_dir）
        "enable_clean": False  # True=启用清理，False=保留所有文件
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