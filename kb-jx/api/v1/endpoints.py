from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from typing import List, Dict, Optional
import asyncio
import uuid
import os
import hashlib
from datetime import datetime
from pathlib import Path

from config import config
from models.schemas import (
    AnalyzeResponse, FileInfo, BatchUploadResponse, 
    BatchStatusResponse, Progress, Downloads
)
from services.detector import DocumentDetector
from services.converter import DocumentConverter
from services.zipper import ZipperService
from services.text_pipeline import TextPipeline
from utils.file_handler import FileHandler
from utils.logger import get_logger
from utils.cleaner import StorageCleaner
from utils.dedup_store import DedupStore, compute_file_sha256, compute_sha256

logger = get_logger("api")

router = APIRouter()

# 初始化去重存储（从配置读取）
dedup_store = DedupStore(
    backend="redis" if config.Redis.ENABLED else "memory",
    redis_config=config.get_redis_config()
)

# 初始化文本管线（从配置读取）
text_pipeline = TextPipeline(
    dedup_store=dedup_store,
    min_paragraph_len=config.TextPipeline.MIN_PARAGRAPH_LEN,
    simhash_distance_threshold=config.TextPipeline.SIMHASH_DISTANCE_THRESHOLD,
    enable_near_duplicate=config.TextPipeline.ENABLE_NEAR_DUPLICATE,
    custom_noise_patterns=config.TextPipeline.CUSTOM_NOISE_PATTERNS,
    enable_cross_doc_dedup=False
)

# 初始化服务（注入 text_pipeline）
file_handler = FileHandler()
detector = DocumentDetector()
converter = DocumentConverter(text_pipeline=text_pipeline)
zipper = ZipperService()
cleaner = StorageCleaner()

# 存储批量任务状态
batch_tasks = {}


@router.post("/document/analyze", response_model=AnalyzeResponse)
async def analyze_document(file: UploadFile = File(...)):
    """单文件上传和分析（集成文本管线）"""
    logger.info(f"单文件分析请求: {file.filename}")
    
    try:
        # 保存原始文件
        original_path = await file_handler.save_upload_file(
            file, 
            file_handler.original_dir,
            keep_path=False
        )
        logger.debug(f"文件保存成功: {original_path}")
        
        # 检测文档类型
        is_pure_text, reason = detector.detect(original_path)
        logger.info(f"文档检测结果: {file.filename} -> 纯文本={is_pure_text}, 原因={reason}")
        
        # 获取路径信息
        path_info = file_handler.parse_file_path(file)
        file_id = str(uuid.uuid4())
        
        # 构建原始文件信息
        original_file = FileInfo(
            name=path_info['filename'],
            path=path_info['full_path'],
            download_url=f"/api/v1/files/download/original/{file_id}{path_info['extension']}"
        )
        
        converted_file = None
        pipeline_info = None
        
        # 如果是纯文本，转换为 docx（应用文本管线）
        if is_pure_text:
            converted_path = file_handler.converted_dir / f"{file_id}.docx"
            result = converter.convert_to_docx(
                original_path, 
                str(converted_path),
                doc_name=file.filename or "unknown"
            )
            
            if result["success"]:
                logger.info(f"文档转换成功: {file.filename} -> {converted_path.name}")
                
                # 记录管线统计信息
                if "pipeline_stats" in result:
                    pipeline_info = result["pipeline_stats"]
                    logger.debug(f"文本管线统计: {pipeline_info}")
                
                converted_file = FileInfo(
                    name=f"{path_info['stem']}.docx",
                    path=f"{path_info['directory']}/{path_info['stem']}.docx".lstrip('/'),
                    download_url=f"/api/v1/files/download/converted/{file_id}.docx"
                )
            elif result.get("doc_duplicate"):
                # 文档级去重命中
                logger.warning(f"文档去重命中: {file.filename}")
                return AnalyzeResponse(
                    is_pure_text=is_pure_text,
                    original_file=original_file,
                    converted_file=None,
                    message=result.get("message", "文档已存在")
                )
            else:
                logger.error(f"文档转换失败: {file.filename}, {result.get('message')}")
        
        return AnalyzeResponse(
            is_pure_text=is_pure_text,
            original_file=original_file,
            converted_file=converted_file
        )
    except Exception as e:
        logger.error(f"单文件分析错误: {file.filename}, 错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"处理文件失败: {str(e)}")


@router.post("/documents/batch-upload", response_model=BatchUploadResponse)
async def batch_upload_documents(files: List[UploadFile] = File(...)):
    """批量上传文档"""
    logger.info(f"批量上传请求: {len(files)} 个文件")
    
    # 生成任务 ID
    task_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    logger.info(f"创建任务: {task_id}")
    
    # 创建任务目录
    task_dir = file_handler.get_batch_dir(task_id)
    logger.debug(f"任务目录: {task_dir}")
    
    # 初始化任务状态
    batch_tasks[task_id] = {
        'status': 'processing',
        'total': len(files),
        'completed': 0,
        'pure_text_count': 0,
        'rich_media_count': 0,
        'pure_text_files': [],
        'rich_media_files': [],
        'task_dir': str(task_dir),
        'dedup_stats': {  # 新增：去重统计
            'doc_duplicates': 0,
            'para_exact_dup_total': 0,
            'para_near_dup_total': 0,
            'noise_removed_total': 0
        }
    }
    
    # 关键修复：在这里先读取所有文件内容
    logger.info(f"开始读取 {len(files)} 个文件内容...")
    file_data_list = []
    for i, file in enumerate(files):
        try:
            # 读取文件内容和元数据
            content = await file.read()
            file_data = {
                'filename': file.filename,
                'content': content,
                'content_type': file.content_type
            }
            file_data_list.append(file_data)
            logger.debug(f"读取文件 [{i+1}/{len(files)}]: {file.filename} ({len(content)} bytes)")
        except Exception as e:
            logger.error(f"读取文件 {file.filename} 失败: {e}")
            # 记录失败但继续处理
            file_data_list.append(None)
    
    logger.info(f"文件读取完成, 成功: {len([f for f in file_data_list if f is not None])}/{len(files)}")
    
    # 启动异步处理（传入文件数据而非 UploadFile 对象）
    asyncio.create_task(process_batch_files(file_data_list, task_id, task_dir))
    logger.info(f"后台处理任务已启动: {task_id}")
    
    return BatchUploadResponse(
        task_id=task_id,
        total_files=len(files),
        status_url=f"/api/v1/batch/status/{task_id}"
    )


async def process_batch_files(file_data_list: List[Dict], task_id: str, task_dir: Path):
    """异步处理批量文件（接收文件数据而非 UploadFile）"""
    logger.info(f"[任务 {task_id}] 开始处理 {len(file_data_list)} 个文件")
    
    # 步骤1：先计算所有文件的SHA256，实现任务内原始文件去重
    seen_file_hashes = {}  # {file_hash: (index, filename)}
    file_hash_map = {}  # {index: file_hash}
    duplicate_indices = set()  # 记录重复文件的索引
    
    logger.info(f"[任务 {task_id}] 步骤1: 计算原始文件哈希并去重...")
    for i, file_data in enumerate(file_data_list):
        if file_data is None:
            continue
        
        try:
            filename = file_data['filename']
            content = file_data['content']
            
            # 计算原始文件的SHA256
            file_hash = hashlib.sha256(content).hexdigest()
            file_hash_map[i] = file_hash
            
            # 检查是否已经见过这个哈希
            if file_hash in seen_file_hashes:
                first_index, first_filename = seen_file_hashes[file_hash]
                logger.info(f"[任务 {task_id}] 原始文件重复: {filename} 与 {first_filename} 完全相同，仅保留第一个")
                duplicate_indices.add(i)
            else:
                seen_file_hashes[file_hash] = (i, filename)
                logger.debug(f"[任务 {task_id}] 文件 [{i+1}]: {filename}, hash={file_hash[:16]}...")
        except Exception as e:
            logger.error(f"[任务 {task_id}] 计算文件 {i+1} 哈希失败: {e}")
    
    logger.info(f"[任务 {task_id}] 原始文件去重完成: 总数={len(file_data_list)}, 独一份={len(seen_file_hashes)}, 重复={len(duplicate_indices)}")
    
    # 从配置读取并发数
    semaphore = asyncio.Semaphore(config.BatchProcess.MAX_CONCURRENT_TASKS)
    
    async def process_one(file_data: Dict, index: int):
        async with semaphore:
            if file_data is None:
                logger.warning(f"[任务 {task_id}] 文件 [{index+1}] 数据为空，跳过")
                return None
                
            filename = ""
            original_file = None  # 初始化为None
            try:
                # 从文件数据中获取信息
                filename = file_data['filename']
                content = file_data['content']
                logger.debug(f"[任务 {task_id}] 开始处理文件 [{index+1}]: {filename}")
                
                # 解析路径（手动构建 path_info）
                from pathlib import Path as PathLib
                path_obj = PathLib(filename)
                path_info = {
                    'full_path': filename,
                    'directory': str(path_obj.parent) if path_obj.parent != PathLib('.') else '',
                    'filename': path_obj.name,
                    'stem': path_obj.stem,
                    'extension': path_obj.suffix
                }
                
                # 保存原始文件（保留路径） - 所有文件都先保存，包括重复和临时文件
                original_dir = task_dir / "original"
                original_dir.mkdir(exist_ok=True)
                
                if path_info['directory']:
                    file_dir = original_dir / path_info['directory']
                    file_dir.mkdir(parents=True, exist_ok=True)
                    original_file = file_dir / path_info['filename']
                else:
                    original_file = original_dir / path_info['filename']
                
                # 写入磁盘
                with open(original_file, 'wb') as f:
                    f.write(content)
                logger.debug(f"[任务 {task_id}] 文件保存: {original_file}")
                
                # 检查是否为重复文件，如果是则返回特殊标记（但文件已保存）
                if index in duplicate_indices:
                    logger.debug(f"[任务 {task_id}] 跳过重复文件 [{index+1}]")
                    return {
                        'skipped': True,
                        'skip_reason': 'duplicate',
                        'filename': filename,
                        'original_file': str(original_file)  # 保存了原始文件路径
                    }
                
                # 检查是否为临时锁文件（~$ 开头）
                if config.Conversion.SKIP_TEMP_FILES and path_info['filename'].startswith('~$'):
                    logger.info(f"[任务 {task_id}] 跳过临时锁文件: {filename}")
                    return {
                        'path_info': path_info,
                        'is_pure_text': False,
                        'reason': '临时锁文件，已跳过',
                        'original_file': str(original_file),  # 保存了原始文件路径
                        'filename': filename,
                        'skipped': True,
                        'skip_reason': 'temp_file'
                    }
                
                # 先检测原文件内容类型
                is_pure_text, reason = detector.detect(str(original_file))
                logger.info(f"[任务 {task_id}] 检测结果: {filename} -> 纯文本={is_pure_text}, {reason}")
                
                result = {
                    'path_info': path_info,
                    'original_file': str(original_file),
                    'filename': filename,
                    'is_pure_text': is_pure_text,
                    'reason': reason
                }
                
                # 富媒体文件的去重已经在任务开始时完成，这里不需要再次检查
                
                # 判断是否需要格式转换
                old_format_map = {
                    '.doc': '.docx',
                    '.xls': '.xlsx',
                    '.ppt': '.pptx'
                }
                
                need_conversion = False
                target_ext = path_info['extension']
                
                # 旧格式转换策略：根据是否纯文本决定目标格式
                if path_info['extension'] in old_format_map:
                    need_conversion = True
                    if is_pure_text:
                        # 纯文本：统一转为 docx 并应用文本管线
                        target_ext = '.docx'
                        logger.info(f"[任务 {task_id}] 纯文本旧格式转为docx: {path_info['extension']} -> {target_ext}")
                    else:
                        # 富媒体：转为对应的新格式（保留富媒体内容）
                        target_ext = old_format_map[path_info['extension']]
                        logger.info(f"[任务 {task_id}] 富媒体旧格式转为新格式: {path_info['extension']} -> {target_ext}")
                # 新格式文档转换策略
                elif path_info['extension'] in ['.docx', '.xlsx', '.pptx']:
                    if is_pure_text:
                        # 纯文本：转为 docx 应用文本管线清洗
                        need_conversion = True
                        target_ext = '.docx'
                        logger.info(f"[任务 {task_id}] 纯文本文档转为docx清洗: {path_info['extension']} -> {target_ext}")
                    else:
                        # 富媒体：保持原格式，不转换
                        need_conversion = False
                        logger.info(f"[任务 {task_id}] 富媒体文档保持原格式: {path_info['extension']}")
                
                # 执行格式转换
                if need_conversion:
                    converted_dir = task_dir / "converted"
                    converted_dir.mkdir(exist_ok=True)
                    
                    if path_info['directory']:
                        converted_file_dir = converted_dir / path_info['directory']
                        converted_file_dir.mkdir(parents=True, exist_ok=True)
                        converted_file = converted_file_dir / f"{path_info['stem']}{target_ext}"
                    else:
                        converted_file = converted_dir / f"{path_info['stem']}{target_ext}"
                    
                    # 修复：使用 Path 处理路径拼接，然后转为 posix 格式（修复问题1）
                    if path_info['directory']:
                        # Windows 路径转换为正斜杠，兼容 ZIP 归档
                        converted_path = str(Path(path_info['directory']) / f"{path_info['stem']}{target_ext}").replace('\\', '/')
                    else:
                        # 根目录文件，无前导分隔符（修复问题4）
                        converted_path = f"{path_info['stem']}{target_ext}"
                    
                    logger.debug(f"[任务 {task_id}] 开始转换: {filename} -> {converted_file.name}")
                    convert_result = converter.convert_to_docx(
                        str(original_file), 
                        str(converted_file),
                        doc_name=filename,
                        apply_pipeline=is_pure_text  # 只有纯文本才应用文本管线
                    )
                    
                    if convert_result["success"]:
                        logger.info(f"[任务 {task_id}] 转换成功: {filename} -> {converted_file.name}")
                        
                        result['converted_file'] = str(converted_file)
                        result['converted_path'] = converted_path
                        
                        # 富媒体文档转换后，不再需要执行去重（已经在任务开始时去重）
                        
                        # 记录管线统计（仅纯文本docx有）
                        if "pipeline_stats" in convert_result:
                            pipeline_stats = convert_result["pipeline_stats"]
                            result['pipeline_stats'] = pipeline_stats
                            logger.debug(f"[任务 {task_id}] 管线统计: 段落去重={pipeline_stats.get('paragraphs_exact_dup', 0)+pipeline_stats.get('paragraphs_near_dup', 0)}, 噪声移除={pipeline_stats.get('noise_removed_count', 0)}")
                    elif convert_result.get("doc_duplicate"):
                        # 纯文本文档级去重命中（文本管线内部去重）
                        # 注意：清洗后的文件已经被保存到 converted_file 路径
                        logger.warning(f"[任务 {task_id}] 文档去重命中: {filename}")
                        result['doc_duplicate'] = True
                        # 保留 converted_file 路径，因为清洗后的文件已经存在
                        result['converted_file'] = str(converted_file)
                        result['converted_path'] = converted_path
                    else:
                        logger.error(f"[任务 {task_id}] 转换失败: {filename}, {convert_result.get('message')}")
                        # 转换失败，保留原文件信息
                
                return result
                
            except Exception as e:
                # 使用保存的 filename
                display_name = filename if filename else f"<file_{index}>"
                error_msg = f"{type(e).__name__}: {str(e)}"
                logger.error(f"[任务 {task_id}] 处理文件 {display_name} 错误: {error_msg}", exc_info=True)
                # 返回特殊标记而不是 None，以便记录失败原因
                return {
                    'skipped': True,
                    'skip_reason': 'error',
                    'error_message': error_msg,
                    'filename': display_name,
                    'original_file': str(original_file) if original_file else ''  # 如果文件已保存则返回路径
                }
    
    # 并发处理所有文件
    tasks = [process_one(file_data, i) for i, file_data in enumerate(file_data_list)]
    logger.info(f"[任务 {task_id}] 开始并发处理，并发数: {config.BatchProcess.MAX_CONCURRENT_TASKS}")
    results = await asyncio.gather(*tasks)
    logger.info(f"[任务 {task_id}] 所有文件处理完成")
    
    # 分类结果
    pure_text_files = []
    rich_media_files = []
    failed_files = []  # 记录处理失败的文件
    duplicate_files = []  # 记录原始文件重复的文件（新增）
    temp_files = []  # 记录临时锁文件（新增）
    
    # 新增：任务内独一份文件（基于SHA256去重，保留最早）
    unique_pure_text_files = {}  # {file_hash: file_info}
    unique_rich_media_files = {}  # {file_hash: file_info}
    
    # 统计去重与清洗信息
    doc_duplicates = 0
    para_exact_dup_total = 0
    para_near_dup_total = 0
    noise_removed_total = 0
    
    for i, result in enumerate(results):
        if result is None:
            # 真正的处理失败（非重复）
            try:
                if i < len(file_data_list) and file_data_list[i] is not None:
                    failed_file = file_data_list[i]['filename']
                    failed_files.append({'filename': failed_file, 'reason': '未知错误'})
                    logger.warning(f"[任务 {task_id}] 文件处理失败，已跳过: {failed_file}")
            except (KeyError, IndexError, TypeError) as e:
                logger.debug(f"[任务 {task_id}] 无法获取失败文件名: {e}")
            continue
        
        # 检查是否为重复文件（原始文件去重）
        if result.get('skipped') and result.get('skip_reason') == 'duplicate':
            duplicate_files.append({
                'filename': result.get('filename', 'unknown'),
                'original_file': result.get('original_file', '')
            })
            logger.debug(f"[任务 {task_id}] 原始文件去重：已跳过 {result.get('filename', 'unknown')}")
            continue
        
        # 检查是否为处理失败（错误）
        if result.get('skipped') and result.get('skip_reason') == 'error':
            failed_files.append({
                'filename': result.get('filename', 'unknown'),
                'reason': result.get('error_message', '未知错误'),
                'original_file': result.get('original_file', '')  # 修复：保存原始文件路径
            })
            logger.warning(f"[任务 {task_id}] 文件处理错误: {result.get('filename', 'unknown')}, 原因: {result.get('error_message', '未知')}")
            continue
        
        # 检查是否为临时锁文件
        if result.get('skipped') and result.get('skip_reason') == 'temp_file':
            temp_files.append({
                'filename': result.get('filename', 'unknown'),
                'reason': result.get('reason', '临时锁文件，已跳过')
            })
            logger.info(f"[任务 {task_id}] 临时锁文件已跳过: {result.get('filename', 'unknown')}")
            continue
        
        # 汇总管线统计
        if "pipeline_stats" in result:
            stats = result["pipeline_stats"]
            para_exact_dup_total += stats.get("paragraphs_exact_dup", 0)
            para_near_dup_total += stats.get("paragraphs_near_dup", 0)
            noise_removed_total += stats.get("noise_removed_count", 0)
        
        # 文档级去重命中，记录但仍然保存文件（因为已经清洗过）
        if result.get("doc_duplicate"):
            doc_duplicates += 1
            is_pure = result.get('is_pure_text', False)
            logger.info(f"[任务 {task_id}] 文档去重命中（但保留清洗后的文件）: {result.get('filename', 'unknown')} ({'纯文本' if is_pure else '富媒体'})")
            # 注意：不 continue，继续处理以便保存清洗后的文件
        
        # 检查 is_pure_text 字段是否存在
        if 'is_pure_text' not in result:
            logger.warning(f"[任务 {task_id}] 结果缺少 is_pure_text 字段: {result}")
            continue
        
        # 根据是否纯文本分类
        if result.get('is_pure_text') and result.get('converted_file'):
            # 纯文本且有转换后的docx文件
            file_info = {
                'original_path': result['path_info']['full_path'],
                'converted_path': result.get('converted_path', ''),
                'converted_file': result.get('converted_file', ''),
                'original_file': result['original_file']
            }
            pure_text_files.append(file_info)
            
            # 独一份去重：基于文本内容而非二进制文件
            try:
                converted_file_path = result.get('converted_file', '')
                if converted_file_path and Path(converted_file_path).exists():
                    # 提取docx文本内容
                    from docx import Document
                    try:
                        doc = Document(converted_file_path)
                        # 提取所有段落文本
                        text_content = '\n'.join([para.text for para in doc.paragraphs if para.text.strip()])
                        # 基于文本内容计算hash
                        content_hash = compute_sha256(text_content)
                        
                        if content_hash not in unique_pure_text_files:
                            unique_pure_text_files[content_hash] = file_info
                            logger.debug(f"[任务 {task_id}] 纯文本独一份: {result['path_info']['full_path']} (content_hash={content_hash[:16]}...)")
                        else:
                            logger.debug(f"[任务 {task_id}] 纯文本内容重复跳过: {result['path_info']['full_path']}")
                    except Exception as doc_err:
                        logger.warning(f"[任务 {task_id}] 无法读取docx内容，使用文件hash: {doc_err}")
                        # 备用方案：使用文件hash
                        file_hash = compute_file_sha256(converted_file_path)
                        if file_hash not in unique_pure_text_files:
                            unique_pure_text_files[file_hash] = file_info
            except Exception as e:
                logger.error(f"[任务 {task_id}] 计算纯文本文件哈希失败: {e}")
        else:
            # 富媒体文档：使用转换后文件（如有）或原文件
            file_to_use = result.get('converted_file') or result['original_file']
            # 如果有转换后的文件，使用转换后的路径；否则使用原始路径
            path_to_use = result.get('converted_path') or result['path_info']['full_path']
            file_info = {
                'path': path_to_use,
                'reason': result.get('reason', '富媒体文档'),
                'original_file': file_to_use
            }
            rich_media_files.append(file_info)
            
            # 独一份去重：计算文件的SHA256
            try:
                if file_to_use and Path(file_to_use).exists():
                    file_hash = compute_file_sha256(file_to_use)
                    if file_hash not in unique_rich_media_files:
                        unique_rich_media_files[file_hash] = file_info
                        logger.debug(f"[任务 {task_id}] 富媒体独一份: {path_to_use} (hash={file_hash[:16]}...)")
                    else:
                        logger.debug(f"[任务 {task_id}] 富媒体重复跳过: {path_to_use}")
            except Exception as e:
                logger.error(f"[任务 {task_id}] 计算富媒体文件哈希失败: {e}")
    
    logger.info(f"[任务 {task_id}] 分类结果: 纯文本={len(pure_text_files)}, 富媒体={len(rich_media_files)}, 失败={len(failed_files)}, 原始重复={len(duplicate_files)}, 临时锁文件={len(temp_files)}, 文档去重={doc_duplicates}")
    logger.info(f"[任务 {task_id}] 清洗统计: 段落精确去重={para_exact_dup_total}, 段落近重复={para_near_dup_total}, 噪声移除={noise_removed_total}")
    logger.info(f"[任务 {task_id}] 独一份统计: 纯文本={len(unique_pure_text_files)}, 富媒体={len(unique_rich_media_files)}")
    
    # 创建 ZIP 包
    zip_dir = task_dir / "downloads"
    zip_dir.mkdir(exist_ok=True)
    logger.info(f"[任务 {task_id}] 开始创建 ZIP 包...")
    
    pure_zip = None
    rich_zip = None
    all_zip = None
    unique_pure_zip = None  # 新增
    unique_rich_zip = None  # 新增
    duplicate_zip = None  # 新增：原始文件重复的 ZIP
    failed_zip = None  # 新增：处理失败的 ZIP
    temp_zip = None  # 新增：临时锁文件的 ZIP
    
    try:
        if pure_text_files:
            logger.debug(f"[任务 {task_id}] 创建纯文本文档 ZIP: {len(pure_text_files)} 个文件")
            pure_zip = zipper.create_structured_zip(
                pure_text_files, 'converted', task_id, str(zip_dir)
            )
            logger.info(f"[任务 {task_id}] 纯文本 ZIP 创建成功: {pure_zip}")
        
        if rich_media_files:
            logger.debug(f"[任务 {task_id}] 创建富媒体文档 ZIP: {len(rich_media_files)} 个文件")
            rich_zip = zipper.create_structured_zip(
                rich_media_files, 'original', task_id, str(zip_dir)
            )
            logger.info(f"[任务 {task_id}] 富媒体 ZIP 创建成功: {rich_zip}")
        
        if pure_text_files or rich_media_files:
            logger.debug(f"[任务 {task_id}] 创建综合 ZIP: 纯文本={len(pure_text_files)}, 富媒体={len(rich_media_files)}")
            all_zip = zipper.create_combined_zip(
                pure_text_files, rich_media_files, task_id, str(zip_dir)
            )
            logger.info(f"[任务 {task_id}] 综合 ZIP 创建成功: {all_zip}")
        
        # 新增：创建独一份 ZIP
        if unique_pure_text_files:
            unique_pure_list = list(unique_pure_text_files.values())
            logger.debug(f"[任务 {task_id}] 创建纯文本独一份 ZIP: {len(unique_pure_list)} 个文件")
            unique_pure_zip = zipper.create_structured_zip(
                unique_pure_list, 'converted', f"{task_id}_unique_pure", str(zip_dir)
            )
            logger.info(f"[任务 {task_id}] 纯文本独一份 ZIP 创建成功: {unique_pure_zip}")
        
        if unique_rich_media_files:
            unique_rich_list = list(unique_rich_media_files.values())
            logger.debug(f"[任务 {task_id}] 创建富媒体独一份 ZIP: {len(unique_rich_list)} 个文件")
            unique_rich_zip = zipper.create_structured_zip(
                unique_rich_list, 'original', f"{task_id}_unique_rich", str(zip_dir)
            )
            logger.info(f"[任务 {task_id}] 富媒体独一份 ZIP 创建成功: {unique_rich_zip}")
        
        # 新增：创建原始文件重复的 ZIP
        if duplicate_files:
            logger.debug(f"[任务 {task_id}] 创建原始文件重复 ZIP: {len(duplicate_files)} 个文件")
            # 构建重复文件的信息列表
            duplicate_file_list = []
            for dup_info in duplicate_files:
                original_file = dup_info['original_file']
                if original_file and Path(original_file).exists():
                    # 构建路径信息
                    dup_path = str(Path(original_file).relative_to(task_dir / 'original'))
                    duplicate_file_list.append({
                        'path': dup_path.replace('\\', '/'),
                        'reason': '原始文件与其他文件完全相同（已去重）',
                        'original_file': original_file
                    })
            
            if duplicate_file_list:
                duplicate_zip = zipper.create_structured_zip(
                    duplicate_file_list, 'original', f"{task_id}_duplicates", str(zip_dir)
                )
                logger.info(f"[任务 {task_id}] 原始文件重复 ZIP 创建成功: {duplicate_zip}")
        
        # 新增：创建处理失败的 ZIP
        if failed_files:
            logger.debug(f"[任务 {task_id}] 创建处理失败文件 ZIP: {len(failed_files)} 个文件")
            # 构建失败文件的信息列表
            failed_file_list = []
            for failed_info in failed_files:
                original_file = failed_info.get('original_file', '')
                
                # 修复：直接使用已保存的 original_file 路径
                if original_file and Path(original_file).exists():
                    # 从完整路径提取相对路径
                    try:
                        relative_path = str(Path(original_file).relative_to(task_dir / 'original'))
                        failed_file_list.append({
                            'path': relative_path.replace('\\', '/'),
                            'reason': failed_info.get('reason', '未知错误'),
                            'original_file': original_file
                        })
                    except ValueError:
                        # 如果路径不在 original 目录下，直接使用文件名
                        failed_file_list.append({
                            'path': failed_info.get('filename', 'unknown'),
                            'reason': failed_info.get('reason', '未知错误'),
                            'original_file': original_file
                        })
                else:
                    # 如果原始文件不存在，记录警告
                    logger.warning(f"[任务 {task_id}] 失败文件的原始副本不存在: {failed_info.get('filename', 'unknown')}, 原因: {failed_info.get('reason', '未知')}")
            
            if failed_file_list:
                failed_zip = zipper.create_structured_zip(
                    failed_file_list, 'original', f"{task_id}_failed", str(zip_dir)
                )
                logger.info(f"[任务 {task_id}] 处理失败文件 ZIP 创建成功: {failed_zip}")
        
        # 新增：创建临时锁文件的 ZIP
        if temp_files:
            logger.debug(f"[任务 {task_id}] 创建临时锁文件 ZIP: {len(temp_files)} 个文件")
            # 构建临时文件的信息列表
            temp_file_list = []
            for temp_info in temp_files:
                if isinstance(temp_info, dict):
                    temp_filename = temp_info.get('filename', '')
                    temp_reason = temp_info.get('reason', '临时锁文件，已跳过')
                else:
                    continue
                
                # 尝试从 original 目录找到该文件
                original_dir = task_dir / "original"
                if isinstance(temp_filename, str):
                    temp_path = original_dir / temp_filename.lstrip('\\\\\\\\')
                else:
                    continue
                
                # 如果原始文件存在，添加到列表
                if temp_path.exists():
                    path_str = str(Path(temp_filename))
                    temp_file_list.append({
                        'path': path_str.replace('\\', '/'),
                        'reason': temp_reason,
                        'original_file': str(temp_path)
                    })
            
            if temp_file_list:
                temp_zip = zipper.create_structured_zip(
                    temp_file_list, 'original', f"{task_id}_temp", str(zip_dir)
                )
                logger.info(f"[任务 {task_id}] 临时锁文件 ZIP 创建成功: {temp_zip}")
    except Exception as e:
        logger.error(f"[任务 {task_id}] ZIP 创建失败: {e}", exc_info=True)
    
    # 更新任务状态
    successful_count = len([r for r in results if r is not None and not (r.get('skipped') and r.get('skip_reason') in ('duplicate', 'error', 'temp_file'))])
    batch_tasks[task_id].update({
        'status': 'completed',
        'completed': successful_count,  # 只统计成功处理的文件（不包括重复和失败）
        'pure_text_count': len(pure_text_files),
        'rich_media_count': len(rich_media_files),
        'duplicate_count': len(duplicate_files),  # 新增：原始文件重复数量
        'failed_count': len(failed_files),  # 新增：处理失败数量
        'temp_file_count': len(temp_files),  # 新增：临时锁文件数量
        'unique_pure_count': len(unique_pure_text_files),  # 新增：独一份纯文本数量
        'unique_rich_count': len(unique_rich_media_files),  # 新增：独一份富媒体数量
        'pure_text_files': [
            {'original_path': f['original_path'], 'converted_path': f['converted_path']}
            for f in pure_text_files
        ],
        'rich_media_files': [
            {'path': f['path'], 'reason': f['reason']}
            for f in rich_media_files
        ],
        'downloads': {
            'pure_text_converted': pure_zip,
            'rich_media_original': rich_zip,
            'all_files': all_zip,
            'unique_pure_text': unique_pure_zip,  # 新增
            'unique_rich_media': unique_rich_zip,  # 新增
            'duplicates': duplicate_zip,  # 新增
            'failed': failed_zip,  # 新增
            'temp_files': temp_zip  # 新增：临时锁文件下载链接
        },
        'dedup_stats': {  # 更新去重统计
            'original_duplicates': len(duplicate_files),  # 新增
            'doc_duplicates': doc_duplicates,
            'para_exact_dup_total': para_exact_dup_total,
            'para_near_dup_total': para_near_dup_total,
            'noise_removed_total': noise_removed_total
        }
    })
    logger.info(f"[任务 {task_id}] 任务完成! 成功={successful_count}, 纯文本={len(pure_text_files)}, 富媒体={len(rich_media_files)}, 原始重复={len(duplicate_files)}, 处理失败={len(failed_files)}, 临时锁文件={len(temp_files)}")


@router.get("/batch/status/{task_id}", response_model=BatchStatusResponse)
async def get_batch_status(task_id: str):
    """查询批量任务状态"""
    logger.debug(f"查询任务状态: {task_id}")
    
    if task_id not in batch_tasks:
        logger.warning(f"任务不存在: {task_id}")
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = batch_tasks[task_id]
    logger.debug(f"任务 {task_id} 状态: {task['status']}, 进度: {task['completed']}/{task['total']}")
    
    return BatchStatusResponse(
        task_id=task_id,
        status=task['status'],
        progress=Progress(
            total=task['total'],
            completed=task['completed'],
            pure_text_count=task['pure_text_count'],
            rich_media_count=task['rich_media_count'],
            unique_pure_count=task.get('unique_pure_count', 0),  # 新增
            unique_rich_count=task.get('unique_rich_count', 0),   # 新增
            duplicate_count=task.get('duplicate_count', 0),  # 新增
            failed_count=task.get('failed_count', 0),  # 新增
            temp_file_count=task.get('temp_file_count', 0)  # 新增：临时锁文件计数
        ),
        pure_text_files=task.get('pure_text_files', []),
        rich_media_files=task.get('rich_media_files', []),
        downloads=Downloads(
            pure_text_converted=f"/api/v1/batch/download/pure-converted/{task_id}" if task.get('downloads', {}).get('pure_text_converted') else None,
            rich_media_original=f"/api/v1/batch/download/rich-original/{task_id}" if task.get('downloads', {}).get('rich_media_original') else None,
            all_files=f"/api/v1/batch/download/all/{task_id}" if task.get('downloads', {}).get('all_files') else None,
            unique_pure_text=f"/api/v1/batch/download/unique-pure/{task_id}" if task.get('downloads', {}).get('unique_pure_text') else None,
            unique_rich_media=f"/api/v1/batch/download/unique-rich/{task_id}" if task.get('downloads', {}).get('unique_rich_media') else None,
            duplicates=f"/api/v1/batch/download/duplicates/{task_id}" if task.get('downloads', {}).get('duplicates') else None,
            failed=f"/api/v1/batch/download/failed/{task_id}" if task.get('downloads', {}).get('failed') else None,
            temp_files=f"/api/v1/batch/download/temp-files/{task_id}" if task.get('downloads', {}).get('temp_files') else None
        ),
        dedup_stats=task.get('dedup_stats', {})  # 新增：返回去重统计
    )


@router.get("/batch/download/pure-converted/{task_id}")
async def download_pure_converted(task_id: str):
    """下载纯文字文档（转换后）"""
    logger.info(f"请求下载纯文本文档: {task_id}")
    
    if task_id not in batch_tasks:
        logger.warning(f"任务不存在: {task_id}")
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = batch_tasks[task_id]
    
    if 'downloads' not in task or not task['downloads'].get('pure_text_converted'):
        logger.warning(f"纯文本 ZIP 不存在: {task_id}")
        raise HTTPException(status_code=404, detail="文件不存在")
    
    zip_path = task['downloads']['pure_text_converted']
    
    if not Path(zip_path).exists():
        logger.error(f"ZIP 文件不存在: {zip_path}")
        raise HTTPException(status_code=404, detail="文件不存在")
    
    logger.info(f"返回纯文本 ZIP: {Path(zip_path).name}")
    
    return FileResponse(
        zip_path,
        media_type='application/zip',
        filename=Path(zip_path).name
    )


@router.get("/batch/download/rich-original/{task_id}")
async def download_rich_original(task_id: str):
    """下载富媒体文档（原文件）"""
    logger.info(f"请求下载富媒体文档: {task_id}")
    
    if task_id not in batch_tasks:
        logger.warning(f"任务不存在: {task_id}")
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = batch_tasks[task_id]
    
    if 'downloads' not in task or not task['downloads'].get('rich_media_original'):
        logger.warning(f"富媒体 ZIP 不存在: {task_id}")
        raise HTTPException(status_code=404, detail="文件不存在")
    
    zip_path = task['downloads']['rich_media_original']
    
    if not Path(zip_path).exists():
        logger.error(f"ZIP 文件不存在: {zip_path}")
        raise HTTPException(status_code=404, detail="文件不存在")
    
    logger.info(f"返回富媒体 ZIP: {Path(zip_path).name}")
    
    return FileResponse(
        zip_path,
        media_type='application/zip',
        filename=Path(zip_path).name
    )


@router.get("/batch/download/all/{task_id}")
async def download_all_files(task_id: str):
    """下载所有文件"""
    
    if task_id not in batch_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = batch_tasks[task_id]
    
    if 'downloads' not in task or not task['downloads'].get('all_files'):
        raise HTTPException(status_code=404, detail="文件不存在")
    
    zip_path = task['downloads']['all_files']
    
    if not Path(zip_path).exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileResponse(
        zip_path,
        media_type='application/zip',
        filename=Path(zip_path).name
    )


@router.get("/batch/download/unique-pure/{task_id}")
async def download_unique_pure_text(task_id: str):
    """下载纯文本独一份文档（去除完全相同文件）"""
    logger.info(f"请求下载纯文本独一份文档: {task_id}")
    
    if task_id not in batch_tasks:
        logger.warning(f"任务不存在: {task_id}")
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = batch_tasks[task_id]
    
    if 'downloads' not in task or not task['downloads'].get('unique_pure_text'):
        logger.warning(f"纯文本独一份 ZIP 不存在: {task_id}")
        raise HTTPException(status_code=404, detail="文件不存在")
    
    zip_path = task['downloads']['unique_pure_text']
    
    if not Path(zip_path).exists():
        logger.error(f"ZIP 文件不存在: {zip_path}")
        raise HTTPException(status_code=404, detail="文件不存在")
    
    logger.info(f"返回纯文本独一份 ZIP: {Path(zip_path).name}")
    
    return FileResponse(
        zip_path,
        media_type='application/zip',
        filename=Path(zip_path).name
    )


@router.get("/batch/download/unique-rich/{task_id}")
async def download_unique_rich_media(task_id: str):
    """下载富媒体独一份文档（去除完全相同文件）"""
    logger.info(f"请求下载富媒体独一份文档: {task_id}")
    
    if task_id not in batch_tasks:
        logger.warning(f"任务不存在: {task_id}")
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = batch_tasks[task_id]
    
    if 'downloads' not in task or not task['downloads'].get('unique_rich_media'):
        logger.warning(f"富媒体独一份 ZIP 不存在: {task_id}")
        raise HTTPException(status_code=404, detail="文件不存在")
    
    zip_path = task['downloads']['unique_rich_media']
    
    if not Path(zip_path).exists():
        logger.error(f"ZIP 文件不存在: {zip_path}")
        raise HTTPException(status_code=404, detail="文件不存在")
    
    logger.info(f"返回富媒体独一份 ZIP: {Path(zip_path).name}")
    
    return FileResponse(
        zip_path,
        media_type='application/zip',
        filename=Path(zip_path).name
    )


@router.get("/batch/download/duplicates/{task_id}")
async def download_duplicates(task_id: str):
    """下载原始重复文件"""
    logger.info(f"请求下载原始重复文件: {task_id}")
    
    if task_id not in batch_tasks:
        logger.warning(f"任务不存在: {task_id}")
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = batch_tasks[task_id]
    
    if 'downloads' not in task or not task['downloads'].get('duplicates'):
        logger.warning(f"原始重复文件 ZIP 不存在: {task_id}")
        raise HTTPException(status_code=404, detail="文件不存在")
    
    zip_path = task['downloads']['duplicates']
    
    if not Path(zip_path).exists():
        logger.error(f"ZIP 文件不存在: {zip_path}")
        raise HTTPException(status_code=404, detail="文件不存在")
    
    logger.info(f"返回原始重复文件 ZIP: {Path(zip_path).name}")
    
    return FileResponse(
        zip_path,
        media_type='application/zip',
        filename=Path(zip_path).name
    )


@router.get("/batch/download/failed/{task_id}")
async def download_failed(task_id: str):
    """下载处理失败的文件"""
    logger.info(f"请求下载处理失败的文件: {task_id}")
    
    if task_id not in batch_tasks:
        logger.warning(f"任务不存在: {task_id}")
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = batch_tasks[task_id]
    
    if 'downloads' not in task or not task['downloads'].get('failed'):
        logger.warning(f"处理失败文件 ZIP 不存在: {task_id}")
        raise HTTPException(status_code=404, detail="文件不存在")
    
    zip_path = task['downloads']['failed']
    
    if not Path(zip_path).exists():
        logger.error(f"ZIP 文件不存在: {zip_path}")
        raise HTTPException(status_code=404, detail="文件不存在")
    
    logger.info(f"返回处理失败文件 ZIP: {Path(zip_path).name}")
    
    return FileResponse(
        zip_path,
        media_type='application/zip',
        filename=Path(zip_path).name
    )


@router.get("/batch/download/temp-files/{task_id}")
async def download_temp_files(task_id: str):
    """下载临时锁文件"""
    logger.info(f"请求下载临时锁文件: {task_id}")
    
    if task_id not in batch_tasks:
        logger.warning(f"任务不存在: {task_id}")
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = batch_tasks[task_id]
    
    if 'downloads' not in task or not task['downloads'].get('temp_files'):
        logger.warning(f"临时锁文件 ZIP 不存在: {task_id}")
        raise HTTPException(status_code=404, detail="文件不存在")
    
    zip_path = task['downloads']['temp_files']
    
    if not Path(zip_path).exists():
        logger.error(f"ZIP 文件不存在: {zip_path}")
        raise HTTPException(status_code=404, detail="文件不存在")
    
    logger.info(f"返回临时锁文件 ZIP: {Path(zip_path).name}")
    
    return FileResponse(
        zip_path,
        media_type='application/zip',
        filename=Path(zip_path).name
    )


@router.get("/files/download/original/{file_name}")
async def download_original_file(file_name: str):
    """下载原始文件"""
    
    file_path = file_handler.original_dir / file_name
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileResponse(
        str(file_path),
        filename=file_name
    )


@router.get("/files/download/converted/{file_name}")
async def download_converted_file(file_name: str):
    """下载转换后的文件"""
    
    file_path = file_handler.converted_dir / file_name
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileResponse(
        str(file_path),
        filename=file_name
    )


@router.post("/storage/clean")
async def clean_storage(days: int = 7):
    """
    清理旧文件
    
    Args:
        days: 保留天数，默认 7 天
    
    Returns:
        清理统计信息
    """
    logger.info(f"手动清理请求: 保留最近 {days} 天的文件")
    
    try:
        result = cleaner.clean_all(days)
        return {
            "success": True,
            "message": f"清理完成，保留最近 {days} 天的文件",
            "data": result
        }
    except Exception as e:
        logger.error(f"清理失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"清理失败: {str(e)}")


@router.get("/storage/info")
async def get_storage_info():
    """
    获取存储使用情况
    
    Returns:
        存储统计信息
    """
    logger.debug("查询存储使用情况")
    
    try:
        info = cleaner.get_storage_info()
        return {
            "success": True,
            "data": info
        }
    except Exception as e:
        logger.error(f"获取存储信息失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取信息失败: {str(e)}")
