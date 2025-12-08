# 文档检测与批量处理系统 - 离线部署包

##  包含内容

```
kb-jx/
 offline_packages/          # 离线依赖包 (32个包, ~51MB)
 install_offline.bat        # 离线安装脚本
 requirements.txt           # 依赖清单
 main.py                    # 主程序
 api/                       # API 接口
 services/                  # 业务服务
 models/                    # 数据模型
 utils/                     # 工具类
 static/                    # 静态文件
 README_OFFLINE.txt         # 本文档
```

##  部署步骤

### 1. 环境要求

- Windows 操作系统
- Python 3.10 或更高版本
- Microsoft Office (可选，支持 .doc/.xls/.ppt 格式需要)

### 2. 快速安装

**方法 A: 使用自动安装脚本 (推荐)**

直接双击运行：
```
install_offline.bat
```

**方法 B: 手动安装**

```bash
# 1. 升级 pip
python -m pip install --upgrade pip --no-index --find-links=offline_packages

# 2. 安装依赖
pip install --no-index --find-links=offline_packages -r requirements.txt

# 3. 验证安装
python -c "import fastapi; print(\"安装成功\")"
```

### 3. 启动服务

```bash
python main.py
```

服务启动后访问：
- 主页: http://localhost:8000
- 上传页面: http://localhost:8000/upload
- API 文档: http://localhost:8000/docs

##  功能说明

### 支持的文件格式

| 格式 | 说明 | 依赖 |
|-----|------|------|
| .txt | 纯文本 | 无 |
| .md | Markdown | 无 |
| .docx | Word 文档 (新格式) | 无 |
| .doc | Word 文档 (旧格式) | 需要 Microsoft Word |
| .xlsx | Excel 表格 (新格式) | 无 |
| .xls | Excel 表格 (旧格式) | 需要 Microsoft Excel |
| .pptx | PPT 演示 (新格式) | 无 |
| .ppt | PPT 演示 (旧格式) | 需要 Microsoft PowerPoint |
| .pdf | PDF 文档 | 无 |

### API 接口

1. **单文件分析**
   - POST /api/v1/document/analyze
   - 检测文档类型并转换为 DOCX

2. **批量上传**
   - POST /api/v1/documents/batch-upload
   - 支持多文件、多层级目录

3. **查询任务状态**
   - GET /api/v1/batch/status/{task_id}

4. **下载结果**
   - 纯文本转换包
   - 富媒体原文件包
   - 完整文件包

5. **存储管理**
   - POST /api/v1/storage/clean - 清理旧文件
   - GET /api/v1/storage/info - 查看存储使用情况

##  配置说明

### 端口修改

修改 main.py 最后几行：
```python
uvicorn.run(
    app,
    host="0.0.0.0",
    port=8000,  # 修改此处端口
    log_level="info"
)
```

### 存储目录

默认存储在 `storage/` 目录：
- storage/original/ - 原始文件
- storage/converted/ - 转换文件
- storage/batch/ - 批量任务

### 日志配置

日志存储在 `logs/` 目录：
- logs/app_YYYYMMDD.log - 完整日志
- logs/error_YYYYMMDD.log - 错误日志

### 清理策略

自动清理配置（main.py）：
```python
result = cleaner.clean_old_batch_tasks(days=7)  # 保留7天
```

##  使用示例

### cURL 示例

**单文件上传**:
```bash
curl -X POST "http://localhost:8000/api/v1/document/analyze" \
  -F "file=@document.docx"
```

**批量上传**:
```bash
curl -X POST "http://localhost:8000/api/v1/documents/batch-upload" \
  -F "files=@file1.doc" \
  -F "files=@folder/file2.xls" \
  -F "files=@folder/subfolder/file3.ppt"
```

### Python 示例

```python
import requests

# 单文件分析
with open(''test.docx'', ''rb'') as f:
    response = requests.post(
        ''http://localhost:8000/api/v1/document/analyze'',
        files={''file'': f}
    )
    print(response.json())

# 批量上传
files = [
    (''files'', (''doc1.docx'', open(''doc1.docx'', ''rb''))),
    (''files'', (''data/report.xlsx'', open(''report.xlsx'', ''rb'')))
]
response = requests.post(
    ''http://localhost:8000/api/v1/documents/batch-upload'',
    files=files
)
task_id = response.json()[''task_id'']
```

##  常见问题

### Q1: 提示 "未检测到 Python"
**A**: 请确保已安装 Python 3.10+ 并添加到系统 PATH

### Q2: 安装依赖失败
**A**: 确保 offline_packages 目录完整，或检查网络连接重新下载

### Q3: .doc/.xls/.ppt 文件提示不支持
**A**: 这些旧格式需要安装 Microsoft Office

### Q4: 端口 8000 被占用
**A**: 修改 main.py 中的端口号

### Q5: 服务启动后无法访问
**A**: 检查防火墙设置，允许端口访问

##  技术支持

系统版本: 1.0.0
Python 版本要求: 3.10+
依赖包数量: 32 个
离线包大小: ~51 MB

##  许可信息

依赖包许可：
- FastAPI: MIT
- Uvicorn: BSD
- python-docx: MIT
- openpyxl: MIT
- python-pptx: MIT
- PyMuPDF: AGPL
- pywin32: PSF

---
更新日期: 2025-11-11
