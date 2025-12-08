import zipfile
from pathlib import Path
from typing import List, Dict


class ZipperService:
    """ZIP 打包服务 - 保留目录结构"""
    
    def __init__(self):
        pass
    
    def create_structured_zip(self, files: List[Dict], file_type: str, 
                              task_id: str, output_dir: str) -> str:
        """
        创建保留目录结构的 ZIP 包
        file_type: 'converted' 或 'original'
        
        修复:
        1. 归一化 ZIP 归档路径，统一使用正斜杠
        2. 移除前导分隔符
        """
        zip_filename = f'{file_type}_{task_id}.zip'
        zip_path = Path(output_dir) / zip_filename
        
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for file_info in files:
                    source_file = ''  # 初始化变量
                    try:
                        if file_type == 'converted':
                            # 纯文字文档：使用转换后的路径
                            source_file = file_info.get('converted_file', '')
                            arcname = file_info.get('converted_path', '')
                        else:
                            # 富媒体文档：使用原始路径
                            source_file = file_info.get('original_file', '')
                            arcname = file_info.get('path', '')
                        
                        # 检查路径是否有效
                        if not source_file or not arcname:
                            print(f"警告: 文件信息不完整，跳过: {file_info}")
                            continue
                        
                        # 修复：归一化路径（Windows 路径转为正斜杠，移除前导分隔符）
                        arcname = arcname.replace('\\', '/')  # Windows 反斜杠转正斜杠
                        if arcname.startswith('/'):
                            arcname = arcname[1:]  # 移除前导斜杠
                        
                        # 添加文件到 ZIP
                        if Path(source_file).exists():
                            zf.write(source_file, arcname=arcname)
                        else:
                            print(f"警告: 文件不存在，跳过: {source_file}")
                    except Exception as e:
                        print(f"添加文件到 ZIP 失败: {source_file}, 错误: {e}")
                        continue
            
            return str(zip_path)
            
        except Exception as e:
            print(f"创建 ZIP 文件失败: {e}")
            # 清理部分创建的 ZIP 文件
            if zip_path.exists():
                try:
                    zip_path.unlink()
                except:
                    pass
            raise
    
    def create_combined_zip(self, pure_files: List[Dict], rich_files: List[Dict],
                           task_id: str, output_dir: str) -> str:
        """
        创建包含所有文件的综合 ZIP 包
        
        修复:
        1. 归一化 ZIP 归档路径，统一使用正斜杠
        2. 移除前导分隔符
        """
        zip_filename = f'all_{task_id}.zip'
        zip_path = Path(output_dir) / zip_filename
        
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                # 添加纯文字文档（转换后）
                for file_info in pure_files:
                    source_file = ''  # 初始化变量
                    try:
                        source_file = file_info.get('converted_file', '')
                        arcname = file_info.get('converted_path', '')
                        
                        if not source_file or not arcname:
                            print(f"警告: 纯文本文件信息不完整，跳过: {file_info}")
                            continue
                        
                        # 修复：归一化路径
                        arcname = arcname.replace('\\', '/')  # Windows 反斜杠转正斜杠
                        if arcname.startswith('/'):
                            arcname = arcname[1:]  # 移除前导斜杠
                        
                        if Path(source_file).exists():
                            zf.write(source_file, arcname=arcname)
                        else:
                            print(f"警告: 文件不存在，跳过: {source_file}")
                    except Exception as e:
                        print(f"添加纯文本文件失败: {source_file}, 错误: {e}")
                        continue
                
                # 添加富媒体文档（原文件）
                for file_info in rich_files:
                    source_file = ''  # 初始化变量
                    try:
                        source_file = file_info.get('original_file', '')
                        arcname = file_info.get('path', '')
                        
                        if not source_file or not arcname:
                            print(f"警告: 富媒体文件信息不完整，跳过: {file_info}")
                            continue
                        
                        # 修复：归一化路径
                        arcname = arcname.replace('\\', '/')  # Windows 反斜杠转正斜杠
                        if arcname.startswith('/'):
                            arcname = arcname[1:]  # 移除前导斜杠
                        
                        if Path(source_file).exists():
                            zf.write(source_file, arcname=arcname)
                        else:
                            print(f"警告: 文件不存在，跳过: {source_file}")
                    except Exception as e:
                        print(f"添加富媒体文件失败: {source_file}, 错误: {e}")
                        continue
            
            return str(zip_path)
            
        except Exception as e:
            print(f"创建综合 ZIP 文件失败: {e}")
            # 清理部分创建的 ZIP 文件
            if zip_path.exists():
                try:
                    zip_path.unlink()
                except:
                    pass
            raise
