# RAG-Preprocess 文档预处理工具

<p align="center">
  <b>专为 RAG 和向量数据库设计的文档预处理解决方案</b>
</p>

---

## 项目简介

**RAG-Preprocess** 是一个一站式文档预处理工具链，专门用于将各种格式的企业文档智能转换为高质量的纯文本格式，为大语言模型（LLM）和向量数据库提供优质的知识库输入。

### 解决什么问题？

在构建企业知识库时，我们常常面临以下挑战：

| 挑战 | 本项目的解决方案 |
|------|-----------------|
| 文档格式繁多（PDF/Word/Excel/PPT） | 统一解析引擎，支持 6+ 种主流格式 |
| 图片中的文字无法被检索 | 集成 OCR + LLM 优化，精准提取图片文字 |
| 表格数据结构丢失 | 智能保留表格语义关系，支持复杂合并单元格 |
| 重复内容影响检索质量 | 多级去重策略（文档级 + 段落级 + 近重复检测） |
| 批量处理效率低下 | 异步并发处理，支持目录结构保留的批量转换 |

## 核心功能

### 1. 多格式文档解析

```
支持格式：
├── PDF     → 文本提取 + 表格识别 + 图片OCR
├── DOCX    → 段落 + 表格 + 嵌入图片解析
├── DOC     → 自动转换为DOCX后处理
├── XLSX    → 多Sheet支持 + 合并单元格智能填充
├── XLS     → 自动转换为XLSX后处理
├── PPTX    → 幻灯片文本与表格提取
├── PPT     → 自动转换为PPTX后处理
└── TXT/MD  → 直接处理，保留Markdown结构
```

### 2. 智能 OCR 处理

- **多引擎支持**：PaddleOCR（本地免费）、百度云、阿里云
- **LLM 优化**：自动修正 OCR 识别错误
- **图片增强**：对比度优化，提升识别准确率

### 3. 文本清洗管线

```python
原始文本 → Unicode规范化 → 噪声过滤 → 段落拆分 → 去重处理 → 输出
                ↓              ↓            ↓           ↓
              ftfy          URL/邮箱      智能分段    SHA256精确去重
                            电话/页码                 SimHash近重复
```

### 4. RESTful API 服务

- FastAPI 构建，自动生成交互式 API 文档
- 异步批量处理，支持 5 并发任务
- 分类打包下载（纯文本 / 富媒体 / 全部）

## 快速开始

### 环境要求

- Python 3.8+
- Windows / Linux / macOS

### 安装步骤

```bash
# 1. 克隆仓库
git clone https://github.com/your-org/rag-preprocess.git
cd rag-preprocess

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 3. 安装依赖
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 启动服务

```bash
# 方式1：一键启动（Windows）
双击 start.bat

# 方式2：命令行
python main.py

# 方式3：开发模式
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 访问地址

启动成功后：

| 地址 | 说明 |
|------|-----|
| http://localhost:8000/upload | Web 上传界面 |
| http://localhost:8000/docs | Swagger API 文档 |
| http://localhost:8000/redoc | ReDoc API 文档 |

## 项目结构

```
rag-preprocess/
│
├── main.py                 # 应用入口
├── config.py               # 配置管理
├── requirements.txt        # 依赖列表
│
├── api/v1/                 # API 接口层
│   └── endpoints.py        # RESTful 端点实现
│
├── services/               # 业务逻辑层
│   ├── detector.py         # 文档类型检测（纯文本/富媒体）
│   ├── converter.py        # 格式转换服务
│   ├── text_pipeline.py    # 文本清洗与去重管线
│   └── zipper.py           # ZIP 打包服务
│
├── parsers/                # 文档解析引擎
│   ├── doc_parser/         # Word 文档解析器
│   ├── pdf_parser/         # PDF 解析器
│   └── xlsx_parser/        # Excel 解析器
│
├── utils/                  # 工具类
│   ├── file_handler.py     # 文件操作
│   ├── logger.py           # 日志管理
│   └── dedup_store.py      # 去重存储
│
└── storage/                # 运行时存储（自动创建）
```

## API 使用示例

### 1. 单文件上传分析

```bash
curl -X POST "http://localhost:8000/api/v1/document/analyze" \
  -F "file=@报告.pdf"
```

**响应**：
```json
{
  "is_pure_text": true,
  "original_file": {
    "name": "报告.pdf",
    "download_url": "/api/v1/files/download/original/abc123.pdf"
  },
  "converted_file": {
    "name": "报告.docx",
    "download_url": "/api/v1/files/download/converted/abc123.docx"
  }
}
```

### 2. 批量上传（保留目录结构）

```bash
curl -X POST "http://localhost:8000/api/v1/documents/batch-upload" \
  -F "files=@报告.pdf;filename=财务/2024/年度报告.pdf" \
  -F "files=@制度.docx;filename=人事/员工手册.docx"
```

### 3. 查询处理状态

```bash
curl "http://localhost:8000/api/v1/batch/status/batch_20241230_123456"
```

### 4. 下载处理结果

```bash
# 下载纯文本转换包
curl "http://localhost:8000/api/v1/batch/download/pure-converted/{task_id}" -o pure.zip

# 下载所有文件包
curl "http://localhost:8000/api/v1/batch/download/all/{task_id}" -o all.zip
```

## 配置说明

### 环境变量配置

创建 `.env` 文件：

```env
# 应用配置
APP_HOST=0.0.0.0
APP_PORT=8000
APP_DEBUG=false

# 存储配置
STORAGE_BASE_DIR=./storage
STORAGE_CLEAN_KEEP_DAYS=7

# OCR 配置
OCR_PROVIDER=paddleocr      # paddleocr / baidu / aliyun
OCR_API_KEY=your_api_key

# LLM 配置（用于 OCR 结果优化）
LLM_API_URL=https://api.openai.com/v1
LLM_API_KEY=your_api_key
LLM_MODEL=gpt-4o-mini
```

## 技术栈

| 组件 | 技术选型 | 用途 |
|-----|---------|-----|
| Web 框架 | FastAPI | 高性能异步 API 服务 |
| Word 处理 | python-docx | DOCX 文档解析与生成 |
| Excel 处理 | openpyxl | XLSX 表格处理 |
| PPT 处理 | python-pptx | PPTX 演示文稿处理 |
| PDF 处理 | PyMuPDF | PDF 文本与图片提取 |
| 表格提取 | Camelot | PDF 表格识别 |
| OCR | PaddleOCR | 图片文字识别 |
| 去重 | SimHash | 近重复内容检测 |

## 常见问题

### Q: 扫描版 PDF 如何处理？

扫描版 PDF 会自动通过 OCR 处理。建议：
1. 确保 OCR 服务已正确配置
2. 扫描件清晰度影响识别效果
3. 启用 LLM 优化可显著提升准确率

### Q: 处理速度慢怎么办？

1. 检查是否有大量图片需要 OCR
2. 调整并发数配置（默认 5）
3. 考虑使用本地 OCR 服务减少网络延迟

### Q: 如何扩展支持新格式？

1. 在 `parsers/` 创建新的解析器模块
2. 实现标准解析接口
3. 在 `services/detector.py` 添加格式检测
4. 在 `services/converter.py` 添加转换逻辑

## 性能指标

| 文档类型 | 单文件处理速度（参考） |
|---------|---------------------|
| TXT/MD | < 1秒 |
| DOCX（无图片） | 1-3秒 |
| DOCX（有图片OCR） | 5-30秒（取决于图片数量） |
| XLSX | 2-10秒（取决于数据量） |
| PDF（文本型） | 2-5秒 |
| PDF（扫描型） | 10-60秒（取决于页数） |

## 开源协议

本项目采用 [MIT License](LICENSE) 开源协议。

## 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送分支 (`git push origin feature/amazing-feature`)
5. 提交 Pull Request

---

<p align="center">
  <b>如果这个项目对你有帮助，请给个 Star ⭐️</b>
</p>
