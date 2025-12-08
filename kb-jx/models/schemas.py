from pydantic import BaseModel
from typing import List, Optional, Dict


class FileInfo(BaseModel):
    """文件信息"""
    name: str
    path: str
    download_url: str


class AnalyzeResponse(BaseModel):
    """单文件分析响应"""
    is_pure_text: bool
    original_file: FileInfo
    converted_file: Optional[FileInfo] = None
    message: Optional[str] = None  # 新增：提示信息（如去重命中）


class BatchUploadResponse(BaseModel):
    """批量上传响应"""
    task_id: str
    total_files: int
    status_url: str


class FilePathInfo(BaseModel):
    """文件路径信息"""
    original_path: str
    converted_path: Optional[str] = None
    reason: Optional[str] = None


class Progress(BaseModel):
    """进度信息"""
    total: int
    completed: int
    pure_text_count: int
    rich_media_count: int
    unique_pure_count: int = 0  # 新增：独一份纯文本数量
    unique_rich_count: int = 0  # 新增：独一份富媒体数量
    duplicate_count: int = 0  # 新增：原始重复文件数量
    failed_count: int = 0  # 新增：处理失败文件数量
    temp_file_count: int = 0  # 新增：临时锁文件数量


class Downloads(BaseModel):
    """下载链接"""
    pure_text_converted: Optional[str] = None
    rich_media_original: Optional[str] = None
    all_files: Optional[str] = None
    unique_pure_text: Optional[str] = None  # 新增：纯文本独一份下载链接
    unique_rich_media: Optional[str] = None  # 新增：富媒体独一份下载链接
    duplicates: Optional[str] = None  # 新增：原始重复文件下载链接
    failed: Optional[str] = None  # 新增：处理失败文件下载链接
    temp_files: Optional[str] = None  # 新增：临时锁文件下载链接


class BatchStatusResponse(BaseModel):
    """批量任务状态响应"""
    task_id: str
    status: str
    progress: Progress
    pure_text_files: List[Dict[str, str]]
    rich_media_files: List[Dict[str, str]]
    downloads: Downloads
    dedup_stats: Optional[Dict[str, int]] = None  # 新增：去重统计
