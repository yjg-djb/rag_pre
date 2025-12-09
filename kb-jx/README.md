Here is the complete English translation of the document, formatted in Markdown.

---

# Document Detection and Batch Processing System

## Functional Description

This system implements document plain text detection and batch processing capabilities:

1.  **Single File Analysis**: Upload a single file to detect if it is plain text, and automatically convert it to DOCX.
2.  **Batch Upload**: Support batch file uploads while preserving the directory structure.
3.  **Intelligent Detection**: Detect rich media content such as images and charts within documents.
4.  **Format Conversion**: Unify plain text documents by converting them to DOCX format.
5.  **Categorized Download**: Provide three download options: plain text files, rich media files, and all files.

## Supported Formats

-   **Text**: `.txt`, `.md`
-   **Office**: `.docx`, `.xlsx`, `.pptx`
-   **PDF**: `.pdf`

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the Service

```bash
python main.py
```

The service will start at `http://localhost:8000`.

### 3. Access API Documentation

Open in browser: `http://localhost:8000/docs`

## API Usage Examples

### Single File Upload

```bash
curl -X POST "http://localhost:8000/api/v1/document/analyze" \
  -F "file=@document.pdf"
```

### Batch Upload (Preserving Directory Structure)

```bash
curl -X POST "http://localhost:8000/api/v1/documents/batch-upload" \
  -F "files=@finance/report.pdf;filename=finance/report.pdf" \
  -F "files=@hr/policy.docx;filename=hr/policy.docx" \
  -F "files=@readme.txt;filename=readme.txt"
```

### Query Task Status

```bash
curl "http://localhost:8000/api/v1/batch/status/{task_id}"
```

### Download Files

```bash
# Download converted plain text files
curl "http://localhost:8000/api/v1/batch/download/pure-converted/{task_id}" -o pure.zip

# Download original rich media files
curl "http://localhost:8000/api/v1/batch/download/rich-original/{task_id}" -o rich.zip

# Download all files
curl "http://localhost:8000/api/v1/batch/download/all/{task_id}" -o all.zip
```

## Project Structure

```
kb-jx/
├── main.py                 # FastAPI Main Program
├── requirements.txt        # Dependencies
├── api/
│   └── v1/
│       └── endpoints.py    # API Endpoints
├── services/
│   ├── detector.py         # Document Detection Service
│   ├── converter.py        # Format Conversion Service
│   └── zipper.py           # ZIP Packaging Service
├── models/
│   └── schemas.py          # Data Models
├── utils/
│   └── file_handler.py     # File Handling Utilities
└── storage/                # Storage Directory (Auto-created)
    ├── original/           # Original Files
    ├── converted/          # Converted Files
    └── batch/              # Batch Task Files
```

## Important Notes

1.  When uploading batch files, specify the relative path in the `filename` parameter to preserve the directory structure.
2.  The system will automatically create the `storage` directory to store files.
3.  Batch processing supports a maximum of 5 concurrent tasks.
4.  Once the task is complete, a ZIP package containing the full directory structure can be downloaded via the API.

## Testing Suggestions

1.  Prepare test files (including both plain text and rich media documents).
2.  Use Postman or curl to test the APIs.
3.  Visit `/docs` to view the interactive API documentation.
4.  Check if the downloaded ZIP package retains the directory structure.
