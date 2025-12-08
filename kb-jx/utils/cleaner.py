import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict
from utils.logger import get_logger

logger = get_logger("cleaner")


class StorageCleaner:
    """存储清理工具类"""
    
    def __init__(self, base_dir: str = "storage"):
        self.base_dir = Path(base_dir)
        self.batch_dir = self.base_dir / "batch"
        self.original_dir = self.base_dir / "original"
        self.converted_dir = self.base_dir / "converted"
    
    def clean_old_batch_tasks(self, days: int = 7) -> Dict:
        """
        清理指定天数之前的批量任务目录
        
        Args:
            days: 保留天数，默认 7 天
        
        Returns:
            清理统计信息
        """
        logger.info(f"开始清理 {days} 天前的批量任务...")
        
        if not self.batch_dir.exists():
            logger.warning(f"批量任务目录不存在: {self.batch_dir}")
            return {'deleted': 0, 'total_size': 0, 'total_size_mb': 0, 'errors': 0}
        
        cutoff_time = datetime.now() - timedelta(days=days)
        deleted_count = 0
        total_size = 0
        error_count = 0
        
        for task_dir in self.batch_dir.iterdir():
            if not task_dir.is_dir():
                continue
            
            try:
                # 获取目录修改时间
                dir_mtime = datetime.fromtimestamp(task_dir.stat().st_mtime)
                
                if dir_mtime < cutoff_time:
                    # 计算目录大小
                    dir_size = sum(f.stat().st_size for f in task_dir.rglob('*') if f.is_file())
                    
                    # 删除目录
                    shutil.rmtree(task_dir)
                    deleted_count += 1
                    total_size += dir_size
                    
                    logger.info(f"已删除任务目录: {task_dir.name} ({self._format_size(dir_size)})")
            
            except Exception as e:
                error_count += 1
                logger.error(f"删除任务目录失败: {task_dir.name}, 错误: {e}")
        
        result = {
            'deleted': deleted_count,
            'total_size': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'errors': error_count
        }
        
        logger.info(f"清理完成: 删除 {deleted_count} 个任务目录, 释放 {self._format_size(total_size)} 空间")
        return result
    
    def clean_old_single_files(self, days: int = 7) -> Dict:
        """
        清理单文件上传的旧文件
        
        Args:
            days: 保留天数，默认 7 天
        
        Returns:
            清理统计信息
        """
        logger.info(f"开始清理 {days} 天前的单文件...")
        
        cutoff_time = datetime.now() - timedelta(days=days)
        deleted_count = 0
        total_size = 0
        error_count = 0
        
        # 清理原始文件
        if self.original_dir.exists():
            count, size, errors = self._clean_directory(self.original_dir, cutoff_time)
            deleted_count += count
            total_size += size
            error_count += errors
        
        # 清理转换文件
        if self.converted_dir.exists():
            count, size, errors = self._clean_directory(self.converted_dir, cutoff_time)
            deleted_count += count
            total_size += size
            error_count += errors
        
        result = {
            'deleted': deleted_count,
            'total_size': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'errors': error_count
        }
        
        logger.info(f"单文件清理完成: 删除 {deleted_count} 个文件, 释放 {self._format_size(total_size)} 空间")
        return result
    
    def clean_all(self, days: int = 7) -> Dict:
        """
        清理所有旧文件
        
        Args:
            days: 保留天数，默认 7 天
        
        Returns:
            清理统计信息
        """
        logger.info(f"=== 开始完整清理 (保留最近 {days} 天) ===")
        
        batch_result = self.clean_old_batch_tasks(days)
        single_result = self.clean_old_single_files(days)
        
        total_result = {
            'batch_tasks': batch_result,
            'single_files': single_result,
            'total_deleted': batch_result['deleted'] + single_result['deleted'],
            'total_size': batch_result['total_size'] + single_result['total_size'],
            'total_size_mb': round((batch_result['total_size'] + single_result['total_size']) / (1024 * 1024), 2),
            'total_errors': batch_result['errors'] + single_result['errors']
        }
        
        logger.info(f"=== 清理完成 ===")
        logger.info(f"总删除数: {total_result['total_deleted']} 项")
        logger.info(f"释放空间: {self._format_size(total_result['total_size'])}")
        
        return total_result
    
    def get_storage_info(self) -> Dict:
        """
        获取存储使用情况
        
        Returns:
            存储统计信息
        """
        info = {
            'batch_tasks': self._get_dir_info(self.batch_dir),
            'original_files': self._get_dir_info(self.original_dir),
            'converted_files': self._get_dir_info(self.converted_dir),
        }
        
        total_size = sum(d['size'] for d in info.values())
        total_count = sum(d['count'] for d in info.values())
        
        info['total'] = {
            'size': total_size,
            'size_mb': round(total_size / (1024 * 1024), 2),
            'size_formatted': self._format_size(total_size),
            'count': total_count
        }
        
        return info
    
    def _clean_directory(self, directory: Path, cutoff_time: datetime) -> tuple:
        """清理目录中的旧文件"""
        deleted_count = 0
        total_size = 0
        error_count = 0
        
        for file_path in directory.rglob('*'):
            if not file_path.is_file():
                continue
            
            try:
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                
                if file_mtime < cutoff_time:
                    file_size = file_path.stat().st_size
                    file_path.unlink()
                    deleted_count += 1
                    total_size += file_size
                    logger.debug(f"已删除文件: {file_path}")
            
            except Exception as e:
                error_count += 1
                logger.error(f"删除文件失败: {file_path}, 错误: {e}")
        
        return deleted_count, total_size, error_count
    
    def _get_dir_info(self, directory: Path) -> Dict:
        """获取目录信息"""
        if not directory.exists():
            return {'size': 0, 'size_mb': 0, 'count': 0}
        
        files = list(directory.rglob('*'))
        total_size = sum(f.stat().st_size for f in files if f.is_file())
        file_count = sum(1 for f in files if f.is_file())
        
        return {
            'size': total_size,
            'size_mb': round(total_size / (1024 * 1024), 2),
            'size_formatted': self._format_size(total_size),
            'count': file_count
        }
    
    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """格式化文件大小"""
        size = float(size_bytes)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"
