from typing import List
import time

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

    def embed_chunks(self, chunks: List[Chunk], batch_size=256) -> List[Chunk]:
        texts = [chunk.text for chunk in chunks]
        batch_texts = [texts[i:i + batch_size] for i in range(0, len(texts), batch_size)]
        embeddings = []
        
        total_chunks = len(chunks)
        processed_chunks = 0
        start_time = time.time()
        
        # Log start of embedding process
        if log_available:
            model_name = self.__class__.__name__
            log.color_print(f"🔢 Starting embedding generation for {total_chunks} chunks using {model_name}")
            log.color_print(f"   ↳ Processing in {len(batch_texts)} batches of up to {batch_size} chunks each")
        
        for i, batch_text in enumerate(batch_texts):
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
                log.inline_progress(f"⏳ Embedding: {processed_chunks}/{total_chunks} chunks ({progress_pct:.1f}%) - {chunks_per_sec:.1f} chunks/sec, {remaining/60:.1f} min left")
                
                # Periodically print detailed stats on a new line
                if i % max(1, len(batch_texts)//10) == 0 or i == len(batch_texts) - 1:
                    if i < len(batch_texts) - 1:  # Not the final batch
                        log.color_print(f"   ↳ Batch {i+1}/{len(batch_texts)}: {len(batch_text)} chunks in {batch_time:.2f}s", same_line=False)
        
        # Assign embeddings to chunks
        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding
            
        # Log completion
        if log_available:
            # Add a newline after the progress updates
            print()
            total_time = time.time() - start_time
            log.color_print(f"✅ Embedding complete: {total_chunks} chunks embedded in {total_time/60:.1f} minutes")
            
        return chunks

    @property
    def dimension(self) -> int:
        pass