import json
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import asyncio
import logging
import hashlib
from dataclasses import dataclass, asdict
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import requests
import os

logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    id: str
    document_name: str
    text: str
    embedding: List[float]
    chunk_index: int


@dataclass
class SearchResult:
    text: str
    score: float
    document: str
    chunk_id: str


class EmbeddingService:
    """Local embedding service using Ollama"""
    
    def __init__(self, model: str = "nomic-embed-text:v1.5", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        
        # Optimize HTTP session for performance
        self.session = requests.Session()
        
        # Configure connection pooling and keep-alive
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,  # Number of connection pools
            pool_maxsize=20,      # Max connections per pool
            max_retries=2,        # Retry failed requests
            pool_block=False      # Don't block when pool is full
        )
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set persistent headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Connection': 'keep-alive'
        })
        
        self._model_pulled = False
    
    def ollama_available(self) -> bool:
        """Check if ollama is available"""
        try:
            response = requests.get(self.base_url, timeout=10)
            response.raise_for_status()
            return True
        except Exception:
            return False
    
    async def ensure_model_available(self):
        """Ensure model is pulled (only once)"""
        if self._model_pulled:
            return
            
        try:
            import subprocess
            logger.info(f"Pulling Ollama model {self.model} (one-time setup)...")
            subprocess.run(
                ["ollama", "pull", self.model],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self._model_pulled = True
            logger.info(f"Model {self.model} is ready")
        except Exception as e:
            logger.warning(f"Failed to pull model {self.model}: {e}")
            # Continue anyway - model might already exist

    async def get_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using Ollama"""
        await self.ensure_model_available()
        
        try:
            # Pre-serialize JSON to avoid repeated serialization overhead
            payload = json.dumps({"model": self.model, "prompt": text})
            
            response = self.session.post(
                f"{self.base_url}/api/embeddings",
                data=payload,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            embedding = data.get("embedding")
            if embedding is None or not isinstance(embedding, list):
                raise ValueError(f"No embedding returned from Ollama: {data}")
            return embedding
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Cannot connect to Ollama at {self.base_url}. Is Ollama running?")
            raise ValueError(f"Ollama connection failed. Please ensure Ollama is running at {self.base_url}")
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise

    async def get_embeddings_batch(self, texts: List[str], batch_size: int = 20) -> List[List[float]]:
        """Generate embeddings for multiple texts using true batch processing"""
        await self.ensure_model_available()
        
        if not texts:
            return []
        
        # For small batches, use individual requests with connection reuse
        if len(texts) <= 5:
            tasks = [self.get_embedding(text) for text in texts]
            return await asyncio.gather(*tasks)
        
        # For larger batches, process in chunks to avoid memory issues
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            logger.debug(f"Processing batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size} ({len(batch_texts)} texts)")
            
            # Use concurrent requests with connection reuse - much faster than sequential
            batch_tasks = [self.get_embedding(text) for text in batch_texts]
            batch_embeddings = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Handle any failures gracefully
            valid_embeddings = []
            for j, result in enumerate(batch_embeddings):
                if isinstance(result, Exception):
                    logger.warning(f"Failed to embed text {i+j}: {result}")
                    # Use zero vector as fallback
                    valid_embeddings.append([0.0] * 768)  # nomic-embed-text dimension
                else:
                    valid_embeddings.append(result)
            
            embeddings.extend(valid_embeddings)
            
            # Brief pause between large batches to prevent overwhelming Ollama
            if len(batch_texts) == batch_size and i + batch_size < len(texts):
                await asyncio.sleep(0.05)  # Reduced from 0.1s
        
        return embeddings


class RagEngine:
    """RAG engine for PDF document processing and search"""
    
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.chunks: Dict[str, DocumentChunk] = {}
        self.embedding_service = EmbeddingService()
        
    async def initialize(self):
        """Initialize the RAG engine"""
        await self.load_from_disk()
        
    async def add_document(self, filename: str, data: bytes) -> int:
        """Add a document to the RAG system"""
        logger.info(f"Processing document: {filename}")
        
        # Check if Ollama is available before processing
        if not self.embedding_service.ollama_available():
            raise ValueError("Ollama is not available. Please ensure Ollama is running.")
        
        # Extract text from PDF
        text = self.extract_pdf_text(data)
        if not text.strip():
            raise ValueError("No text extracted from PDF")
        
        # Create chunks
        chunks = self.chunk_text(text, chunk_size=500)
        logger.info(f"Created {len(chunks)} chunks for {filename}")
        
        # Remove existing chunks for this document
        self.chunks = {k: v for k, v in self.chunks.items() 
                      if v.document_name != filename}
        
        # Filter valid chunks
        valid_chunks = [(i, chunk_text) for i, chunk_text in enumerate(chunks) 
                       if len(chunk_text.strip()) >= 10]
        
        if not valid_chunks:
            logger.warning(f"No valid chunks found in {filename}")
            return 0
        
        logger.info(f"Generating embeddings for {len(valid_chunks)} chunks from {filename}...")
        start_time = time.time()
        
        # Extract texts for batch processing
        chunk_texts = [chunk_text for _, chunk_text in valid_chunks]
        
        # Generate embeddings in batches (much faster!)
        embeddings = await self.embedding_service.get_embeddings_batch(chunk_texts, batch_size=20)
        
        embedding_time = time.time() - start_time
        logger.info(f"Generated {len(embeddings)} embeddings in {embedding_time:.2f}s ({len(embeddings)/embedding_time:.1f} embeddings/sec)")
        
        # Create and store chunks
        chunk_count = 0
        for (i, chunk_text), embedding in zip(valid_chunks, embeddings):
            chunk = DocumentChunk(
                id=str(uuid.uuid4()),
                document_name=filename,
                text=chunk_text,
                embedding=embedding,
                chunk_index=i
            )
            
            self.chunks[chunk.id] = chunk
            chunk_count += 1
        
        await self.save_to_disk()
        logger.info(f"Successfully processed {chunk_count} chunks for {filename}")
        return chunk_count

    async def add_document_with_progress(self, filename: str, data: bytes, progress_tracker: dict) -> int:
        """Add a document to the RAG system with progress tracking"""
        logger.info(f"Processing document: {filename}")
        
        # Check if Ollama is available before processing
        if not self.embedding_service.ollama_available():
            raise ValueError("Ollama is not available. Please ensure Ollama is running.")
        
        # Extract text from PDF
        text = self.extract_pdf_text(data)
        if not text.strip():
            raise ValueError("No text extracted from PDF")
        
        # Create chunks
        chunks = self.chunk_text(text, chunk_size=500)
        logger.info(f"Created {len(chunks)} chunks for {filename}")
        
        # Remove existing chunks for this document
        self.chunks = {k: v for k, v in self.chunks.items() 
                      if v.document_name != filename}
        
        # Filter valid chunks
        valid_chunks = [(i, chunk_text) for i, chunk_text in enumerate(chunks) 
                       if len(chunk_text.strip()) >= 10]
        
        if not valid_chunks:
            logger.warning(f"No valid chunks found in {filename}")
            return 0
        
        logger.info(f"Generating embeddings for {len(valid_chunks)} chunks from {filename}...")
        start_time = time.time()
        
        # Extract texts for batch processing
        chunk_texts = [chunk_text for _, chunk_text in valid_chunks]
        
        # Generate embeddings in batches (much faster!)
        embeddings = await self.embedding_service.get_embeddings_batch(chunk_texts, batch_size=20)
        
        embedding_time = time.time() - start_time
        logger.info(f"Generated {len(embeddings)} embeddings in {embedding_time:.2f}s ({len(embeddings)/embedding_time:.1f} embeddings/sec)")
        
        # Create and store chunks
        chunk_count = 0
        for (i, chunk_text), embedding in zip(valid_chunks, embeddings):
            chunk = DocumentChunk(
                id=str(uuid.uuid4()),
                document_name=filename,
                text=chunk_text,
                embedding=embedding,
                chunk_index=i
            )
            
            self.chunks[chunk.id] = chunk
            chunk_count += 1
            
            # Update progress tracker
            progress_tracker["current_file_chunks"] = chunk_count
        
        await self.save_to_disk()
        logger.info(f"Successfully processed {chunk_count} chunks for {filename}")
        return chunk_count
    
    async def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """Search documents using optimized vectorized similarity"""
        if not self.chunks:
            return []
        
        logger.debug(f"Searching for: '{query}' (searching {len(self.chunks)} chunks)")
        start_time = time.time()
        
        # Get query embedding
        query_embedding = await self.embedding_service.get_embedding(query)
        query_array = np.array(query_embedding).reshape(1, -1)
        
        # Prepare chunk data for vectorized operations
        chunks_list = list(self.chunks.values())
        embeddings_matrix = np.array([chunk.embedding for chunk in chunks_list])
        
        # Vectorized cosine similarity calculation (much faster)
        similarities = cosine_similarity(query_array, embeddings_matrix)[0]
        
        # Get top-k indices using numpy's argpartition (more efficient than sorting all)
        if len(similarities) <= top_k:
            top_indices = np.argsort(similarities)[::-1]
        else:
            # Use argpartition for better performance on large datasets
            top_indices = np.argpartition(similarities, -top_k)[-top_k:]
            top_indices = top_indices[np.argsort(similarities[top_indices])[::-1]]
        
        search_time = time.time() - start_time
        logger.debug(f"Search completed in {search_time:.3f}s")
        
        return [
            SearchResult(
                text=chunks_list[idx].text,
                score=float(similarities[idx]),
                document=chunks_list[idx].document_name,
                chunk_id=chunks_list[idx].id
            )
            for idx in top_indices
        ]
    
    def list_documents(self) -> List[str]:
        """List all processed documents"""
        docs = set(chunk.document_name for chunk in self.chunks.values())
        return sorted(list(docs))
    
    def get_stats(self) -> dict:
        """Get RAG system statistics"""
        doc_count = len(self.list_documents())
        chunk_count = len(self.chunks)
        
        return {
            "documents": doc_count,
            "chunks": chunk_count,
            "status": "ready"
        }
    
    async def load_documents_from_dir(self, documents_dir: str):
        """Load all PDFs from a directory"""
        documents_path = Path(documents_dir)
        if not documents_path.exists():
            logger.warning(f"Documents directory does not exist: {documents_dir}")
            return
        
        for pdf_file in documents_path.glob("*.pdf"):
            filename = pdf_file.name
            
            # Skip if already processed
            if any(chunk.document_name == filename for chunk in self.chunks.values()):
                logger.info(f"Document {filename} already processed, skipping")
                continue
            
            try:
                logger.info(f"Loading document: {filename}")
                data = pdf_file.read_bytes()
                chunk_count = await self.add_document(filename, data)
                logger.info(f"Successfully processed {filename} with {chunk_count} chunks")
                
                # Yield control after each document to keep server responsive
                await asyncio.sleep(0.001)
                
            except Exception as e:
                logger.warning(f"Skipping {filename}: {e}")

    async def load_documents_from_dir_with_progress(self, documents_dir: str, progress_tracker: dict):
        """Load all PDFs from a directory with progress tracking"""
        documents_path = Path(documents_dir)
        if not documents_path.exists():
            logger.warning(f"Documents directory does not exist: {documents_dir}")
            return
        
        pdf_files = list(documents_path.glob("*.pdf"))
        progress_tracker["total_files"] = len(pdf_files)
        
        for file_index, pdf_file in enumerate(pdf_files):
            filename = pdf_file.name
            progress_tracker["current_file"] = filename
            progress_tracker["current_file_chunks"] = 0
            
            # Skip if already processed
            if any(chunk.document_name == filename for chunk in self.chunks.values()):
                logger.info(f"Document {filename} already processed, skipping")
                progress_tracker["processed_files"] += 1
                continue
            
            try:
                logger.info(f"Loading document {file_index + 1}/{len(pdf_files)}: {filename}")
                data = pdf_file.read_bytes()
                
                # Process document and track chunks
                chunk_count = await self.add_document_with_progress(filename, data, progress_tracker)
                
                progress_tracker["processed_files"] += 1
                progress_tracker["total_chunks"] += chunk_count
                progress_tracker["current_file_chunks"] = chunk_count
                
                logger.info(f"Successfully processed {filename} with {chunk_count} chunks")
                
                # Yield control after each document
                await asyncio.sleep(0.001)
                
            except Exception as e:
                logger.warning(f"Skipping {filename}: {e}")
                progress_tracker["processed_files"] += 1  # Still count as processed
    
    def extract_pdf_text(self, data: bytes) -> str:
        """Extract text from PDF using pdftotext (poppler)"""
        logger.info("Extracting PDF text using pdftotext")
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(data)
            temp_path = temp_file.name
        
        try:
            # Use pdftotext command
            result = subprocess.run([
                'pdftotext', 
                '-layout', 
                '-enc', 'UTF-8', 
                temp_path, 
                '-'
            ], capture_output=True, text=True, check=True)
            
            text = result.stdout
            if not text.strip():
                raise ValueError("pdftotext produced no text output")
            
            logger.info(f"✅ pdftotext extracted {len(text)} characters")
            return text
            
        except subprocess.CalledProcessError as e:
            logger.warning(f"pdftotext failed: {e.stderr}")
            raise ValueError(f"pdftotext failed: {e.stderr}")
        except FileNotFoundError:
            logger.error("pdftotext not found. Please install poppler-utils")
            raise ValueError("pdftotext command not found. Install with: brew install poppler (macOS) or sudo apt-get install poppler-utils (Linux)")
        finally:
            os.unlink(temp_path)
    
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks for better context preservation"""
        if not text.strip():
            return []
        
        words = text.split()
        if len(words) <= chunk_size:
            return [text] if text.strip() else []
        
        chunks = []
        step_size = chunk_size - overlap
        
        for i in range(0, len(words), step_size):
            chunk_words = words[i:i + chunk_size]
            if len(chunk_words) >= 10:  # Only include meaningful chunks
                chunk_text = " ".join(chunk_words)
                chunks.append(chunk_text)
            
            # Break if we've covered all words
            if i + chunk_size >= len(words):
                break
        
        return chunks
    
    async def save_to_disk(self):
        """Save chunks to disk with optimized I/O"""
        chunks_file = self.data_dir / "chunks.json"
        
        # Use more efficient JSON serialization
        chunks_data = {}
        for k, v in self.chunks.items():
            chunks_data[k] = {
                'id': v.id,
                'document_name': v.document_name,
                'text': v.text,
                'embedding': v.embedding,
                'chunk_index': v.chunk_index
            }
        
        # Write atomically to prevent corruption
        temp_file = chunks_file.with_suffix('.json.tmp')
        try:
            with open(temp_file, 'w', buffering=65536) as f:  # Larger buffer for better I/O
                json.dump(chunks_data, f, separators=(',', ':'))  # Compact JSON
            
            # Atomic rename
            temp_file.replace(chunks_file)
            logger.debug(f"Saved {len(self.chunks)} chunks to disk")
        except Exception as e:
            if temp_file.exists():
                temp_file.unlink()
            raise e
    
    async def load_from_disk(self):
        """Load chunks from disk"""
        chunks_file = self.data_dir / "chunks.json"
        
        if chunks_file.exists():
            try:
                with open(chunks_file, 'r') as f:
                    chunks_data = json.load(f)
                
                # Yield control periodically while loading chunks
                self.chunks = {}
                chunk_count = 0
                for k, v in chunks_data.items():
                    self.chunks[k] = DocumentChunk(**v)
                    chunk_count += 1
                    # Yield control every 50 chunks to keep server responsive
                    if chunk_count % 50 == 0:
                        await asyncio.sleep(0.001)  # Very short sleep to yield control
                
                logger.info(f"Loaded {len(self.chunks)} chunks from disk")
            except Exception as e:
                logger.warning(f"Failed to load chunks from disk: {e}")
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if len(a) != len(b):
            return 0.0
        
        # Convert to numpy arrays for efficient computation
        a_arr = np.array(a).reshape(1, -1)
        b_arr = np.array(b).reshape(1, -1)
        
        # Handle zero vectors
        if np.linalg.norm(a_arr) == 0 or np.linalg.norm(b_arr) == 0:
            return 0.0
        
        return cosine_similarity(a_arr, b_arr)[0][0]