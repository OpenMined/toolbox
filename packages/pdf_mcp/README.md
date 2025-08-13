# PDF MCP - Local PDF Document Search & Analysis

A Model Context Protocol (MCP) server that provides intelligent semantic search capabilities for PDF documents using local AI processing.

## 🚀 Features

- **Semantic Search**: Find information across your PDF documents using natural language queries
- **Local Processing**: All document processing and AI inference happens locally - no data sent to external services
- **Automatic File Watching**: Automatically detects when PDFs are added, modified, or removed from your Documents folder
- **Fast Text Extraction**: Uses Poppler's `pdftotext` for efficient PDF text extraction
- **Smart Chunking**: Intelligently splits documents into searchable chunks with overlap for better context
- **Persistent Index**: Pre-computed embeddings are cached locally for instant search results
- **Real-time Updates**: Changes to your PDF files are automatically reflected in the search index

## 🏗️ How It Works

### Architecture Overview

1. **Document Monitoring**: Watches your `~/Documents/` folder for PDF file changes using filesystem events
2. **Text Extraction**: Uses Poppler's `pdftotext` to extract clean text from PDF documents
3. **Intelligent Chunking**: Splits documents into overlapping chunks (~1000 characters) for optimal search
4. **Local Embeddings**: Generates semantic embeddings using Ollama's `nomic-embed-text` model
5. **Vector Storage**: Stores embeddings and chunks in local files for persistence
6. **Semantic Search**: Performs similarity search across document chunks to find relevant content

### File Processing Pipeline

```
PDF Added → Text Extraction → Chunking → Embedding Generation → Index Storage
     ↓
PDF Modified → Re-process → Update Index → Save to Disk
     ↓
PDF Deleted → Remove from Index → Update Storage
```

## 📁 Directory Structure

- **Documents**: `~/Documents/` - Your main Documents folder (monitored for PDF files)
- **Data Cache**: `~/.pdf-mcp/` - Local storage for embeddings and processed chunks
- **Index File**: `~/.pdf-mcp/chunks.json` - Persistent storage of document chunks and metadata

## 🔧 Dependencies

### Required External Tools

1. **Poppler** (for `pdftotext`):

   ```bash
   # macOS
   brew install poppler

   # Ubuntu/Debian
   sudo apt-get install poppler-utils

   # Windows
   # Download from: https://poppler.freedesktop.org/
   ```

2. **Ollama** (for local embeddings):

   ```bash
   # Install Ollama
   curl -fsSL https://ollama.ai/install.sh | sh

   # Pull the embedding model (done automatically on first use)
   ollama pull nomic-embed-text:v1.5
   ```

## 🎯 Available MCP Tools

### Core Search Functions

- **`search_documents`** - Semantic search across all PDF documents

  - Query your documents using natural language
  - Returns relevant chunks with source document and page information
  - Supports complex queries and finds conceptually related content

- **`get_document_list`** - List all indexed PDF documents

  - Shows which documents are currently in the search index
  - Useful for understanding what content is available

- **`get_document_text`** - Retrieve full text content of a specific document
  - Get the complete extracted text from any indexed PDF
  - Useful for detailed document review

## 🚦 Usage Examples

### Basic Search

```
Ask Claude: "Search my PDFs for information about machine learning algorithms"
```

### Document Management

```
Ask Claude: "What PDF documents do I have indexed?"
Ask Claude: "Show me the full text of the research_paper.pdf document"
```

### Content Analysis

```
Ask Claude: "Find all references to climate change in my documents"
Ask Claude: "What documents mention Python programming?"
```

## 🔄 Automatic File Watching

The PDF MCP automatically monitors your Documents folder and will:

- **Detect new PDFs** and add them to the search index
- **Update the index** when existing PDFs are modified
- **Remove documents** from the index when PDFs are deleted or moved
- **Handle renames** by treating them as delete + add operations
- **Restart monitoring** automatically if the file watcher fails

### File Processing Status

- Documents are processed in the background when added
- Large documents may take a few moments to fully index
- The system uses debouncing to avoid processing files that are still being written
- All processing happens asynchronously without blocking other operations

## 🛠️ Installation

The PDF MCP is installed via the toolbox system:

```bash
tb install pdf-mcp
```

This will:

1. Install the MCP server and dependencies
2. Configure it to work with Claude Desktop
3. Set up automatic document monitoring
4. Create necessary data directories

## 🔍 Technical Details

- **Embedding Model**: nomic-embed-text:v1.5 (384 dimensions)
- **Chunk Size**: ~1000 characters with 200 character overlap
- **Search Method**: Cosine similarity on semantic embeddings
- **File Formats**: PDF only (uses pdftotext for extraction)
- **Concurrency**: Asynchronous processing with proper event loop handling
- **Error Handling**: Graceful degradation with comprehensive logging

## 🚨 Troubleshooting

### Common Issues

1. **No search results**: Ensure PDFs are in `~/Documents/` and have been processed
2. **Ollama errors**: Check that Ollama is running (`ollama serve`)
3. **Text extraction fails**: Verify Poppler is installed (`pdftotext --version`)
4. **File watching not working**: Check file permissions on Documents folder

### Logs

Monitor the server activity:

```bash
tb log pdf-mcp
```

Look for messages about:

- Document processing status
- File watcher events
- Embedding generation progress
- Search query execution

## 📄 License

This project is part of the toolbox ecosystem and follows the same licensing terms.
