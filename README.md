The knowledge base preprocessing module kb-jx performs the following steps:

It first analyzes and separates input documents into plain text and rich media formats (such as images, tables, PDFs with embedded graphics, audio, video, etc.). The extracted plain text is then processed through a series of cleaning and normalization pipelines, including:

Deduplication using algorithmic methods to remove redundant or near-duplicate content
Text sanitization via regular expressions (regex) to eliminate noise such as HTML/XML tags, special characters, excessive whitespace, invisible control characters, and other non-semantic artifacts
This cleaned plain text is subsequently prepared for downstream tasks like chunking, embedding, and vector indexing in the knowledge base.
# Intelligent Document Parser

This project provides specialized parsers for challenging semi-structured document formats—enabling robust conversion into clean, structured plain text suitable for LLMs, RAG systems, and downstream NLP pipelines.

## Key Capabilities

- ✅ **Multimodal "Pad Word" Documents**:  
  Handles hybrid documents from digital notepads (e.g., WPS Pad, mobile note apps) that combine freehand writing, typed text, images, and layout elements.

- ✅ **Complex `.xlsx` Spreadsheets**:  
  Accurately parses Excel files with merged cells, cross-sheet references, nested headers, formulas, and multi-level tables.

- ✅ **Semi-Structured → Structured Text**:  
  Transforms raw, noisy inputs into well-organized, machine-readable output in **Markdown** or **JSON**, preserving semantic relationships and data integrity.

## Output Example

**Input**: A scanned "pad word" note with handwritten tables + a complex financial `.xlsx` file  
**Output**:
```json
{
  "document_type": "multimodal_note",
  "sections": [
    {
      "type": "table",
      "data": [
        {"Item": "Revenue", "Q1": "¥1.2M", "Q2": "¥1.5M"}
      ]
    }
  ]
}
