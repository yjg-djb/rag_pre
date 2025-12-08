# 文档检测与批量处理系统

## 功能说明

本系统实现了文档纯文本检测与批量处理功能：

1. **单文件分析**：上传单个文件，检测是否为纯文本，并自动转换为 DOCX
2. **批量上传**：支持批量上传文件，保留目录结构
3. **智能检测**：检测文档中的图片、图表等富媒体内容
4. **格式转换**：将纯文本文档统一转换为 DOCX 格式
5. **分类下载**：提供纯文本、富媒体、全部文件三种下载方式

## 支持格式

- 文本：`.txt`, `.md`
- Office：`.docx`, `.xlsx`, `.pptx`
- PDF：`.pdf`

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动服务

```bash
python main.py
```

服务将在 `http://localhost:8000` 启动

### 3. 访问 API 文档

浏览器打开：`http://localhost:8000/docs`

## API 使用示例

### 单文件上传

```bash
curl -X POST "http://localhost:8000/api/v1/document/analyze" \
  -F "file=@document.pdf"
```

### 批量上传（保留目录结构）

```bash
curl -X POST "http://localhost:8000/api/v1/documents/batch-upload" \
  -F "files=@finance/report.pdf;filename=finance/report.pdf" \
  -F "files=@hr/policy.docx;filename=hr/policy.docx" \
  -F "files=@readme.txt;filename=readme.txt"
```

### 查询任务状态

```bash
curl "http://localhost:8000/api/v1/batch/status/{task_id}"
```

### 下载文件

```bash
# 下载纯文字转换后的文件
curl "http://localhost:8000/api/v1/batch/download/pure-converted/{task_id}" -o pure.zip

# 下载富媒体原文件
curl "http://localhost:8000/api/v1/batch/download/rich-original/{task_id}" -o rich.zip

# 下载所有文件
curl "http://localhost:8000/api/v1/batch/download/all/{task_id}" -o all.zip
```

## 项目结构

```
kb-jx/
├── main.py                 # FastAPI 主程序
├── requirements.txt        # 依赖
├── api/
│   └── v1/
│       └── endpoints.py    # API 端点
├── services/
│   ├── detector.py         # 文档检测服务
│   ├── converter.py        # 格式转换服务
│   └── zipper.py          # ZIP 打包服务
├── models/
│   └── schemas.py         # 数据模型
├── utils/
│   └── file_handler.py    # 文件处理工具
└── storage/               # 存储目录（自动创建）
    ├── original/          # 原始文件
    ├── converted/         # 转换后文件
    └── batch/             # 批量任务文件
```

## 注意事项

1. 上传批量文件时，可在 `filename` 参数中指定相对路径来保留目录结构
2. 系统会自动创建 `storage` 目录用于存储文件
3. 批量处理支持最大 5 个并发任务
4. 任务完成后可通过 API 下载 ZIP 包，包含完整目录结构

## 测试建议

1. 准备测试文件（包含纯文本和富媒体文档）
2. 使用 Postman 或 curl 测试 API
3. 访问 `/docs` 查看交互式 API 文档
4. 检查下载的 ZIP 包是否保留了目录结构
