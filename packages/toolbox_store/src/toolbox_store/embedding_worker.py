import threading

from loguru import logger

from toolbox_store.store import ToolboxStore


class EmbeddingWorker:
    def __init__(
        self,
        store: ToolboxStore,
        sleep_interval: int = 5,
        page_size: int = 32,
    ):
        self.store = store
        self.sleep_interval = sleep_interval
        self.page_size = page_size
        self.running = False
        self._thread = None
        self._stop_event = threading.Event()

    def run(self) -> None:
        self.running = True
        self._stop_event.clear()
        logger.info("Starting embedding worker...")

        while self.running:
            try:
                if self._stop_event.wait(timeout=0.1):
                    break

                docs = self.store.db.get_docs_without_embeddings(limit=self.page_size)
                if not docs:
                    logger.debug("No documents without embeddings found, sleeping...")
                    if self._stop_event.wait(timeout=self.sleep_interval):
                        break
                    continue

                try:
                    embedded_chunks = self.store.embed_documents(docs)
                    self.store.insert_chunks(embedded_chunks)
                    logger.debug(
                        f"Successfully embedded {len(embedded_chunks)} chunks from {len(docs)} documents"
                    )
                except Exception as e:
                    logger.error(f"Error embedding documents: {e}")

                if self._stop_event.wait(timeout=self.sleep_interval):
                    break

            except Exception as e:
                logger.error(f"Error in embedding worker: {e}")
                if self._stop_event.wait(timeout=self.sleep_interval):
                    break

        logger.info("Embedding worker stopped")

    def run_in_thread(self) -> threading.Thread:
        """Start the worker in a background thread."""
        if self._thread and self._thread.is_alive():
            logger.warning("Worker thread is already running")
            return self._thread

        self._thread = threading.Thread(target=self.run, daemon=True)
        self._thread.start()
        logger.info("Embedding worker thread started")
        return self._thread

    def stop(self, timeout: float = 5.0) -> None:
        """Stop the worker gracefully."""
        if not self.running:
            logger.debug("Worker is not running")
            return

        logger.info("Stopping embedding worker...")
        self.running = False
        self._stop_event.set()

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=timeout)
            if self._thread.is_alive():
                logger.warning(f"Worker thread did not stop within {timeout} seconds")
            else:
                logger.info("Worker thread stopped successfully")

        self._thread = None
