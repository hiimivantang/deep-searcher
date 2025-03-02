import os
import time
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Union, Tuple

from tqdm import tqdm
import sys

from deepsearcher.loader.splitter import split_docs_to_chunks
from deepsearcher.tools import log
from deepsearcher.embedding.base import BaseEmbedding

# from deepsearcher.configuration import embedding_model, vector_db, file_loader
from deepsearcher import configuration

# Get document batch size from environment variable or use default of 10
DEFAULT_DOC_BATCH_SIZE = 10
DOC_BATCH_SIZE = int(os.environ.get("DEEPSEARCHER_DOC_BATCH_SIZE", DEFAULT_DOC_BATCH_SIZE))

# Get flag for using parallel embedding from environment
USE_PARALLEL_EMBEDDING = os.environ.get("DEEPSEARCHER_PARALLEL_EMBEDDING", "true").lower() in ("true", "1", "yes", "y")

# Get flag for using background worker from environment
USE_BACKGROUND_WORKER = os.environ.get("DEEPSEARCHER_BACKGROUND_WORKER", "true").lower() in ("true", "1", "yes", "y")


def _load_single_path(path: str, file_loader) -> List:
    if os.path.isdir(path):
        return file_loader.load_directory(path)
    else:
        return file_loader.load_file(path)


def load_from_local_files(
    paths_or_directory: Union[str, List[str]],
    collection_name: str = None,
    collection_description: str = None,
    force_new_collection: bool = False,
    chunk_size=1500,
    chunk_overlap=100,
    max_workers=None,  # Uses CPU count by default
    doc_batch_size=None,  # Number of documents to process in each batch
):
    """
    Load documents from local files, process them in batches, and store in vector database.
    
    Args:
        paths_or_directory: Path(s) to file(s) or directory/directories to load
        collection_name: Name of vector database collection to store documents in
        collection_description: Description of the collection
        force_new_collection: If True, will drop existing collection with same name
        chunk_size: Size of text chunks for splitting documents
        chunk_overlap: Overlap between chunks
        max_workers: Number of workers for parallel processing of files
        doc_batch_size: Number of documents to process in each batch for streaming insertion
                       (smaller batches use less memory but may be slower)
                       If None, uses the DEEPSEARCHER_DOC_BATCH_SIZE environment variable or defaults to 10
    """
    # Enable progress logging regardless of dev mode
    log.set_dev_mode(True)
    
    # Generate a unique task ID for tracking progress
    task_id = f"files_{int(time.time())}"
    
    # Set default max_workers to CPU count minus 1
    cpu_count = multiprocessing.cpu_count()
    default_workers = max(1, cpu_count - 1)
    
    # Check if we're in Docker - if so, be more conservative with resources
    in_docker = os.path.exists('/.dockerenv')
    if max_workers is None:
        max_workers = default_workers
        if in_docker:
            log.color_print(f"🐳 Docker environment detected, using {max_workers} workers (1 less than {cpu_count} CPU cores)", task_id=task_id)
    
    log.color_print(f"🔄 Starting data loading process...", task_id=task_id)
    
    vector_db = configuration.vector_db
    if collection_name is None:
        collection_name = vector_db.default_collection
    collection_name = collection_name.replace(" ", "_").replace("-", "_")
    embedding_model = configuration.embedding_model
    file_loader = configuration.file_loader
    
    log.color_print(f"✅ Initializing vector database collection: {collection_name}", task_id=task_id)
    vector_db.init_collection(
        dim=embedding_model.dimension,
        collection=collection_name,
        description=collection_description,
        force_new_collection=force_new_collection,
    )
    
    # Start background worker if enabled
    if USE_BACKGROUND_WORKER:
        log.color_print(f"🚀 Starting background embedding worker...", task_id=task_id)
        BaseEmbedding.start_embedding_worker(vector_db, collection_name, task_id=task_id)
    if isinstance(paths_or_directory, str):
        paths_or_directory = [paths_or_directory]
    
    # Get all file paths first, expanding directories
    log.color_print(f"🔍 Scanning for files to process...", task_id=task_id)
    all_file_paths = []
    supported_files_count = 0
    unsupported_files_count = 0
    
    for path in paths_or_directory:
        # Check if path exists
        if not os.path.exists(path):
            log.color_print(f"⚠️ Warning: Path does not exist: {path}")
            continue
            
        if os.path.isdir(path):
            # Check if directory is empty
            files = os.listdir(path)
            if not files:
                log.color_print(f"⚠️ Warning: Directory is empty: {path}")
                continue
                
            log.color_print(f"📂 Scanning directory: {path} ({len(files)} items found)")
            
            # Check for supported files in directory
            has_supported_files = False
            dir_supported_count = 0
            
            for file in files:
                file_path = os.path.join(path, file)
                file_ext = os.path.splitext(file)[1].lower().lstrip('.')
                if os.path.isfile(file_path) and (file_ext in file_loader.supported_file_types or 
                                                 any(file.endswith(f".{suffix}") for suffix in file_loader.supported_file_types)):
                    all_file_paths.append(file_path)
                    has_supported_files = True
                    dir_supported_count += 1
                    supported_files_count += 1
                elif os.path.isfile(file_path):
                    unsupported_files_count += 1
            
            log.color_print(f"   ↳ Found {dir_supported_count} supported files in {path}")
                    
            if not has_supported_files:
                log.color_print(f"⚠️ Warning: No supported files found in directory: {path}")
                log.color_print(f"   ↳ Supported file types: {', '.join(file_loader.supported_file_types)}")
        else:
            # Check if file type is supported
            file_ext = os.path.splitext(path)[1].lower().lstrip('.')
            if file_ext in file_loader.supported_file_types or any(path.endswith(f".{suffix}") for suffix in file_loader.supported_file_types):
                all_file_paths.append(path)
                supported_files_count += 1
                log.color_print(f"📄 Found supported file: {path}")
            else:
                log.color_print(f"⚠️ Warning: Unsupported file type: {path}")
                log.color_print(f"   ↳ Supported file types: {', '.join(file_loader.supported_file_types)}")
                unsupported_files_count += 1
                
    # Check if we found any files to process
    if not all_file_paths:
        log.color_print("❌ Error: No valid files found to process")
        return
    
    log.color_print(f"📊 File scan complete: {supported_files_count} supported files found, {unsupported_files_count} unsupported files skipped")
    
    # Use multiprocessing for file loading
    log.color_print(f"📚 Starting file loading with {max_workers if max_workers else multiprocessing.cpu_count() - 1} workers...", task_id=task_id, progress_type="loading")
    
    # Add status message for number of files
    log.color_print(f"📚 Found {len(all_file_paths)} files to process", task_id=f"{task_id}_count", progress_type="loading")
    
    all_docs = []
    if max_workers is None:
        max_workers = max(1, multiprocessing.cpu_count() - 1)  # Leave one core free
    
    success_count = 0
    error_count = 0
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(file_loader.load_file, path): path 
                  for path in all_file_paths}
        
        total_files = len(futures)
        completed = 0
        
        # Initial progress message
        log.inline_progress(f"📚 Loading files: 0/{total_files} (0%)", task_id=task_id, progress_type="loading")
        
        for i, future in enumerate(as_completed(futures)):
            try:
                docs = future.result()
                path = futures[future]
                if docs is not None:
                    doc_count = len(docs)
                    all_docs.extend(docs)
                    success_count += 1
                    completed += 1
                    
                    # Update progress inline
                    progress_pct = (completed / total_files) * 100
                    log.inline_progress(f"📚 Loading files: {completed}/{total_files} ({progress_pct:.1f}%)", task_id=task_id, progress_type="loading")
                    
                    # Additional details for periodic detailed updates
                    if i % 10 == 0 or i == total_files - 1:  # Less frequent detailed updates
                        log.color_print(f"✅ Loaded file: {path} ({doc_count} documents)", same_line=False, task_id=f"{task_id}_details")
                else:
                    path = futures[future]
                    error_count += 1
                    completed += 1
                    
                    # Update progress inline
                    progress_pct = (completed / total_files) * 100
                    log.inline_progress(f"📚 Loading files: {completed}/{total_files} ({progress_pct:.1f}%)")
                    
                    # Print error on new line
                    log.color_print(f"⚠️ Warning: No documents returned for {path}", same_line=False)
            except Exception as e:
                path = futures[future]
                error_count += 1
                completed += 1
                
                # Update progress inline
                progress_pct = (completed / total_files) * 100
                log.inline_progress(f"📚 Loading files: {completed}/{total_files} ({progress_pct:.1f}%)")
                
                # Print error on new line
                log.color_print(f"❌ Error loading {path}: {e}", same_line=False)
        
        # End progress with a newline
        print()
    
    # Handle case where no documents were loaded
    if not all_docs:
        log.color_print("❌ No documents were successfully loaded. Please check file formats and paths.")
        return
    
    total_docs = len(all_docs)
    log.color_print(f"📊 File loading complete: {success_count} files loaded successfully, {error_count} files failed")
    log.color_print(f"📄 Total documents extracted: {total_docs}")
    
    # Process documents in batches for streaming insertion
    # Use the provided batch size or the global default from environment variable
    batch_size = doc_batch_size if doc_batch_size is not None else DOC_BATCH_SIZE
    doc_batches = [all_docs[i:i + batch_size] for i in range(0, len(all_docs), batch_size)]
    
    total_chunks_processed = 0
    batch_count = len(doc_batches)
    
    log.color_print(f"🔄 Processing {total_docs} documents in {batch_count} batches (batch size: {batch_size})...",
                    task_id=task_id, progress_type="processing")
    
    for batch_idx, doc_batch in enumerate(doc_batches):
        batch_docs_count = len(doc_batch)
        
        # Log batch progress
        log.color_print(f"⏱️ Processing batch {batch_idx+1}/{batch_count} ({batch_docs_count} documents)...",
                       task_id=f"{task_id}_batch_{batch_idx}", progress_type="processing")
        
        # 1. Split batch documents into chunks
        log.color_print(f"✂️ Splitting batch {batch_idx+1} documents into chunks (size: {chunk_size}, overlap: {chunk_overlap})...",
                       task_id=f"{task_id}_split_{batch_idx}", progress_type="chunking")
        
        batch_chunks = split_docs_to_chunks(
            doc_batch,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            task_id=f"{task_id}_split_{batch_idx}"
        )
        
        batch_chunk_count = len(batch_chunks)
        log.color_print(f"🧩 Created {batch_chunk_count} chunks from batch {batch_idx+1} documents",
                       task_id=f"{task_id}_split_{batch_idx}", progress_type="chunking")
        
        # 2. Process batch chunks based on configuration
        if batch_chunk_count > 0:
            if USE_BACKGROUND_WORKER:
                # Queue chunks for background processing
                log.color_print(f"📤 Queuing {batch_chunk_count} chunks for background processing...",
                               task_id=f"{task_id}_queue_{batch_idx}", progress_type="embedding")
                
                queued = BaseEmbedding.queue_chunks_for_embedding(
                    embedding_model, 
                    batch_chunks, 
                    task_id=f"{task_id}_embed_{batch_idx}"
                )
                
                if queued:
                    log.color_print(f"✅ Successfully queued {batch_chunk_count} chunks for background processing",
                                   task_id=f"{task_id}_queue_{batch_idx}", progress_type="embedding")
                else:
                    # Fall back to parallel embedding if queuing fails
                    log.color_print(f"⚠️ Background worker not available, falling back to parallel embedding",
                                   task_id=f"{task_id}_fallback_{batch_idx}", progress_type="warning")
                    
                    log.color_print(f"🔢 Generating embeddings for {batch_chunk_count} chunks using parallel processing...",
                                   task_id=f"{task_id}_embed_{batch_idx}", progress_type="embedding")
                    
                    embedded_chunks = embedding_model.embed_chunks_parallel(
                        batch_chunks, 
                        task_id=f"{task_id}_embed_{batch_idx}"
                    )
                    
                    log.color_print(f"💾 Inserting {batch_chunk_count} chunks into vector database...",
                                   task_id=f"{task_id}_insert_{batch_idx}", progress_type="storing")
                    
                    vector_db.insert_data(collection=collection_name, chunks=embedded_chunks)
            elif USE_PARALLEL_EMBEDDING:
                # Use parallel embedding
                log.color_print(f"🔢 Generating embeddings for {batch_chunk_count} chunks using parallel processing...",
                               task_id=f"{task_id}_embed_{batch_idx}", progress_type="embedding")
                
                embedded_chunks = embedding_model.embed_chunks_parallel(
                    batch_chunks, 
                    task_id=f"{task_id}_embed_{batch_idx}"
                )
                
                # Insert chunks
                log.color_print(f"💾 Inserting {batch_chunk_count} chunks into vector database collection '{collection_name}'...",
                               task_id=f"{task_id}_insert_{batch_idx}", progress_type="storing")
                
                vector_db.insert_data(collection=collection_name, chunks=embedded_chunks)
            else:
                # Use standard embedding
                log.color_print(f"🔢 Generating embeddings for {batch_chunk_count} chunks using {embedding_model.__class__.__name__}...",
                               task_id=f"{task_id}_embed_{batch_idx}", progress_type="embedding")
                
                embedded_chunks = embedding_model.embed_chunks(batch_chunks, task_id=f"{task_id}_embed_{batch_idx}")
                
                # Insert chunks
                log.color_print(f"💾 Inserting {batch_chunk_count} chunks into vector database collection '{collection_name}'...",
                               task_id=f"{task_id}_insert_{batch_idx}", progress_type="storing")
                
                vector_db.insert_data(collection=collection_name, chunks=embedded_chunks)
            
            total_chunks_processed += batch_chunk_count
            
            # Log progress after each batch
            progress_pct = ((batch_idx + 1) / batch_count) * 100
            log.color_print(f"✅ Batch {batch_idx+1}/{batch_count} complete: {batch_chunk_count} chunks processed ({progress_pct:.1f}% total)",
                           task_id=f"{task_id}_progress", progress_type="progress")
    
    # Clean up the background worker if it was used
    if USE_BACKGROUND_WORKER:
        log.color_print(f"⏳ Waiting for background worker to complete...", task_id=task_id, progress_type="cleanup")
        BaseEmbedding.stop_embedding_worker(task_id=task_id, wait=True)
    
    # Final completion message
    log.color_print(f"🎉 Data loading complete! {total_chunks_processed} chunks successfully stored in collection '{collection_name}'",
                   task_id=task_id, progress_type="complete")
    
    # Reset dev mode to original setting
    log.set_dev_mode(False)


def load_from_website(
    urls: Union[str, List[str]],
    collection_name: str = None,
    collection_description: str = None,
    force_new_collection: bool = False,
    doc_batch_size=None,  # Number of documents to process in each batch
):
    """
    Load documents from websites, process them in batches, and store in vector database.
    
    Args:
        urls: URL(s) to crawl and load
        collection_name: Name of vector database collection to store documents in
        collection_description: Description of the collection
        force_new_collection: If True, will drop existing collection with same name
        doc_batch_size: Number of documents to process in each batch for streaming insertion
                       (smaller batches use less memory but may be slower)
                       If None, uses the DEEPSEARCHER_DOC_BATCH_SIZE environment variable or defaults to 10
    """
    # Enable progress logging regardless of dev mode
    log.set_dev_mode(True)
    
    # Generate a task_id for this web processing job
    task_id = f"web_{int(time.time())}"
    
    log.color_print(f"🔄 Starting website loading process...", task_id=task_id)
    
    if isinstance(urls, str):
        urls = [urls]
    vector_db = configuration.vector_db
    embedding_model = configuration.embedding_model
    web_crawler = configuration.web_crawler

    if collection_name is None:
        collection_name = vector_db.default_collection
    collection_name = collection_name.replace(" ", "_").replace("-", "_")
    
    log.color_print(f"✅ Initializing vector database collection: {collection_name}", task_id=task_id)
    vector_db.init_collection(
        dim=embedding_model.dimension,
        collection=collection_name,
        description=collection_description,
        force_new_collection=force_new_collection,
    )
    
    # Start background worker if enabled
    if USE_BACKGROUND_WORKER:
        log.color_print(f"🚀 Starting background embedding worker...", task_id=task_id)
        BaseEmbedding.start_embedding_worker(vector_db, collection_name, task_id=task_id)

    log.color_print(f"🌐 Crawling {len(urls)} websites using {web_crawler.__class__.__name__}...")
    all_docs = []
    success_count = 0
    error_count = 0
    
    for i, url in enumerate(tqdm(urls, desc="Loading from websites")):
        log.color_print(f"🔍 Crawling website {i+1}/{len(urls)}: {url}")
        try:
            docs = web_crawler.crawl_url(url)
            if docs:
                page_count = len(docs)
                all_docs.extend(docs)
                success_count += 1
                log.color_print(f"✅ Successfully crawled {url} ({page_count} pages/documents extracted)")
            else:
                error_count += 1
                log.color_print(f"⚠️ Warning: No content extracted from {url}")
        except Exception as e:
            error_count += 1
            log.color_print(f"❌ Error crawling {url}: {e}")
    
    if not all_docs:
        log.color_print("❌ No documents were successfully crawled. Please check the URLs.")
        return
    
    total_docs = len(all_docs)
    log.color_print(f"📊 Web crawling complete: {success_count} sites crawled successfully, {error_count} sites failed")
    log.color_print(f"📄 Total documents extracted: {total_docs}")
    
    # Process documents in batches for streaming insertion
    # Use the provided batch size or the global default from environment variable
    batch_size = doc_batch_size if doc_batch_size is not None else DOC_BATCH_SIZE
    doc_batches = [all_docs[i:i + batch_size] for i in range(0, len(all_docs), batch_size)]
    
    total_chunks_processed = 0
    batch_count = len(doc_batches)
    
    # Generate a task_id for this web processing job
    task_id = f"web_{int(time.time())}"
    
    log.color_print(f"🔄 Processing {total_docs} documents in {batch_count} batches (batch size: {batch_size})...",
                   task_id=task_id, progress_type="processing")
    
    for batch_idx, doc_batch in enumerate(doc_batches):
        batch_docs_count = len(doc_batch)
        
        # Log batch progress
        log.color_print(f"⏱️ Processing batch {batch_idx+1}/{batch_count} ({batch_docs_count} documents)...",
                       task_id=f"{task_id}_batch_{batch_idx}", progress_type="processing")
        
        # 1. Split batch documents into chunks
        log.color_print(f"✂️ Splitting batch {batch_idx+1} documents into chunks...",
                       task_id=f"{task_id}_split_{batch_idx}", progress_type="chunking")
        
        batch_chunks = split_docs_to_chunks(
            doc_batch,
            task_id=f"{task_id}_split_{batch_idx}"
        )
        
        batch_chunk_count = len(batch_chunks)
        log.color_print(f"🧩 Created {batch_chunk_count} chunks from batch {batch_idx+1} documents",
                       task_id=f"{task_id}_split_{batch_idx}", progress_type="chunking")
        
        # 2. Process batch chunks based on configuration
        if batch_chunk_count > 0:
            if USE_BACKGROUND_WORKER:
                # Queue chunks for background processing
                log.color_print(f"📤 Queuing {batch_chunk_count} chunks for background processing...",
                               task_id=f"{task_id}_queue_{batch_idx}", progress_type="embedding")
                
                queued = BaseEmbedding.queue_chunks_for_embedding(
                    embedding_model, 
                    batch_chunks, 
                    task_id=f"{task_id}_embed_{batch_idx}"
                )
                
                if queued:
                    log.color_print(f"✅ Successfully queued {batch_chunk_count} chunks for background processing",
                                   task_id=f"{task_id}_queue_{batch_idx}", progress_type="embedding")
                else:
                    # Fall back to parallel embedding if queuing fails
                    log.color_print(f"⚠️ Background worker not available, falling back to parallel embedding",
                                   task_id=f"{task_id}_fallback_{batch_idx}", progress_type="warning")
                    
                    log.color_print(f"🔢 Generating embeddings for {batch_chunk_count} chunks using parallel processing...",
                                   task_id=f"{task_id}_embed_{batch_idx}", progress_type="embedding")
                    
                    embedded_chunks = embedding_model.embed_chunks_parallel(
                        batch_chunks, 
                        task_id=f"{task_id}_embed_{batch_idx}"
                    )
                    
                    log.color_print(f"💾 Inserting {batch_chunk_count} chunks into vector database...",
                                   task_id=f"{task_id}_insert_{batch_idx}", progress_type="storing")
                    
                    vector_db.insert_data(collection=collection_name, chunks=embedded_chunks)
            elif USE_PARALLEL_EMBEDDING:
                # Use parallel embedding
                log.color_print(f"🔢 Generating embeddings for {batch_chunk_count} chunks using parallel processing...",
                               task_id=f"{task_id}_embed_{batch_idx}", progress_type="embedding")
                
                embedded_chunks = embedding_model.embed_chunks_parallel(
                    batch_chunks, 
                    task_id=f"{task_id}_embed_{batch_idx}"
                )
                
                # Insert chunks
                log.color_print(f"💾 Inserting {batch_chunk_count} chunks into vector database collection '{collection_name}'...",
                               task_id=f"{task_id}_insert_{batch_idx}", progress_type="storing")
                
                vector_db.insert_data(collection=collection_name, chunks=embedded_chunks)
            else:
                # Use standard embedding
                log.color_print(f"🔢 Generating embeddings for {batch_chunk_count} chunks using {embedding_model.__class__.__name__}...",
                               task_id=f"{task_id}_embed_{batch_idx}", progress_type="embedding")
                
                embedded_chunks = embedding_model.embed_chunks(batch_chunks, task_id=f"{task_id}_embed_{batch_idx}")
                
                # Insert chunks
                log.color_print(f"💾 Inserting {batch_chunk_count} chunks into vector database collection '{collection_name}'...",
                               task_id=f"{task_id}_insert_{batch_idx}", progress_type="storing")
                
                vector_db.insert_data(collection=collection_name, chunks=embedded_chunks)
            
            total_chunks_processed += batch_chunk_count
            
            # Log progress after each batch
            progress_pct = ((batch_idx + 1) / batch_count) * 100
            log.color_print(f"✅ Batch {batch_idx+1}/{batch_count} complete: {batch_chunk_count} chunks processed ({progress_pct:.1f}% total)",
                           task_id=f"{task_id}_progress", progress_type="progress")
    
    # Clean up the background worker if it was used
    if USE_BACKGROUND_WORKER:
        log.color_print(f"⏳ Waiting for background worker to complete...", task_id=task_id, progress_type="cleanup")
        BaseEmbedding.stop_embedding_worker(task_id=task_id, wait=True)
    
    # Final completion message
    log.color_print(f"🎉 Data loading complete! {total_chunks_processed} chunks successfully stored in collection '{collection_name}'",
                   task_id=task_id, progress_type="complete")
    
    # Reset dev mode to original setting
    log.set_dev_mode(False)
