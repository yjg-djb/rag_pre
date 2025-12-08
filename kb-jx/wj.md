# 知识库文档内容纯度检测工具需求文档

## 1. 项目背景
- **行业场景**：金融行业知识库文档分类管理系统
- **核心痛点**：大量文档需要按内容纯度（纯文本 vs 富媒体）进行分类，便于后续知识提取与向量化处理
- **应用价值**：自动识别仅包含文字内容的纯文档（不含图片、图表等富媒体元素）与包含富媒体的复合文档，与文件格式无关

## 2. 功能目标
接收单个文件上传，检测文档内容是否为纯文本（仅包含文字），区分：
- **纯文档**：仅包含文字内容，不含图片、图表、嵌入对象等富媒体元素
- **富媒体文档**：包含图片、图表、表格、嵌入对象等非纯文本元素

**与格式无关性**：无论是 .docx、.pptx、.pdf 还是 .txt，只要内容纯粹是文字即为纯文档。

## 3. 支持的文件格式

**所有格式统一处理**，通过内容解析判断是否为纯文档：

### 3.1 文本类格式
- `.txt` - 纯文本文件（默认为纯文档，除非检测到特殊字符或二进制内容）
- `.md` - Markdown 文档（检查是否包含图片引用）

### 3.2 Office 文档类格式
- `.doc` - Word 文档（需要先转为docx格式，再检查是否包含图片、图表、形状、嵌入对象）
- `.docx` - Word 文档（检查是否包含图片、图表、形状、嵌入对象）
- `.xlsx` - Excel 表格（检查是否包含图表、图片、嵌入对象）
- `.pptx` - PowerPoint 演示文稿（检查是否包含图片、图表、形状、SmartArt）
- `.xls` - Excel 表格（需要先转为xlsx格式，再检查是否包含图片、图表、形状、嵌入对象）
- `.ppt` - PowerPoint 演示文稿（需要先转为pptx格式，再检查是否包含图片、图表、形状、SmartArt）

### 3.3 便携文档格式
- `.pdf` - PDF 文档（检查是否包含图片、矢量图形、表单元素）

### 3.4 解析库依赖
- **python-docx**: Word (.docx) 文档解析，检测 `document.inline_shapes`、`document.part.rels`
- **openpyxl**: Excel (.xlsx) 文档解析，检测 `sheet._images`、`sheet._charts`
- **python-pptx**: PowerPoint (.pptx) 文档解析，检测 `slide.shapes` 中的图片和图表
- **pdfplumber** 或 **PyMuPDF (fitz)**: PDF 文档解析，检测 `page.get_images()`

## 4. 功能实现方案

### 4.1 输入参数（文件上传模式）
- **file** (UploadFile): FastAPI 文件上传对象，支持多种格式
- **file_name** (str): 原始文件名（可选，用于记录）
- **extract_full_content** (bool): 是否提取完整文本内容，默认 `True`
- **max_content_length** (int): 文本内容最大提取长度（字符数），默认 `50000`，0 表示不限制
- **encoding** (str): 纯文本文件的默认编码，默认 `"utf-8"`，备选 `"gbk"`

### 4.2 输出结果

返回 JSON 格式数据结构：

**纯文档示例**：
```json
{
  "is_pure_text": true,
  "file_info": {
    "file_name": "financial_report.docx",
    "file_type": "docx",
    "file_size": 45120,
    "detected_at": "2025-11-10T10:30:00"
  },
  "content_analysis": {
    "has_images": false,
    "has_charts": false,
    "has_tables": true,
    "has_embedded_objects": false,
    "image_count": 0,
    "chart_count": 0,
    "table_count": 3,
    "total_characters": 15823,
    "total_words": 5240,
    "total_paragraphs": 68
  },
  "text_content": "第一章 金融市场概述\n\n1.1 金融市场定义\n金融市场是指资金供求双方通过金融工具进行交易的场所...（完整文本内容）",
  "metadata": {
    "encoding": "utf-8",
    "author": "张三",
    "created_date": "2025-01-15T09:00:00",
    "modified_date": "2025-01-20T16:30:00",
    "pages": 12
  },
  "rich_media_details": null
}
```

**富媒体文档示例**：
```json
{
  "is_pure_text": false,
  "file_info": {
    "file_name": "product_presentation.pptx",
    "file_type": "pptx",
    "file_size": 2048576,
    "detected_at": "2025-11-10T10:35:00"
  },
  "content_analysis": {
    "has_images": true,
    "has_charts": true,
    "has_tables": false,
    "has_embedded_objects": false,
    "image_count": 15,
    "chart_count": 3,
    "table_count": 0,
    "total_characters": 3280,
    "total_words": 850,
    "total_paragraphs": 45
  },
  "text_content": "产品介绍\n\n核心功能\n- 智能推荐\n- 数据分析\n- 风险控制...（提取的文字部分）",
  "metadata": {
    "author": "李四",
    "created_date": "2025-02-01T14:00:00",
    "slides": 18
  },
  "rich_media_details": {
    "images": [
      {
        "location": "slide_1",
        "type": "png",
        "size": 125648,
        "description": "公司 Logo"
      },
      {
        "location": "slide_5",
        "type": "jpeg",
        "size": 458920,
        "description": "产品架构图"
      }
    ],
    "charts": [
      {
        "location": "slide_8",
        "chart_type": "柱状图",
        "title": "月度销售数据"
      }
    ]
  }
}
```

## 5. 技术实现栈

### 5.1 核心框架
- **FastAPI**: RESTful API 框架，提供文件上传接口
- **Pydantic**: 数据模型验证与序列化
- **python-multipart**: FastAPI 文件上传依赖

### 5.2 文档解析库
- **python-docx**: Word (.docx) 文档解析，检测富媒体元素
  - `document.inline_shapes` - 检测内联图片
  - `document.part.rels` - 检测嵌入对象
- **openpyxl**: Excel (.xlsx) 文档解析
  - `sheet._images` - 检测图片
  - `sheet._charts` - 检测图表
- **python-pptx**: PowerPoint (.pptx) 文档解析
  - `slide.shapes` - 遍历所有形状
  - `shape.shape_type` - 判断类型（图片/图表/文本框）
- **PyMuPDF (fitz)** 或 **pdfplumber**: PDF 文档解析
  - `page.get_images()` - 提取图片列表
  - `page.get_text()` - 提取纯文本
- **chardet**: 自动检测文本文件编码

### 5.3 辅助工具
- **io.BytesIO**: 内存文件流处理（无需落盘）
- **pathlib**: 文件路径与扩展名处理
- **magic** 或 **filetype**: 文件类型检测（可选，验证 MIME 类型）

## 6. 输出说明

### 6.1 POST /api/v1/document/analyze
**功能**: 上传单个文件并分析内容纯度

**请求方式**: `multipart/form-data`

**请求参数**:
- `file` (File): 上传的文件（必填）
- `extract_full_content` (bool): 是否提取完整内容，默认 `true`
- `max_content_length` (int): 最大内容长度，默认 `50000`

**cURL 示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/document/analyze" \
  -F "file=@/path/to/document.docx" \
  -F "extract_full_content=true" \
  -F "max_content_length=50000"
```

**响应体**: 见 4.2 输出结果

**HTTP 状态码**:
- `200 OK`: 分析成功
- `400 Bad Request`: 文件格式不支持或参数错误
- `413 Payload Too Large`: 文件大小超过限制（默认 50MB）
- `500 Internal Server Error`: 解析失败或服务器错误

## 7. 关键技术点

### 7.1 文档纯度检测流程
```python
1. 接收文件上传（FastAPI UploadFile）
2. 读取文件到内存（BytesIO）
3. 根据文件扩展名选择解析器：
   ├─ .txt / .md → 直接读取，检查是否包含图片引用（如 ![image](url)）
   ├─ .docx → python-docx 检测 inline_shapes、images、charts
   ├─ .xlsx → openpyxl 检测 _images、_charts
   ├─ .pptx → python-pptx 遍历 shapes，统计图片/图表
   └─ .pdf → PyMuPDF 调用 get_images() 检测图片
4. 提取文本内容（所有格式统一提取）
5. 统计富媒体元素数量与类型
6. 判定 is_pure_text = (image_count == 0 and chart_count == 0)
7. 构造响应 JSON
```

### 7.2 ZIP 打包下载

```python
import zipfile
import io

def create_batch_zip(converted_files: List[dict], task_id: str):
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_info in converted_files:
            if file_info['is_pure_text']:
                file_path = file_info['converted_file_path']
                arcname = file_info['converted_file_name']
                zf.write(file_path, arcname=arcname)
    
    zip_buffer.seek(0)
    
    # 保存 ZIP 文件
    zip_path = f'/tmp/{task_id}.zip'
    with open(zip_path, 'wb') as f:
        f.write(zip_buffer.read())
    
    return zip_path
```
        image_count += len(page.get_images())
        text_parts.append(page.get_text())
    
    return image_count == 0, "\n".join(text_parts), image_count
```

### 7.3 性能优化策略
- **内存流处理**: 使用 BytesIO 避免临时文件落盘
- **延迟加载**: 仅在需要时提取完整文本（extract_full_content=false 时只检测富媒体）
- **限制文件大小**: 设置最大上传大小（如 50MB）
- **超时控制**: 设置单个文件解析超时时间（如 30s）

## 8. 错误处理与边界情况

### 8.1 异常类型
- **UnsupportedFileTypeError**: 文件格式不支持（返回 400）
- **FileTooLargeError**: 文件超过大小限制（返回 413）
- **CorruptedFileError**: 文件损坏无法解析（返回 500，详细错误信息）
- **UnicodeDecodeError**: 文本文件编码错误（自动尝试 gbk/latin1/cp1252 备选编码）
- **TimeoutError**: 解析超时（返回 500）
- **MemoryError**: 文件过大导致内存不足（限制 max_content_length）

### 8.2 边界条件
- **空文件**: 返回 `is_pure_text=true`，`text_content=""`
- **仅包含空格/换行的文件**: 返回 `is_pure_text=true`，`total_characters=0`
- **加密文档**: 返回 `CorruptedFileError`，提示需要密码
- **Markdown 中的图片引用**: 检测 `![](...)` 语法，`has_images=true`
- **纯表格 Excel（无图表）**: 返回 `is_pure_text=true`（表格视为结构化文本）
- **PDF 扫描版（纯图片）**: 返回 `is_pure_text=false`，`image_count > 0`

## 9. 部署与运行

### 9.1 环境依赖
**requirements.txt**:
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
python-multipart==0.0.6
python-docx==1.1.0
openpyxl==3.1.2
python-pptx==0.6.23
PyMuPDF==1.23.8
chardet==5.2.0
```

安装命令：
```bash
pip install -r requirements.txt
```

### 9.2 启动服务
```bash
# 开发模式（热重载）
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 生产模式（多进程）
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 9.3 Docker 部署
**Dockerfile**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖（PDF 解析可能需要）
RUN apt-get update && apt-get install -y \
    libmupdf-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 限制上传文件大小
ENV MAX_UPLOAD_SIZE=52428800

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.yml**:
```yaml
version: '3.8'
services:
  doc-analyzer:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MAX_UPLOAD_SIZE=52428800  # 50MB
    volumes:
      - ./logs:/app/logs
```

构建与运行：
```bash
docker-compose up -d
```

## 10. 扩展功能（可选）

### 10.1 OCR 集成（扫描版文档处理）
对于纯图片 PDF（扫描版），集成 OCR 提取文字后再判断纯度：
```python
# 使用 PaddleOCR
from paddleocr import PaddleOCR

if image_count > 0 and text_length < 100:  # 可能是扫描版
    ocr = PaddleOCR(lang='ch')
    ocr_text = extract_ocr_text(file_stream)
    # 判断 OCR 后是否仍包含图表
```

### 10.2 高级相似度算法
**语义向量相似度**（可选升级）：
```python
# 使用预训练模型（如 Sentence-BERT）
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
vector = model.encode(text_content)
# 计算语义相似度，比 TF-IDF 更精确
```

### 10.3 增量更新优化
**基于文档修改时间的增量处理**：
```python
# Redis 记录文档最后处理时间
redis_client.hset(f"doc_index:{doc_id}", "last_processed", timestamp)

# 仅处理新上传或修改的文档
if file_modified_time > last_processed_time:
    # 执行完整处理流程
```

### 10.4 文档分类标签
**基于内容的自动标签**：
```python
# 金融领域关键词匹配
finance_keywords = {"投资": "投资类", "风险": "风控类", "合规": "合规类"}
tags = []
for keyword, tag in finance_keywords.items():
    if keyword in text_content:
        tags.append(tag)

redis_client.hset(f"doc_index:{doc_id}", "tags", json.dumps(tags))
```

### 10.5 富媒体元素提取与保存
**提取并独立存储富媒体元素**：
```python
# 提取 Word 中的图片
for rel in doc.part.rels.values():
    if "image" in rel.target_ref:
        image_data = rel.target_part.blob
        image_id = f"{doc_id}_img_{index}"
        # 保存到临时目录或编码为 base64
        redis_client.setex(f"image:{image_id}", 86400, base64.b64encode(image_data))
```

### 10.6 多语言支持
**检测并标记文档语言**：
```python
from langdetect import detect

language = detect(text_content)
redis_client.hset(f"doc_index:{doc_id}", "language", language)

# 根据语言选择分词器
if language == 'zh-cn':
    tokenizer = jieba
elif language == 'en':
    from nltk.tokenize import word_tokenize
    tokenizer = word_tokenize
```

### 10.7 文档版本管理
**记录同一文档的多个版本**：
```python
# 使用 Redis Sorted Set 按时间戳排序版本
version_key = f"doc_versions:{original_filename}"
timestamp = time.time()
redis_client.zadd(version_key, {doc_id: timestamp})

# 获取最新版本
latest_versions = redis_client.zrevrange(version_key, 0, 0)
```

### 10.8 批量下载压缩包
**批量任务完成后打包下载**：
```python
import zipfile
import io

def create_batch_download(task_id: str):
    # 获取所有转换文件
    results = redis_client.lrange(f"batch_results:{task_id}", 0, -1)
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for result in results:
            result_data = json.loads(result)
            if result_data.get("converted_file_url"):
                file_path = result_data["file_path"]
                zip_file.write(file_path, arcname=result_data["file_name"])
    
    zip_buffer.seek(0)
    return zip_buffer
```

## 11. 性能基准测试

### 11.1 预期性能指标
- **单文件处理速度**：
  - 小文件（< 1MB）：< 2 秒
  - 中等文件（1-10MB）：2-10 秒
  - 大文件（10-50MB）：10-30 秒

- **相似度检测**：
  - 与 100 个已存在文档对比：< 1 秒
  - 与 1000 个文档对比：< 3 秒

- **批量处理吞吐量**：
  - 并发数 5：约 10 个文件/分钟
  - 并发数 10：约 18 个文件/分钟

- **Redis 缓存命中率**：> 80%（重复上传场景）

### 11.2 压力测试建议
使用 **Locust** 或 **Apache JMeter** 进行压力测试：
```python
# locustfile.py
from locust import HttpUser, task, between

class DocumentAnalyzerUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def upload_document(self):
        files = {'file': open('test.docx', 'rb')}
        self.client.post("/api/v1/document/analyze", files=files)
```

运行压力测试：
```bash
locust -f locustfile.py --host=http://localhost:8000
```

## 12. 安全性考虑

### 12.1 文件上传安全
- **文件类型白名单验证**（MIME type + 扩展名双重检查）
- **文件大小限制**（默认 50MB，可配置）
- **病毒扫描集成**（可选，使用 ClamAV）
- **防止路径遍历攻击**（sanitize 文件名）

### 12.2 接口安全
- **API 认证**：JWT Token 或 API Key
- **限流控制**：每 IP 每分钟最多 60 次请求
- **CORS 配置**：限制允许的来源域名

### 12.3 数据安全
- **Redis 密码保护**：设置强密码
- **数据加密**：敏感字段使用 AES 加密存储
- **访问日志**：记录所有文件上传与下载操作

## 13. 故障排查指南

### 13.1 常见问题

**问题 1：Redis 连接失败**
```bash
# 检查 Redis 是否启动
redis-cli ping

# 检查连接配置
echo $REDIS_HOST
echo $REDIS_PORT
```

**问题 2：文件解析失败**
- 检查文件是否损坏
- 查看详细错误日志：`docker-compose logs app`
- 尝试使用其他工具打开文件验证

**问题 3：相似度检测不准确**
- 调整 `similarity_threshold` 参数
- 增加自定义分词词典（金融术语）
- 考虑升级为语义向量相似度

**问题 4：批量任务卡住**
```bash
# 查看任务状态
redis-cli HGETALL batch_task:{task_id}

# 清理僵尸任务
redis-cli DEL batch_task:{task_id}
redis-cli DEL batch_results:{task_id}
```

### 13.2 日志配置
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/app.log'),
        logging.StreamHandler()
    ]
)
```

## 14. 总结

本系统提供了一个**完整的知识库文档智能处理方案**，核心特性包括：

✅ **文档纯度检测**：智能识别纯文档与富媒体文档  
✅ **格式标准化**：统一转换为 .docx 格式  
✅ **智能去重**：SHA256 哈希 + TF-IDF 相似度双重检测  
✅ **批量处理**：异步并发处理，实时进度查询  
✅ **Redis 缓存**：高性能缓存与索引管理  
✅ **生产就绪**：Docker 一键部署，完整监控与日志  

适用于**金融、法律、教育等需要大规模文档管理的行业场景**。纯图片 PDF（扫描版），集成 OCR 提取文字后再判断纯度：
```python
# 使用 PaddleOCR
from paddleocr import PaddleOCR

if image_count > 0 and text_length < 100:  # 可能是扫描版
    ocr = PaddleOCR(lang='ch')
    ocr_text = extract_ocr_text(file_stream)
    # 判断 OCR 后是否仍包含图表
```

### 10.2 批量上传接口
**POST /api/v1/documents/batch-analyze**
```python
# 接收多个文件
files: List[UploadFile]

# 返回数组
[
  {"file_name": "doc1.docx", "is_pure_text": true, ...},
  {"file_name": "doc2.pptx", "is_pure_text": false, ...}
]
```

### 10.3 富媒体提取
对于非纯文档，提取图片并保存：
```python
# 提取 Word 中的图片
for rel in doc.part.rels.values():
    if "image" in rel.target_ref:
        image_data = rel.target_part.blob
        # 保存或返回 base64
```

### 10.4 智能分类标签
基于提取的文本内容，使用 NLP 模型自动打标签：
```python
# 金融领域关键词匹配
finance_keywords = ["投资", "风险", "收益", "资产"]
if any(kw in text_content for kw in finance_keywords):
    tags.append("金融文档")
```

### 10.5 文档相似度检测
计算文档内容哈希，检测重复或相似文档：
```python
import hashlib

content_hash = hashlib.sha256(text_content.encode()).hexdigest()
# 存储到 Redis，检测重复
```
