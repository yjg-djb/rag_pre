# RAG-Preprocess

<p align="center">
  <b>RAG Data Preprocessing Toolkit</b>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#api-documentation">API Docs</a> •
  <a href="#examples">Examples</a> •
  <a href="#contributing">Contributing</a>
</p>

<p align="center">
  <a href="README_CN.md">中文文档</a>
</p>

---

A comprehensive document preprocessing solution designed for **RAG (Retrieval-Augmented Generation)** and **Vector Database** applications. Intelligently convert various document formats into high-quality plain text for LLM knowledge bases.

## Why RAG-Preprocess?

| Challenge | Our Solution |
|-----------|--------------|
| Multiple document formats | Unified parser for PDF/DOCX/XLSX/PPTX/TXT/MD |
| Text in images not searchable | OCR + LLM optimization for accurate extraction |
| Table structure lost | Preserve semantic relationships, handle merged cells |
| Duplicate content affects retrieval | Multi-level dedup: document + paragraph + near-duplicate |
| Slow batch processing | Async concurrent processing with directory structure preservation |

## Features

### Core Capabilities

- **Multi-Format Parsing Engine**
  - PDF: Text extraction + Table recognition (Camelot) + Image OCR
  - DOCX/DOC: Paragraphs, tables, embedded images
  - XLSX/XLS: Multi-sheet support, merged cell handling
  - PPTX/PPT: Slide text and table extraction
  - TXT/MD: Markdown structure preservation

- **Intelligent OCR Processing**
  - Multiple OCR providers (PaddleOCR/Baidu/Aliyun)
  - LLM optimization: Auto-correct OCR errors
  - Image enhancement: Contrast optimization

- **Text Cleaning Pipeline**
  - Unicode normalization (ftfy)
  - Noise filtering: URLs, emails, phone numbers, page markers
  - Exact deduplication: SHA256 hashing
  - Near-duplicate detection: SimHash algorithm

- **RESTful API Service**
  - FastAPI with auto-generated OpenAPI docs
  - Async batch processing with 5 concurrent tasks
  - Categorized downloads (pure text/rich media/all)

### Supported Formats

| Format | Extensions | Detection | Conversion |
|--------|-----------|-----------|------------|
| Word Document | `.docx`, `.doc` | Images/Charts/Objects | To DOCX/Plain Text |
| Excel Spreadsheet | `.xlsx`, `.xls` | Charts/Images/Drawings | To DOCX/Plain Text |
| PowerPoint | `.pptx`, `.ppt` | Images/Charts/Shapes | To DOCX/Plain Text |
| PDF Document | `.pdf` | Images/Vector Graphics | To MD/DOCX |
| Plain Text | `.txt`, `.md` | Image references | Direct use |

## Quick Start

### Requirements

- Python 3.8+
- Windows / Linux / macOS

### Installation

```bash
# Clone repository
git clone https://github.com/your-org/rag-preprocess.git
cd rag-preprocess

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### Launch Service

```bash
# Option 1: Quick start (Windows)
start.bat

# Option 2: Command line
python main.py

# Option 3: Development mode (auto-reload)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

After startup, access:
- **Web Upload Interface**: http://localhost:8000/upload
- **API Docs (Swagger)**: http://localhost:8000/docs
- **API Docs (ReDoc)**: http://localhost:8000/redoc

## Architecture

```
rag-preprocess/
├── main.py                    # FastAPI application entry
├── config.py                  # Configuration management
├── requirements.txt           # Python dependencies
│
├── api/                       # API layer
│   └── v1/
│       └── endpoints.py       # RESTful endpoints
│
├── services/                  # Business logic layer
│   ├── detector.py            # Document type detection
│   ├── converter.py           # Format conversion service
│   ├── text_pipeline.py       # Text cleaning pipeline
│   └── zipper.py              # ZIP packaging service
│
├── parsers/                   # Document parsing engines
│   ├── doc_parser/            # DOCX parser
│   │   ├── main.py            # Batch processing entry
│   │   ├── llm_client.py      # LLM client
│   │   └── third_ocr.py       # Third-party OCR integration
│   ├── pdf_parser/            # PDF parser
│   │   ├── pdf2md.py          # PDF → Markdown
│   │   └── md2docx.py         # Markdown → DOCX
│   └── xlsx_parser/           # Excel parser
│       ├── excel_to_docx.py   # Excel → DOCX
│       └── table_relation.py  # Table relationship analysis
│
├── utils/                     # Utilities
│   ├── file_handler.py        # File operations
│   ├── logger.py              # Logging
│   ├── dedup_store.py         # Deduplication storage
│   └── cleaner.py             # Storage cleanup
│
├── models/                    # Data models
│   └── schemas.py             # Pydantic models
│
└── storage/                   # Runtime storage (auto-created)
    ├── original/              # Original files
    ├── converted/             # Converted results
    └── batch/                 # Batch tasks
```

### Processing Flow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Upload    │ → │   Detect    │ → │   Parse     │ → │   Clean     │
│   Document  │    │   Format    │    │   Content   │    │   Text      │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                            ↓
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Output    │ ← │   Convert   │ ← │   Dedupe    │
│   Result    │    │   Format    │    │   Content   │
└─────────────┘    └─────────────┘    └─────────────┘
```

## API Documentation

### Core Endpoints

#### 1. Single File Analysis

```bash
POST /api/v1/document/analyze
Content-Type: multipart/form-data
```

**Request**:
```bash
curl -X POST "http://localhost:8000/api/v1/document/analyze" \
  -F "file=@report.pdf"
```

**Response**:
```json
{
  "is_pure_text": true,
  "original_file": {
    "name": "report.pdf",
    "download_url": "/api/v1/files/download/original/abc123.pdf"
  },
  "converted_file": {
    "name": "report.docx",
    "download_url": "/api/v1/files/download/converted/abc123.docx"
  }
}
```

#### 2. Batch Upload (Preserve Directory Structure)

```bash
POST /api/v1/documents/batch-upload
Content-Type: multipart/form-data
```

**Request**:
```bash
curl -X POST "http://localhost:8000/api/v1/documents/batch-upload" \
  -F "files=@report.pdf;filename=finance/2024/report.pdf" \
  -F "files=@policy.docx;filename=hr/policy.docx"
```

**Response**:
```json
{
  "task_id": "batch_20241230_123456",
  "total_files": 2,
  "status_url": "/api/v1/batch/status/batch_20241230_123456"
}
```

#### 3. Query Task Status

```bash
GET /api/v1/batch/status/{task_id}
```

**Response**:
```json
{
  "task_id": "batch_20241230_123456",
  "status": "completed",
  "progress": {
    "total": 2,
    "completed": 2,
    "pure_text_count": 2,
    "rich_media_count": 0
  },
  "downloads": {
    "pure_text_converted": "/api/v1/batch/download/pure-converted/batch_20241230_123456",
    "all_files": "/api/v1/batch/download/all/batch_20241230_123456"
  }
}
```

#### 4. Download Results

```bash
# Download pure text converted package
GET /api/v1/batch/download/pure-converted/{task_id}

# Download rich media original package
GET /api/v1/batch/download/rich-original/{task_id}

# Download all files package
GET /api/v1/batch/download/all/{task_id}
```

### Full API Reference

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/upload` | Web upload page |
| POST | `/api/v1/document/analyze` | Single file analysis |
| POST | `/api/v1/documents/batch-upload` | Batch upload |
| GET | `/api/v1/batch/status/{task_id}` | Query task status |
| GET | `/api/v1/batch/download/pure-converted/{task_id}` | Download pure text package |
| GET | `/api/v1/batch/download/rich-original/{task_id}` | Download rich media package |
| GET | `/api/v1/batch/download/all/{task_id}` | Download all files |
| GET | `/api/v1/files/download/original/{file_id}` | Download original file |
| GET | `/api/v1/files/download/converted/{file_id}` | Download converted file |

## Examples

### Example 1: PDF Batch Conversion

```python
from parsers.pdf_parser.pdf2md import batch_pdf_to_md

# Configure batch processing
config = {
    "pdf_dir": "./input/pdfs",       # PDF files directory
    "md_dir": "./output/markdown",    # Markdown output directory
    "docx_dir": "./output/docx",      # DOCX output directory
    "enable_clean": True              # Clean intermediate files
}

# Execute batch conversion
batch_pdf_to_md(**config)
```

### Example 2: DOCX OCR Processing

```python
from parsers.doc_parser.main import batch_process

# Place DOCX files in input directory and run
# Output includes:
# - Extracted text content
# - Structured table data
# - OCR results (LLM optimized)
batch_process()
```

### Example 3: Excel to Plain Text

```python
from parsers.xlsx_parser.excel_to_docx import xlsx_to_docx

xlsx_to_docx(
    xlsx_path="./data.xlsx",
    docx_save_path="./output.docx",
    output_format="text",        # "text" or "table"
    filter_empty_rows=True,      # Filter empty rows
    keep_merge_info=False        # Don't preserve merge info
)
```

### Example 4: Text Cleaning Pipeline

```python
from services.text_pipeline import TextPipeline
from utils.dedup_store import DedupStore

# Initialize dedup storage
dedup_store = DedupStore()

# Create text pipeline
pipeline = TextPipeline(
    dedup_store=dedup_store,
    min_paragraph_len=10,              # Minimum paragraph length
    simhash_distance_threshold=3,      # Near-duplicate threshold
    enable_near_duplicate=True,        # Enable near-duplicate detection
    enable_cross_doc_dedup=True        # Enable cross-document dedup
)

# Process text
result = pipeline.process(raw_text, doc_name="example.pdf")
print(f"Cleaned text length: {result['stats']['final_length']}")
print(f"Duplicate paragraphs removed: {result['stats']['paragraphs_exact_dup']}")
```

## Configuration

### Environment Variables

Create a `.env` file:

```env
# Application
APP_HOST=0.0.0.0
APP_PORT=8000
APP_DEBUG=false

# Storage
STORAGE_BASE_DIR=./storage
STORAGE_CLEAN_KEEP_DAYS=7

# Redis (optional, for distributed dedup)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# OCR Configuration
OCR_PROVIDER=paddleocr  # paddleocr / baidu / aliyun
OCR_API_KEY=your_api_key

# LLM Configuration (for OCR optimization)
LLM_API_URL=https://api.openai.com/v1
LLM_API_KEY=your_api_key
LLM_MODEL=gpt-4o-mini
```

### Concurrency Settings

```python
# api/v1/endpoints.py
semaphore = asyncio.Semaphore(5)  # Modify concurrent tasks
```

## Performance Optimization

- **Async I/O**: All file operations are asynchronous
- **Concurrent Processing**: Batch tasks support 5 concurrent (configurable)
- **Streaming Transfer**: Large file downloads use FileResponse
- **Memory Optimization**: Files written directly to disk
- **Startup Cleanup**: Auto-clean expired task files

## Tech Stack

| Component | Technology |
|-----------|------------|
| Web Framework | FastAPI 0.104+ |
| ASGI Server | Uvicorn |
| Word Processing | python-docx |
| Excel Processing | openpyxl |
| PPT Processing | python-pptx |
| PDF Processing | PyMuPDF (fitz) |
| Table Extraction | Camelot |
| OCR | PaddleOCR / Third-party API |
| Text Normalization | ftfy |
| Near-Duplicate Detection | simhash |
| Data Validation | Pydantic |
| Async Processing | asyncio |

## FAQ

### Q: How to process scanned PDFs?

Scanned PDFs (image-only) are automatically processed via OCR. Tips:
1. Ensure OCR service is properly configured
2. Scan quality affects recognition accuracy
3. Enable LLM optimization for better results

### Q: Which OCR services are supported?

Currently supported:
- PaddleOCR (local deployment, free)
- Baidu Cloud OCR
- Aliyun OCR
- Custom OCR service (implement `batch_ocr` interface)

### Q: How to extend support for new formats?

1. Create new parser module in `parsers/`
2. Implement standard parsing interface
3. Add format detection in `services/detector.py`
4. Add conversion logic in `services/converter.py`

### Q: Does dedup storage support distributed deployment?

Yes, via Redis backend:
- Document-level dedup: SHA256 hash storage
- Paragraph-level dedup: SimHash fingerprint storage
- Supports cluster deployment

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 code style
- Add necessary type annotations
- Write unit tests
- Update documentation

## License

This project is licensed under the [MIT License](LICENSE).

## Acknowledgments

Thanks to these open source projects:

- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [python-docx](https://python-docx.readthedocs.io/) - Word document processing
- [PyMuPDF](https://pymupdf.readthedocs.io/) - PDF processing
- [Camelot](https://camelot-py.readthedocs.io/) - PDF table extraction
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) - OCR engine

---

<p align="center">
  <b>If this project helps you, please give it a Star ⭐️</b>
</p>
