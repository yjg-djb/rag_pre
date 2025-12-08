import os
import uuid
from pathlib import Path
from typing import Dict
from fastapi import UploadFile


class FileHandler:
    """文件处理工具类"""
    
    def __init__(self, base_dir: str = "storage"):
        self.base_dir = Path(base_dir)
        self.original_dir = self.base_dir / "original"
        self.converted_dir = self.base_dir / "converted"
        self.batch_dir = self.base_dir / "batch"
        
        # 创建必要的目录
        self.original_dir.mkdir(parents=True, exist_ok=True)
        self.converted_dir.mkdir(parents=True, exist_ok=True)
        self.batch_dir.mkdir(parents=True, exist_ok=True)
    
    def parse_file_path(self, upload_file: UploadFile) -> Dict[str, str]:
        """
        从上传文件中提取路径信息
        filename 格式：finance/report.pdf 或 hr/docs/policy.docx
        
        修复:
        1. 使用 as_posix() 统一路径分隔符为正斜杠
        2. 正确处理空目录情况
        3. 处理 filename 可能为 None 的情况
        """
        filename: str = upload_file.filename if upload_file.filename else "unknown_file"
        path_obj = Path(filename)
        
        # 使用 as_posix() 统一转换为正斜杠路径（跨平台兼容）
        parent_posix = path_obj.parent.as_posix()
        directory = parent_posix if parent_posix != '.' else ''
        
        return {
            'full_path': path_obj.as_posix(),  # 统一使用正斜杠
            'directory': directory,
            'filename': path_obj.name,
            'stem': path_obj.stem,
            'extension': path_obj.suffix
        }
    
    async def save_upload_file(self, upload_file: UploadFile, save_dir: Path, 
                                keep_path: bool = False) -> str:
        """
        保存上传的文件
        keep_path: 是否保留原始路径结构
        """
        if keep_path:
            path_info = self.parse_file_path(upload_file)
            file_dir = save_dir / path_info['directory']
            file_dir.mkdir(parents=True, exist_ok=True)
            file_path = file_dir / path_info['filename']
        else:
            unique_name = f"{uuid.uuid4()}_{upload_file.filename}"
            file_path = save_dir / unique_name
        
        content = await upload_file.read()
        with open(file_path, 'wb') as f:
            f.write(content)
        
        return str(file_path)
    
    def get_batch_dir(self, task_id: str) -> Path:
        """获取批量任务的工作目录"""
        batch_task_dir = self.batch_dir / task_id
        batch_task_dir.mkdir(parents=True, exist_ok=True)
        return batch_task_dir
