import asyncio
import logging
import os
import time
from pathlib import Path
from typing import Optional, Callable, Dict, Any
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

logger = logging.getLogger(__name__)

# Constants
DEBOUNCE_DELAY = 2.0  # Wait 2 seconds after last modification
FILE_STABILITY_CHECK_DELAY = 0.5  # Initial delay to check file stability
FILE_STABILITY_WAIT = 2.0  # Additional wait if file is still being written
OBSERVER_JOIN_TIMEOUT = 1.0  # Timeout when stopping observer
PDF_EXTENSION = '.pdf'


class PDFFileHandler(FileSystemEventHandler):
    """Handler for PDF file system events"""
    
    def __init__(self, callback: Callable[[str, str, Path], None], event_loop=None):
        """
        Initialize the handler
        
        Args:
            callback: Async callback function that takes (event_type, filename, file_path)
            event_loop: Event loop to use for scheduling async callbacks
        """
        super().__init__()
        self.callback = callback
        self.processing_files: Dict[str, float] = {}  # Track files being processed
        self.debounce_delay = DEBOUNCE_DELAY
        self.event_loop = event_loop
    
    def _is_pdf_file(self, path: str) -> bool:
        """Check if a file path represents a PDF file"""
        return path.lower().endswith(PDF_EXTENSION)
    
    def _should_process_event(self, event: FileSystemEvent) -> bool:
        """Check if an event should be processed (non-directory PDF file)"""
        return not event.is_directory and self._is_pdf_file(event.src_path)
        
    def on_any_event(self, event):
        """Log PDF file system events"""
        src_path = getattr(event, 'src_path', None)
        if src_path and self._is_pdf_file(src_path):
            logger.info(f"📄 PDF {event.event_type}: {Path(src_path).name}")
            if hasattr(event, 'dest_path') and event.dest_path:
                logger.info(f"   -> Destination: {Path(event.dest_path).name}")
        
    def on_created(self, event: FileSystemEvent):
        """Handle file creation events"""
        if self._should_process_event(event):
            file_path = Path(event.src_path)
            logger.info(f"🟢 PDF file created: {file_path.name}")
            self._schedule_processing('created', file_path)
    
    def on_modified(self, event: FileSystemEvent):
        """Handle file modification events"""
        if self._should_process_event(event):
            file_path = Path(event.src_path)
            logger.info(f"🟡 PDF file modified: {file_path.name}")
            self._schedule_processing('modified', file_path)
    
    def on_deleted(self, event: FileSystemEvent):
        """Handle file deletion events"""
        if self._should_process_event(event):
            file_path = Path(event.src_path)
            logger.info(f"🔴 PDF file deleted: {file_path.name}")
            # Process deletions immediately (no debouncing needed)
            self._schedule_async_callback('deleted', file_path.name, file_path)
    
    def on_moved(self, event: FileSystemEvent):
        """Handle file move/rename events"""
        if event.is_directory:
            return
            
        # Handle as deletion of old file and creation of new file
        if hasattr(event, 'src_path') and self._is_pdf_file(event.src_path):
            old_path = Path(event.src_path)
            logger.info(f"🔄 PDF file moved from: {old_path.name}")
            self._schedule_async_callback('deleted', old_path.name, old_path)
        
        if hasattr(event, 'dest_path') and self._is_pdf_file(event.dest_path):
            new_path = Path(event.dest_path)
            logger.info(f"🔄 PDF file moved to: {new_path.name}")
            self._schedule_processing('created', new_path)
    
    def _schedule_processing(self, event_type: str, file_path: Path):
        """Schedule file processing with debouncing"""
        filename = file_path.name
        current_time = time.time()
        
        # Update the last modification time for this file
        self.processing_files[filename] = current_time
        
        # Schedule the actual processing after debounce delay
        self._schedule_coroutine(
            self._debounced_processing(event_type, filename, file_path, current_time),
            f"debounced {event_type} processing for {filename}"
        )
    
    async def _debounced_processing(self, event_type: str, filename: str, file_path: Path, scheduled_time: float):
        """Process file after debounce delay"""
        await asyncio.sleep(self.debounce_delay)
        
        # Check if this is still the latest modification for this file
        if filename in self.processing_files and self.processing_files[filename] == scheduled_time:
            # Remove from tracking and process
            self.processing_files.pop(filename, None)
            await self._safe_callback(event_type, filename, file_path)
    
    def _schedule_async_callback(self, event_type: str, filename: str, file_path: Path):
        """Schedule an async callback to be executed immediately"""
        self._schedule_coroutine(
            self._safe_callback(event_type, filename, file_path),
            f"{event_type} callback for {filename}"
        )
    
    def _schedule_coroutine(self, coro, description: str):
        """Schedule a coroutine on the event loop with error handling"""
        try:
            loop = self._get_event_loop()
            if loop:
                future = asyncio.run_coroutine_threadsafe(coro, loop)
                logger.debug(f"Scheduled {description}")
                return future
            else:
                logger.error(f"No event loop available for {description}")
                
        except Exception as e:
            logger.error(f"Failed to schedule {description}: {e}")
        
        return None
    
    def _get_event_loop(self):
        """Get the event loop to use for scheduling coroutines"""
        # Use the stored event loop if available
        if self.event_loop and not self.event_loop.is_closed():
            return self.event_loop
        
        # Fallback: try to get the running event loop
        try:
            return asyncio.get_running_loop()
        except RuntimeError:
            return None

    async def _safe_callback(self, event_type: str, filename: str, file_path: Path):
        """Safely call the callback with error handling"""
        try:
            logger.debug(f"Executing {event_type} callback for {filename}")
            await self.callback(event_type, filename, file_path)
            logger.debug(f"Completed {event_type} callback for {filename}")
        except Exception as e:
            logger.error(f"Error processing {event_type} event for {filename}: {e}")


class DocumentFileWatcher:
    """File watcher for PDF documents with automatic processing"""
    
    def __init__(self, documents_dir: str, rag_engine, loading_progress: Dict[str, Any]):
        """
        Initialize the file watcher
        
        Args:
            documents_dir: Directory to watch for PDF files
            rag_engine: RAG engine instance for processing documents
            loading_progress: Progress tracking dictionary
        """
        self.documents_dir = Path(documents_dir)
        self.rag_engine = rag_engine
        self.loading_progress = loading_progress
        self.observer: Optional[Observer] = None
        self.handler: Optional[PDFFileHandler] = None
        self.is_running = False
        self.event_loop = None  # Store reference to the event loop
        
    async def start_watching(self):
        """Start watching the documents directory"""
        if self.is_running:
            logger.warning("File watcher is already running")
            return
        
        if not self.documents_dir.exists():
            logger.warning(f"Documents directory does not exist: {self.documents_dir}")
            self.documents_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created documents directory: {self.documents_dir}")
        
        logger.info(f"Starting file watcher for: {self.documents_dir}")
        
        try:
            # Store reference to the current event loop
            try:
                self.event_loop = asyncio.get_running_loop()
                logger.debug(f"Captured event loop: {id(self.event_loop)}")
            except RuntimeError:
                logger.warning("No running event loop found during file watcher initialization")
                self.event_loop = None
            
            # Create handler and observer
            self.handler = PDFFileHandler(self._handle_file_event, self.event_loop)
            self.observer = Observer()
            
            # Schedule and start the observer
            self.observer.schedule(self.handler, str(self.documents_dir), recursive=False)
            self.observer.start()
            self.is_running = True
            
            logger.info(f"✅ File watcher started successfully for: {self.documents_dir}")
            logger.info("🔍 Monitoring PDF files: create, modify, delete, and move operations")
            
        except Exception as e:
            logger.error(f"❌ Failed to start file watcher: {e}")
            self.is_running = False
            raise
    
    def stop_watching(self):
        """Stop watching the documents directory"""
        if not self.is_running or not self.observer:
            return
        
        logger.info("Stopping file watcher...")
        self.observer.stop()
        self.observer.join()
        self.observer = None
        self.handler = None
        self.is_running = False
        logger.info("File watcher stopped")
    
    async def _handle_file_event(self, event_type: str, filename: str, file_path: Path):
        """Handle file system events"""
        if not self.rag_engine:
            logger.warning("RAG engine not available, skipping file processing")
            return
        
        logger.info(f"Processing {event_type} event for: {filename}")
        
        try:
            if event_type == 'deleted':
                await self._handle_file_deletion(filename)
            elif event_type in ('created', 'modified'):
                await self._handle_file_addition_or_modification(filename, file_path)
        except Exception as e:
            logger.error(f"Error handling {event_type} event for {filename}: {e}")
    
    async def _handle_file_deletion(self, filename: str):
        """Handle file deletion by removing chunks"""
        logger.info(f"Processing deletion for file: {filename}")
        
        # Remove chunks for this document
        chunks_before = len(self.rag_engine.chunks)
        self.rag_engine.chunks = {
            k: v for k, v in self.rag_engine.chunks.items() 
            if v.document_name != filename
        }
        chunks_removed = chunks_before - len(self.rag_engine.chunks)
        
        if chunks_removed > 0:
            logger.info(f"Removed {chunks_removed} chunks for deleted file: {filename}")
            await self.rag_engine.save_to_disk()
        else:
            logger.info(f"No chunks found for deleted file: {filename}")
    
    async def _handle_file_addition_or_modification(self, filename: str, file_path: Path):
        """Handle file addition or modification by processing the file"""
        if not file_path.exists():
            logger.warning(f"File no longer exists: {filename}")
            return
        
        logger.info(f"Processing file: {filename}")
        
        try:
            # Wait for file to stabilize
            await self._wait_for_file_stability(file_path, filename)
            
            # Read and validate file
            data = file_path.read_bytes()
            if len(data) == 0:
                logger.warning(f"File {filename} is empty, skipping")
                return
            
            # Process the document (this will replace existing chunks if any)
            chunk_count = await self.rag_engine.add_document(filename, data)
            logger.info(f"Successfully processed {filename} with {chunk_count} chunks")
            
            # Save the updated chunks to disk
            await self.rag_engine.save_to_disk()
            
        except Exception as e:
            logger.error(f"Error processing file {filename}: {e}")
    
    async def _wait_for_file_stability(self, file_path: Path, filename: str):
        """Wait for file to finish being written by checking size stability"""
        initial_size = file_path.stat().st_size
        await asyncio.sleep(FILE_STABILITY_CHECK_DELAY)
        current_size = file_path.stat().st_size
        
        if initial_size != current_size:
            logger.info(f"File {filename} is still being written, waiting...")
            await asyncio.sleep(FILE_STABILITY_WAIT)
    
    def is_watching(self) -> bool:
        """Check if the watcher is currently running"""
        return self.is_running and self.observer and self.observer.is_alive()
    
    async def ensure_observer_alive(self):
        """Ensure the observer is alive, restart if necessary"""
        if not self.is_running:
            return False
            
        if not self.observer or not self.observer.is_alive():
            logger.warning("🔄 Observer is dead, restarting file watcher...")
            try:
                # Stop the dead observer if it exists
                if self.observer:
                    try:
                        self.observer.stop()
                        self.observer.join(timeout=OBSERVER_JOIN_TIMEOUT)
                    except Exception as e:
                        logger.warning(f"Error stopping dead observer: {e}")
                
                # Create a new observer
                logger.info("Creating new Observer...")
                self.observer = Observer()
                
                # Re-schedule the handler
                logger.info(f"Re-scheduling observer to watch: {self.documents_dir}")
                watch = self.observer.schedule(self.handler, str(self.documents_dir), recursive=False)
                logger.info(f"Watch re-scheduled: {watch}")
                
                # Start the new observer
                logger.info("Starting new observer...")
                self.observer.start()
                
                # Verify it's alive
                if self.observer.is_alive():
                    logger.info("✅ Observer restarted successfully")
                    return True
                else:
                    logger.error("❌ Failed to restart observer - still not alive")
                    return False
                    
            except Exception as e:
                logger.error(f"❌ Failed to restart observer: {e}")
                return False
        
        return True