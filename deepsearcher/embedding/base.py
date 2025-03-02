from typing import List
import time
import os
import queue
import threading
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, as_completed
import psutil

from tqdm import tqdm

from deepsearcher.loader.splitter import Chunk
try:
    from deepsearcher.tools import log
    log_available = True
except ImportError:
    log_available = False


class BaseEmbedding:
    # Class-level embedding queue for background processing
    embedding_queue = None
    embedding_worker_thread = None
    embedding_worker_running = False
    
    def __init__(self):
        # Initialize with default values
        self._max_parallel_workers = 4
    
    def embed_query(self, text: str) -> List[float]:
        pass
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_query(text) for text in texts]
        
    def get_optimal_batch_size(self) -> int:
        """
        Dynamically determine the optimal batch size based on available system resources.
        Returns a batch size that's appropriate for the current environment.
        """
        try:
            # Check if we're in Docker
            in_docker = os.path.exists('/.dockerenv')
            
            # Get available memory in MB
            available_memory = psutil.virtual_memory().available / (1024 * 1024)
            
            # Get CPU count
            cpu_count = multiprocessing.cpu_count()
            
            if in_docker:
                # More conservative in Docker environments
                if available_memory < 1000:  # Less than 1GB
                    return max(16, min(32, int(available_memory / 30)))
                elif available_memory < 2000:  # Less than 2GB
                    return 48
                else:
                    return 64
            else:
                # More aggressive outside Docker
                if available_memory < 2000:  # Less than 2GB
                    return 64
                elif available_memory < 4000:  # Less than 4GB
                    return 96
                else:
                    return 128
        except Exception as e:
            # Fall back to default if there's any error
            if log_available:
                log.color_print(f"⚠️ Error determining optimal batch size: {str(e)}", progress_type="warning")
            return 64
            
    def get_optimal_worker_count(self) -> int:
        """
        Determine the optimal number of parallel workers based on system resources.
        """
        try:
            cpu_count = multiprocessing.cpu_count()
            in_docker = os.path.exists('/.dockerenv')
            
            if in_docker:
                # More conservative in Docker
                return max(2, min(4, cpu_count - 1))
            else:
                # More aggressive outside Docker
                return max(2, min(8, cpu_count - 1))
        except Exception as e:
            # Fall back to default
            if log_available:
                log.color_print(f"⚠️ Error determining optimal worker count: {str(e)}", progress_type="warning")
            return 4

    def embed_chunks_parallel(self, chunks: List[Chunk], batch_size=None, max_workers=None, task_id="default") -> List[Chunk]:
        """
        Embed chunks using parallel processing to speed up embedding generation.
        
        Args:
            chunks: List of chunks to embed
            batch_size: Size of batches to process (if None, will use optimal size)
            max_workers: Number of parallel workers (if None, will use optimal count)
            task_id: Task ID for logging
            
        Returns:
            List of chunks with embeddings
        """
        # Use optimal settings if not specified
        if batch_size is None:
            batch_size = self.get_optimal_batch_size()
            
        if max_workers is None:
            max_workers = self.get_optimal_worker_count()
            
        # Check if we're in Docker for logging
        in_docker = os.path.exists('/.dockerenv')
        
        texts = [chunk.text for chunk in chunks]
        batch_texts = [texts[i:i + batch_size] for i in range(0, len(texts), batch_size)]
        
        total_chunks = len(chunks)
        processed_chunks = 0
        start_time = time.time()
        
        # Log start of embedding process
        if log_available:
            model_name = self.__class__.__name__
            log.color_print(f"🔢 Starting parallel embedding generation for {total_chunks} chunks using {model_name}",
                           task_id=task_id, progress_type="embedding")
            log.color_print(f"   ↳ Processing in {len(batch_texts)} batches with {max_workers} parallel workers",
                           task_id=f"{task_id}_detail", progress_type="embedding")
            log.color_print(f"   ↳ Batch size: {batch_size} chunks per batch", 
                           task_id=f"{task_id}_batch_size", progress_type="embedding")
        
        # Prepare result container
        all_embeddings = []
        
        # Process batches in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all jobs
            future_to_batch = {executor.submit(self.embed_documents, batch): (i, batch) 
                             for i, batch in enumerate(batch_texts)}
            
            # Process results as they complete
            for future in as_completed(future_to_batch):
                batch_idx, batch_text = future_to_batch[future]
                try:
                    # Get the results
                    batch_embeddings = future.result()
                    
                    # Store with batch index for proper ordering later
                    all_embeddings.append((batch_idx, batch_embeddings))
                    processed_chunks += len(batch_text)
                    
                    # Update progress
                    if log_available:
                        progress_pct = (processed_chunks / total_chunks) * 100
                        elapsed = time.time() - start_time
                        chunks_per_sec = processed_chunks / max(1, elapsed)
                        estimated_total = (total_chunks / max(1, processed_chunks)) * elapsed
                        remaining = max(0, estimated_total - elapsed)
                        
                        log.inline_progress(
                            f"⏳ Embedding: {processed_chunks}/{total_chunks} chunks ({progress_pct:.1f}%) - {chunks_per_sec:.1f} chunks/sec, {remaining/60:.1f} min left",
                            task_id=task_id,
                            progress_type="embedding"
                        )
                        
                        # Print detailed stats periodically
                        if batch_idx % max(1, len(batch_texts)//10) == 0:
                            log.color_print(
                                f"   ↳ Completed batch {batch_idx+1}/{len(batch_texts)}: {len(batch_text)} chunks", 
                                same_line=False,
                                task_id=f"{task_id}_batch",
                                progress_type="embedding"
                            )
                except Exception as e:
                    if log_available:
                        log.color_print(
                            f"❌ Error embedding batch {batch_idx+1}: {str(e)}", 
                            same_line=False,
                            task_id=f"{task_id}_error",
                            progress_type="error"
                        )
                        
                        # Add placeholder embeddings
                        placeholder_dim = 1536  # Default dimension
                        if any(len(embs[1]) > 0 for embs in all_embeddings if len(embs) > 1):
                            # Find a previous successful batch to determine dimension
                            for idx, embs in all_embeddings:
                                if embs and len(embs) > 0 and len(embs[0]) > 0:
                                    placeholder_dim = len(embs[0])
                                    break
                        
                        batch_embeddings = [[0.0] * placeholder_dim for _ in range(len(batch_text))]
                        all_embeddings.append((batch_idx, batch_embeddings))
                        processed_chunks += len(batch_text)
                        
                        log.color_print(
                            f"⚠️ Added placeholder embeddings for batch {batch_idx+1}", 
                            same_line=False,
                            task_id=f"{task_id}_warning",
                            progress_type="warning"
                        )
                        
                        # Force garbage collection
                        import gc
                        gc.collect()
        
        # Sort results by batch index to maintain original order
        all_embeddings.sort(key=lambda x: x[0])
        
        # Flatten embeddings list
        embeddings = []
        for _, batch_embs in all_embeddings:
            embeddings.extend(batch_embs)
        
        # Assign embeddings to chunks
        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding
        
        # Log completion
        if log_available:
            print()  # Add a newline
            total_time = time.time() - start_time
            chunks_per_sec = total_chunks / max(1, total_time)
            log.color_print(
                f"✅ Parallel embedding complete: {total_chunks} chunks embedded in {total_time/60:.1f} minutes ({chunks_per_sec:.1f} chunks/sec)",
                task_id=task_id,
                progress_type="embedding"
            )
        
        return chunks

    @classmethod
    def start_embedding_worker(cls, vector_db, collection_name, task_id="default"):
        """
        Start a background worker to process embeddings from the queue.
        
        Args:
            vector_db: Vector database instance to store embeddings
            collection_name: Collection name to store embeddings in
            task_id: Task ID for logging
        """
        if cls.embedding_worker_running:
            if log_available:
                log.color_print("⚠️ Embedding worker already running", task_id=task_id, progress_type="warning")
            return
        
        # Initialize queue if not already done
        if cls.embedding_queue is None:
            cls.embedding_queue = queue.Queue()
        
        # Define worker function
        def worker_function():
            if log_available:
                log.color_print("🔄 Starting background embedding worker", task_id=f"{task_id}_worker", progress_type="embedding")
            
            while cls.embedding_worker_running:
                try:
                    # Get batch from queue with timeout
                    batch_info = cls.embedding_queue.get(timeout=5)
                    
                    # Check for termination signal
                    if batch_info is None:
                        break
                    
                    embedding_model, batch_chunks, batch_task_id = batch_info
                    
                    if log_available:
                        log.color_print(f"🔢 Worker processing {len(batch_chunks)} chunks", 
                                      task_id=f"{task_id}_worker", progress_type="embedding")
                    
                    # Embed chunks
                    embedded_chunks = embedding_model.embed_chunks_parallel(
                        batch_chunks, 
                        task_id=f"{batch_task_id}_worker"
                    )
                    
                    # Insert into vector database
                    if log_available:
                        log.color_print(f"💾 Worker inserting {len(embedded_chunks)} chunks into '{collection_name}'", 
                                      task_id=f"{task_id}_worker", progress_type="storing")
                    
                    vector_db.insert_data(collection=collection_name, chunks=embedded_chunks)
                    
                    if log_available:
                        log.color_print(f"✅ Worker completed batch of {len(embedded_chunks)} chunks", 
                                      task_id=f"{task_id}_worker", progress_type="complete")
                    
                    # Mark task as done
                    cls.embedding_queue.task_done()
                    
                except queue.Empty:
                    # Just continue looping
                    continue
                except Exception as e:
                    if log_available:
                        log.color_print(f"❌ Worker error: {str(e)}", 
                                      task_id=f"{task_id}_worker_error", progress_type="error")
                    
                    # Don't want to crash the worker thread
                    import traceback
                    if log_available:
                        log.color_print(f"Traceback: {traceback.format_exc()}", 
                                      task_id=f"{task_id}_worker_trace", progress_type="error")
                    
                    # Mark task as done even if it failed
                    try:
                        cls.embedding_queue.task_done()
                    except:
                        pass
        
        # Start worker thread
        cls.embedding_worker_running = True
        cls.embedding_worker_thread = threading.Thread(target=worker_function, daemon=True)
        cls.embedding_worker_thread.start()
        
        if log_available:
            log.color_print("✅ Background embedding worker started", task_id=task_id, progress_type="embedding")
    
    @classmethod
    def stop_embedding_worker(cls, task_id="default", wait=True):
        """
        Stop the background embedding worker.
        
        Args:
            task_id: Task ID for logging
            wait: If True, wait for queue to complete before stopping
        """
        if not cls.embedding_worker_running:
            return
        
        if wait and cls.embedding_queue:
            if log_available:
                log.color_print("⏳ Waiting for embedding queue to complete before stopping worker", 
                              task_id=task_id, progress_type="embedding")
            cls.embedding_queue.join()
        
        # Signal worker to stop
        cls.embedding_worker_running = False
        if cls.embedding_queue:
            cls.embedding_queue.put(None)
        
        # Wait for worker to finish
        if cls.embedding_worker_thread:
            cls.embedding_worker_thread.join(timeout=5)
            cls.embedding_worker_thread = None
        
        if log_available:
            log.color_print("✅ Background embedding worker stopped", task_id=task_id, progress_type="embedding")
    
    @classmethod
    def queue_chunks_for_embedding(cls, embedding_model, chunks, task_id="default"):
        """
        Queue chunks for background embedding processing.
        
        Args:
            embedding_model: The embedding model to use
            chunks: Chunks to embed
            task_id: Task ID for logging
        """
        if not cls.embedding_worker_running:
            if log_available:
                log.color_print("⚠️ Embedding worker not running, chunks will not be processed",
                              task_id=task_id, progress_type="warning")
            return False
        
        if log_available:
            log.color_print(f"📤 Queuing {len(chunks)} chunks for background embedding", 
                          task_id=task_id, progress_type="embedding")
        
        cls.embedding_queue.put((embedding_model, chunks, task_id))
        return True

    def embed_chunks(self, chunks: List[Chunk], batch_size=64, task_id="default") -> List[Chunk]:
        """
        Original (sequential) implementation of embed_chunks.
        Consider using embed_chunks_parallel for better performance.
        """
        # Adjust batch size based on environment
        in_docker = os.path.exists('/.dockerenv')
        
        # In Docker, use a moderate batch size (64) to balance performance and stability
        # We've found 64 to be a good compromise between performance and reliability
        if in_docker:
            default_batch_size = 64
            if batch_size != default_batch_size:
                if log_available:
                    log.color_print(f"🐳 Docker environment detected, using balanced batch size of {default_batch_size}",
                                   task_id=task_id, progress_type="embedding")
                batch_size = default_batch_size
            
        texts = [chunk.text for chunk in chunks]
        batch_texts = [texts[i:i + batch_size] for i in range(0, len(texts), batch_size)]
        embeddings = []
        
        total_chunks = len(chunks)
        processed_chunks = 0
        start_time = time.time()
        
        # Log start of embedding process
        if log_available:
            model_name = self.__class__.__name__
            log.color_print(f"🔢 Starting embedding generation for {total_chunks} chunks using {model_name}",
                           task_id=task_id, progress_type="embedding")
            log.color_print(f"   ↳ Processing in {len(batch_texts)} batches of up to {batch_size} chunks each",
                           task_id=f"{task_id}_detail", progress_type="embedding")
        
        for i, batch_text in enumerate(batch_texts):
            try:
                batch_start = time.time()
                batch_embeddings = self.embed_documents(batch_text)
                batch_time = time.time() - batch_start
                
                embeddings.extend(batch_embeddings)
                processed_chunks += len(batch_text)
                
                # Update progress inline
                if log_available:
                    progress_pct = (processed_chunks / total_chunks) * 100
                    elapsed = time.time() - start_time
                    chunks_per_sec = processed_chunks / max(1, elapsed)
                    estimated_total = (total_chunks / max(1, processed_chunks)) * elapsed
                    remaining = max(0, estimated_total - elapsed)
                    
                    # Always update the progress line
                    log.inline_progress(
                        f"⏳ Embedding: {processed_chunks}/{total_chunks} chunks ({progress_pct:.1f}%) - {chunks_per_sec:.1f} chunks/sec, {remaining/60:.1f} min left",
                        task_id=task_id,
                        progress_type="embedding"
                    )
                    
                    # Periodically print detailed stats on a new line
                    if i % max(1, len(batch_texts)//10) == 0 or i == len(batch_texts) - 1:
                        if i < len(batch_texts) - 1:  # Not the final batch
                            log.color_print(
                                f"   ↳ Batch {i+1}/{len(batch_texts)}: {len(batch_text)} chunks in {batch_time:.2f}s", 
                                same_line=False,
                                task_id=f"{task_id}_batch",
                                progress_type="embedding"
                            )
            except Exception as e:
                if log_available:
                    log.color_print(
                        f"❌ Error embedding batch {i+1}: {str(e)}", 
                        same_line=False,
                        task_id=f"{task_id}_error",
                        progress_type="error"
                    )
                    # Try to continue with the next batch rather than failing completely
                    # Add placeholder embeddings for the failed batch (zeros)
                    placeholder_dim = 1536  # Default dimension, should be overridden by actual embeddings later
                    if embeddings and len(embeddings) > 0:
                        placeholder_dim = len(embeddings[0])  # Use dimension from previous successful embeddings
                    
                    # Add placeholder embeddings (zeros) for the failed batch
                    batch_embeddings = [[0.0] * placeholder_dim for _ in range(len(batch_text))]
                    embeddings.extend(batch_embeddings)
                    processed_chunks += len(batch_text)
                    log.color_print(
                        f"⚠️ Added placeholder embeddings for batch {i+1} due to error", 
                        same_line=False,
                        task_id=f"{task_id}_warning",
                        progress_type="warning"
                    )
                    
                    # Try to force garbage collection to free memory
                    import gc
                    gc.collect()
        
        # Assign embeddings to chunks
        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding
            
        # Log completion
        if log_available:
            # Add a newline after the progress updates
            print()
            total_time = time.time() - start_time
            log.color_print(
                f"✅ Embedding complete: {total_chunks} chunks embedded in {total_time/60:.1f} minutes",
                task_id=task_id,
                progress_type="embedding"
            )
            
        return chunks

    @property
    def dimension(self) -> int:
        pass