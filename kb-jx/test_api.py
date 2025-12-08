import requests
import os
from pathlib import Path


def test_server():
    """测试服务器是否运行"""
    base_url = "http://localhost:8000"
    
    print("=" * 60)
    print("文档检测系统 - API 测试")
    print("=" * 60)
    
    # 1. 测试健康检查
    print("\n1. 测试健康检查...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✓ 服务运行正常")
            print(f"  响应: {response.json()}")
        else:
            print(f"✗ 服务异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ 无法连接到服务: {e}")
        print("  请先运行 'python main.py' 启动服务")
        return False
    
    # 2. 测试根路径
    print("\n2. 测试根路径...")
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("✓ 根路径访问成功")
            data = response.json()
            print(f"  系统: {data['message']}")
            print(f"  版本: {data['version']}")
        else:
            print(f"✗ 访问失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 错误: {e}")
    
    # 3. 创建测试文件
    print("\n3. 创建测试文件...")
    test_dir = Path("test_files")
    test_dir.mkdir(exist_ok=True)
    
    # 创建纯文本文件
    txt_file = test_dir / "test.txt"
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write("这是一个测试文件\n\n包含纯文本内容。\n没有图片或图表。")
    print(f"✓ 创建测试文件: {txt_file}")
    
    # 4. 测试单文件上传
    print("\n4. 测试单文件上传...")
    try:
        with open(txt_file, 'rb') as f:
            files = {'file': (txt_file.name, f, 'text/plain')}
            response = requests.post(f"{base_url}/api/v1/document/analyze", files=files)
        
        if response.status_code == 200:
            print("✓ 文件上传成功")
            data = response.json()
            print(f"  是否纯文本: {data['is_pure_text']}")
            print(f"  原始文件: {data['original_file']['name']}")
            if data.get('converted_file'):
                print(f"  转换文件: {data['converted_file']['name']}")
                print(f"  下载链接: {base_url}{data['converted_file']['download_url']}")
        else:
            print(f"✗ 上传失败: {response.status_code}")
            print(f"  响应: {response.text}")
    except Exception as e:
        print(f"✗ 错误: {e}")
    
    # 5. 测试批量上传
    print("\n5. 测试批量上传...")
    
    # 创建更多测试文件
    md_file = test_dir / "readme.md"
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write("# 测试文档\n\n这是一个 Markdown 文档。\n\n## 章节 1\n\n纯文本内容。")
    
    try:
        files = [
            ('files', (txt_file.name, open(txt_file, 'rb'), 'text/plain')),
            ('files', (f"docs/{md_file.name}", open(md_file, 'rb'), 'text/markdown'))
        ]
        
        response = requests.post(f"{base_url}/api/v1/documents/batch-upload", files=files)
        
        # 关闭文件
        for _, (_, file_obj, _) in files:
            file_obj.close()
        
        if response.status_code == 200:
            print("✓ 批量上传成功")
            data = response.json()
            task_id = data['task_id']
            print(f"  任务 ID: {task_id}")
            print(f"  文件总数: {data['total_files']}")
            print(f"  状态查询: {base_url}{data['status_url']}")
            
            # 6. 查询任务状态
            print("\n6. 查询任务状态...")
            import time
            time.sleep(2)  # 等待处理
            
            status_response = requests.get(f"{base_url}/api/v1/batch/status/{task_id}")
            if status_response.status_code == 200:
                status_data = status_response.json()
                print("✓ 任务状态查询成功")
                print(f"  状态: {status_data['status']}")
                print(f"  进度: {status_data['progress']['completed']}/{status_data['progress']['total']}")
                print(f"  纯文本文档: {status_data['progress']['pure_text_count']}")
                print(f"  富媒体文档: {status_data['progress']['rich_media_count']}")
                
                if status_data.get('pure_text_files'):
                    print("\n  纯文本文件列表:")
                    for file in status_data['pure_text_files']:
                        print(f"    - {file['original_path']} -> {file['converted_path']}")
                
                print("\n  下载链接:")
                print(f"    纯文本转换: {base_url}{status_data['downloads']['pure_text_converted']}")
                print(f"    富媒体原文件: {base_url}{status_data['downloads']['rich_media_original']}")
                print(f"    所有文件: {base_url}{status_data['downloads']['all_files']}")
            else:
                print(f"✗ 状态查询失败: {status_response.status_code}")
        else:
            print(f"✗ 批量上传失败: {response.status_code}")
            print(f"  响应: {response.text}")
    except Exception as e:
        print(f"✗ 错误: {e}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
    print("\n提示:")
    print("  1. 访问 http://localhost:8000/docs 查看完整 API 文档")
    print("  2. 使用 Postman 或 curl 进行更多测试")
    print("  3. 检查 storage/ 目录查看生成的文件")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    test_server()
