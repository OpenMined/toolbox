import os
import asyncio
import logging
import time
from pathlib import Path
from mcp.server.fastmcp import FastMCP

from pdf_mcp.rag_engine import RagEngine
from pdf_mcp.file_watcher import DocumentFileWatcher

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Enable debug logging for file watcher
file_watcher_logger = logging.getLogger("pdf_mcp.file_watcher")
file_watcher_logger.setLevel(logging.DEBUG)

# Configuration from environment
APP_HOME = Path(os.getenv("APP_HOME", Path.home() / ".pdf-mcp"))
DATA_DIR = os.getenv("DATA_DIR", APP_HOME)
DOCUMENTS_DIR = os.getenv("DOCUMENTS_DIR", Path.home() / "Documents")
# Initialize MCP server
mcp = FastMCP("PDF RAG MCP Server", stateless_http=True)

# Global RAG engine instance
rag_engine: RagEngine = None
file_watcher: DocumentFileWatcher = None
initialization_status = "not_started"
loading_progress = {
    "total_files": 0,
    "processed_files": 0,
    "current_file": "",
    "current_file_chunks": 0,
    "total_chunks": 0,
    "start_time": None,
    "estimated_remaining": None
}


async def initialize_rag_engine():
    """Initialize the RAG engine and load documents"""
    global rag_engine, file_watcher, initialization_status, loading_progress
    
    try:
        initialization_status = "initializing"
        logger.info("Initializing RAG engine...")
        rag_engine = RagEngine(str(DATA_DIR))
        await rag_engine.initialize()
        
        # Auto-load documents from Documents directory
        logger.info("Starting automatic document loading...")
        await start_document_loading_with_progress(str(DOCUMENTS_DIR))
        
        # Initialize and start file watcher
        logger.info("Starting file watcher for automatic updates...")
        logger.info(f"Documents directory for watching: {DOCUMENTS_DIR}")
        file_watcher = DocumentFileWatcher(str(DOCUMENTS_DIR), rag_engine, loading_progress)
        await file_watcher.start_watching()
        
        # Verify file watcher is running
        if file_watcher.is_watching():
            logger.info("✅ File watcher is running and ready to detect file changes")
            logger.info(f"✅ Event loop captured: {file_watcher.event_loop is not None}")
            
            # Start a background task to periodically check file watcher health
            asyncio.create_task(periodic_health_check())
        else:
            logger.warning("❌ File watcher failed to start properly")
        
        initialization_status = "ready"
        logger.info("RAG engine initialization complete with file watching enabled")
    except Exception as e:
        initialization_status = "failed"
        logger.error(f"Failed to initialize RAG engine: {e}")
        logger.error("PDF MCP will start but search functionality may be limited")
        # Don't fail startup, just log the error
        rag_engine = None
        file_watcher = None


async def start_document_loading_with_progress(directory_path: str = None):
    """Start document loading with progress tracking"""
    global loading_progress, initialization_status
    
    if not rag_engine:
        return "RAG engine not initialized"
    
    if directory_path is None:
        directory_path = str(DOCUMENTS_DIR)
    
    try:
        import time
        from pathlib import Path
        
        documents_path = Path(directory_path)
        if not documents_path.exists():
            return f"Directory does not exist: {directory_path}"
        
        pdf_files = list(documents_path.glob("*.pdf"))
        if not pdf_files:
            return f"No PDF files found in: {directory_path}"
        
        # Initialize progress tracking
        loading_progress.update({
            "total_files": len(pdf_files),
            "processed_files": 0,
            "current_file": "",
            "current_file_chunks": 0,
            "total_chunks": 0,
            "start_time": time.time(),
            "estimated_remaining": None
        })
        
        initialization_status = "loading_documents"
        logger.info(f"Starting to load {len(pdf_files)} PDF files with progress tracking...")
        
        # Load documents with progress updates
        await rag_engine.load_documents_from_dir_with_progress(directory_path, loading_progress)
        
        initialization_status = "ready"
        logger.info("Document loading completed!")
        
        return f"Successfully loaded {loading_progress['processed_files']} documents with {loading_progress['total_chunks']} total chunks"
        
    except Exception as e:
        initialization_status = "failed"
        logger.error(f"Error loading documents: {e}")
        return f"Error loading documents: {str(e)}"


@mcp.tool()
async def search_documents(query: str, top_k: int = 5) -> str:
    """
    Search through uploaded PDF documents using semantic similarity.
    
    Args:
        query (str): The search query
        top_k (int): Number of results to return (default: 5)
    
    Returns:
        str: Formatted search results with relevance scores
    """
    if not rag_engine:
        return "RAG engine not initialized"
    
    try:
        results = await rag_engine.search(query, top_k)
        
        if not results:
            return "No results found."
        
        formatted_results = []
        for i, result in enumerate(results, 1):
            formatted_results.append(
                f"**Result {i}** (Score: {result.score:.3f}) [{result.document}]\n"
                f"{result.text}\n"
            )
        
        return f"Found {len(results)} results for '{query}':\n\n" + "\n---\n\n".join(formatted_results)
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        return f"Search error: {str(e)}"


async def get_loading_progress() -> str:
    """
    Get detailed progress of document loading and chunking.
    Internal function - not exposed as MCP tool.
    
    Returns:
        str: Detailed progress information including current file, chunks, and time estimates
    """
    if initialization_status == "loading_documents":
        import time
        
        current_time = time.time()
        elapsed_time = current_time - (loading_progress["start_time"] or current_time)
        
        # Calculate progress percentage
        file_progress = (loading_progress["processed_files"] / max(loading_progress["total_files"], 1)) * 100
        
        # Estimate remaining time
        if loading_progress["processed_files"] > 0 and elapsed_time > 0:
            avg_time_per_file = elapsed_time / loading_progress["processed_files"]
            remaining_files = loading_progress["total_files"] - loading_progress["processed_files"]
            estimated_remaining = avg_time_per_file * remaining_files
            loading_progress["estimated_remaining"] = estimated_remaining
        
        progress_info = []
        progress_info.append(f"📊 Loading Progress: {file_progress:.1f}% complete")
        progress_info.append(f"📁 Files: {loading_progress['processed_files']}/{loading_progress['total_files']}")
        progress_info.append(f"📄 Current: {loading_progress['current_file']}")
        progress_info.append(f"🔢 Current file chunks: {loading_progress['current_file_chunks']}")
        progress_info.append(f"📦 Total chunks so far: {loading_progress['total_chunks']}")
        progress_info.append(f"⏱️  Elapsed: {elapsed_time:.1f}s")
        
        if loading_progress["estimated_remaining"]:
            progress_info.append(f"⏳ Estimated remaining: {loading_progress['estimated_remaining']:.1f}s")
        
        return "\n".join(progress_info)
    
    elif initialization_status == "ready":
        return f"✅ Loading complete! Processed {loading_progress['total_chunks']} chunks from {loading_progress['processed_files']} documents."
    
    elif initialization_status == "failed":
        return "❌ Loading failed. Check logs for details."
    
    else:
        return f"Status: {initialization_status} (no loading in progress)"


async def get_initialization_status() -> str:
    """
    Get the current initialization status of the RAG engine.
    Internal function - not exposed as MCP tool.
    
    Returns:
        str: Current status and details
    """
    status_messages = {
        "not_started": "Initialization has not started yet",
        "initializing": "RAG engine is initializing...",
        "loading_documents": "Loading and processing PDF documents from Documents folder...",
        "ready": "RAG engine is ready",
        "failed": "Initialization failed"
    }
    
    message = status_messages.get(initialization_status, "Unknown status")
    
    if initialization_status == "ready" and rag_engine:
        doc_count = len(rag_engine.list_documents())
        chunk_count = len(rag_engine.chunks)
        message += f" - {doc_count} documents loaded with {chunk_count} chunks"
    elif initialization_status == "loading_documents":
        message += "\nThis may take several minutes depending on the number and size of PDF files being processed."
    
    return f"Status: {initialization_status}\n{message}"


@mcp.tool()
async def get_document_list() -> str:
    """
    List all uploaded PDF documents.
    
    Returns:
        str: List of document names
    """
    if initialization_status != "ready":
        if initialization_status == "loading_documents":
            return "Still loading documents from your Documents folder. This may take several minutes."
        elif initialization_status == "failed":
            return "RAG engine initialization failed. Check logs for details."
        else:
            return f"RAG engine is {initialization_status}."
    
    if not rag_engine:
        return "RAG engine not available despite ready status. Please check logs."
    
    try:
        documents = rag_engine.list_documents()
        
        if not documents:
            return f"No documents loaded yet. Documents are automatically loaded from your Documents folder ({DOCUMENTS_DIR}) during initialization."
        
        doc_list = "\n".join(f"{i}. {doc}" for i, doc in enumerate(documents, 1))
        return f"Uploaded documents ({len(documents)}):\n{doc_list}"
        
    except Exception as e:
        logger.error(f"List documents error: {e}")
        return f"Error listing documents: {str(e)}"


async def load_documents_from_directory(directory_path: str = None) -> str:
    """
    Load and process PDF documents from a directory.
    Internal function - not exposed as MCP tool.
    
    Args:
        directory_path (str, optional): Path to directory containing PDFs. 
                                      If not provided, uses default Documents directory.
    
    Returns:
        str: Status of the loading process
    """
    if not rag_engine:
        return "RAG engine not initialized yet. Please wait for initialization to complete."
    
    if directory_path is None:
        directory_path = str(DOCUMENTS_DIR)
    
    try:
        documents_path = Path(directory_path)
        if not documents_path.exists():
            return f"Directory does not exist: {directory_path}"
        
        pdf_files = list(documents_path.glob("*.pdf"))
        if not pdf_files:
            return f"No PDF files found in: {directory_path}"
        
        logger.info(f"Starting to load {len(pdf_files)} PDF files from {directory_path}")
        
        # Use progress tracking if available
        if hasattr(rag_engine, 'load_documents_from_dir_with_progress'):
            # Initialize progress tracking
            loading_progress.update({
                "total_files": len(pdf_files),
                "processed_files": 0,
                "current_file": "",
                "current_file_chunks": 0,
                "total_chunks": 0,
                "start_time": time.time(),
                "estimated_remaining": None
            })
            initialization_status = "loading_documents"
            await rag_engine.load_documents_from_dir_with_progress(directory_path, loading_progress)
        else:
            await rag_engine.load_documents_from_dir(directory_path)
        
        doc_count = len(rag_engine.list_documents())
        chunk_count = len(rag_engine.chunks)
        return f"Successfully loaded documents from {directory_path}. Total: {doc_count} documents with {chunk_count} chunks."
        
    except Exception as e:
        logger.error(f"Error loading documents: {e}")
        return f"Error loading documents: {str(e)}"


async def start_auto_loading() -> str:
    """
    Restart document loading from the Documents directory.
    Internal function - not exposed as MCP tool.
    
    Returns:
        str: Status of the loading process initiation
    """
    global initialization_status
    
    if initialization_status == "loading_documents":
        return "Document loading is already in progress."
    
    if not rag_engine:
        return "RAG engine not initialized yet. Please wait for initialization to complete."
    
    try:
        # Start loading in the background
        asyncio.create_task(start_document_loading_with_progress())
        return f"Started document loading from {DOCUMENTS_DIR}."
        
    except Exception as e:
        logger.error(f"Error starting loading: {e}")
        return f"Error starting loading: {str(e)}"


async def periodic_health_check():
    """Periodically ensure file watcher is alive and fix any sync issues"""
    while True:
        try:
            await asyncio.sleep(60)  # Check every minute
            
            # Ensure the file watcher observer is alive
            if file_watcher:
                observer_restarted = await file_watcher.ensure_observer_alive()
                if observer_restarted:
                    logger.info("🔄 File watcher observer was restarted during health check")
            
            # Quick sync check - only clean up stale entries (deleted files)
            if rag_engine:
                documents_path = Path(DOCUMENTS_DIR)
                if documents_path.exists():
                    current_pdf_files = set(pdf_file.name for pdf_file in documents_path.glob("*.pdf"))
                    indexed_documents = set(rag_engine.list_documents())
                    stale_entries = indexed_documents - current_pdf_files
                    
                    if stale_entries:
                        logger.info(f"🧹 Cleaning up {len(stale_entries)} stale entries from index")
                        await sync_document_index()
                
        except Exception as e:
            logger.error(f"Error in periodic health check: {e}")


async def get_rag_stats() -> str:
    """
    Get RAG system statistics and status.
    Internal function - not exposed as MCP tool.
    
    Returns:
        str: JSON-formatted statistics
    """
    if not rag_engine:
        return "RAG engine not initialized"
    
    try:
        stats = rag_engine.get_stats()
        import json
        return f"RAG System Stats:\n{json.dumps(stats, indent=2)}"
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return f"Error getting stats: {str(e)}"









@mcp.tool()
async def get_document_text(filename: str) -> str:
    """
    Get the content of a document given its filename (now uses RAG search).
    
    Args:
        filename (str): The filename of the document to search within.
    
    Returns:
        str: Search results from the document.
    """
    if not rag_engine:
        return "RAG engine not initialized"
    
    # Search within the specific document
    try:
        results = await rag_engine.search(f"document:{filename}", top_k=10)
        document_results = [r for r in results if r.document == filename]
        
        if not document_results:
            return f"No content found in document: {filename}"
        
        # Return the first few chunks of the document
        content_parts = []
        for i, result in enumerate(document_results[:5], 1):
            content_parts.append(f"**Section {i}**:\n{result.text}")
        
        return f"Content from {filename}:\n\n" + "\n\n---\n\n".join(content_parts)
        
    except Exception as e:
        logger.error(f"Document text error: {e}")
        return f"Error getting document text: {str(e)}"


async def get_file_watcher_status() -> str:
    """
    Get the status of the automatic file watcher.
    Internal function - not exposed as MCP tool.
    
    Returns:
        str: File watcher status and information
    """
    if not file_watcher:
        return "File watcher is not initialized"
    
    status = "running" if file_watcher.is_watching() else "stopped"
    documents_dir = file_watcher.documents_dir
    
    # Get detailed status
    result = f"File watcher status: {status}\n"
    result += f"Monitoring directory: {documents_dir}\n"
    result += f"Directory exists: {documents_dir.exists()}\n"
    
    if file_watcher.observer:
        result += f"Observer is alive: {file_watcher.observer.is_alive()}\n"
        result += f"Observer emitters: {len(file_watcher.observer.emitters)}\n"
    else:
        result += "Observer: None\n"
    
    # Check current files in directory
    if documents_dir.exists():
        pdf_files = list(documents_dir.glob("*.pdf"))
        result += f"Current PDF files in directory: {len(pdf_files)}\n"
        if pdf_files:
            result += "Files: " + ", ".join([f.name for f in pdf_files[:5]]) + ("..." if len(pdf_files) > 5 else "") + "\n"
    
    # Check indexed documents
    if rag_engine:
        indexed_docs = rag_engine.list_documents()
        result += f"Documents in search index: {len(indexed_docs)}\n"
    
    result += "\nThe file watcher should automatically detect when PDF files are added, modified, deleted, or moved in your Documents folder."
    
    return result








async def sync_document_index() -> str:
    """
    Synchronize the document index with the actual files in the Documents folder.
    This will remove any documents from the index that no longer exist in the folder.
    Internal function - called automatically by the system.
    
    Returns:
        str: Result of the synchronization process
    """
    if not rag_engine:
        return "RAG engine not initialized"
    
    try:
        documents_path = Path(DOCUMENTS_DIR)
        if not documents_path.exists():
            return f"Documents directory does not exist: {DOCUMENTS_DIR}"
        
        # Get current files in the Documents folder
        current_pdf_files = set(pdf_file.name for pdf_file in documents_path.glob("*.pdf"))
        
        # Get documents currently in the index
        indexed_documents = set(rag_engine.list_documents())
        
        # Find documents that are indexed but no longer exist in the folder
        missing_documents = indexed_documents - current_pdf_files
        
        if not missing_documents:
            return f"Document index is already in sync. Found {len(indexed_documents)} documents."
        
        # Remove chunks for missing documents
        chunks_removed = 0
        for missing_doc in missing_documents:
            logger.info(f"Removing chunks for missing document: {missing_doc}")
            chunks_before = len(rag_engine.chunks)
            rag_engine.chunks = {
                k: v for k, v in rag_engine.chunks.items() 
                if v.document_name != missing_doc
            }
            chunks_after = len(rag_engine.chunks)
            chunks_removed += chunks_before - chunks_after
        
        # Save the updated chunks to disk
        await rag_engine.save_to_disk()
        
        # Get final document count
        final_documents = rag_engine.list_documents()
        
        result = f"Synchronized document index:\n"
        result += f"- Removed {len(missing_documents)} missing documents: {', '.join(missing_documents)}\n"
        result += f"- Removed {chunks_removed} chunks\n"
        result += f"- Current documents in index: {len(final_documents)}"
        
        return result
        
    except Exception as e:
        logger.error(f"Error syncing document index: {e}")
        return f"Error syncing document index: {str(e)}"


async def cleanup_resources():
    """Cleanup resources when shutting down"""
    global file_watcher
    
    if file_watcher:
        logger.info("Stopping file watcher...")
        file_watcher.stop_watching()
        file_watcher = None
        logger.info("File watcher stopped")


# Startup will be handled by app.py lifespan

if __name__ == "__main__":
    # Ensure directories exist
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
    Path(DOCUMENTS_DIR).mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Data directory: {DATA_DIR}")
    logger.info(f"Documents directory: {DOCUMENTS_DIR}")
    logger.info("Starting PDF RAG MCP Server...")
    
    mcp.run(transport="streamable-http", mount_path="/mcp")