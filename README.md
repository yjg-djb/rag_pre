The knowledge base preprocessing module kb-jx performs the following steps:

It first analyzes and separates input documents into plain text and rich media formats (such as images, tables, PDFs with embedded graphics, audio, video, etc.). The extracted plain text is then processed through a series of cleaning and normalization pipelines, including:

Deduplication using algorithmic methods to remove redundant or near-duplicate content
Text sanitization via regular expressions (regex) to eliminate noise such as HTML/XML tags, special characters, excessive whitespace, invisible control characters, and other non-semantic artifacts
This cleaned plain text is subsequently prepared for downstream tasks like chunking, embedding, and vector indexing in the knowledge base.
