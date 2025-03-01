from typing import List
import time
import os

from tqdm import tqdm

from deepsearcher.loader.splitter import Chunk
try:
    from deepsearcher.tools import log
    log_available = True
except ImportError:
    log_available = False


class BaseEmbedding:
    def embed_query(self, text: str) -> List[float]:
        pass
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_query(text) for text in texts]

    def embed_chunks(self, chunks: List[Chunk], batch_size=64, task_id="default") -> List[Chunk]:
        # Adjust batch size based on environment
        in_docker = os.path.exists('/.dockerenv')
        
        # In Docker, use a smaller default batch size (32) for stability
        # Outside of Docker, use a larger batch size (64) for performance
        if in_docker:
            default_batch_size = 32
            if batch_size > default_batch_size:
                if log_available:
                    log.color_print(f"🐳 Docker environment detected, using conservative batch size of {default_batch_size}",
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