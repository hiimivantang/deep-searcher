import os
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Union, Tuple

from tqdm import tqdm
import sys

from deepsearcher.loader.splitter import split_docs_to_chunks
from deepsearcher.tools import log

# from deepsearcher.configuration import embedding_model, vector_db, file_loader
from deepsearcher import configuration


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
):
    # Enable progress logging regardless of dev mode
    log.set_dev_mode(True)
    
    log.color_print(f"🔄 Starting data loading process...")
    
    vector_db = configuration.vector_db
    if collection_name is None:
        collection_name = vector_db.default_collection
    collection_name = collection_name.replace(" ", "_").replace("-", "_")
    embedding_model = configuration.embedding_model
    file_loader = configuration.file_loader
    
    log.color_print(f"✅ Initializing vector database collection: {collection_name}")
    vector_db.init_collection(
        dim=embedding_model.dimension,
        collection=collection_name,
        description=collection_description,
        force_new_collection=force_new_collection,
    )
    if isinstance(paths_or_directory, str):
        paths_or_directory = [paths_or_directory]
    
    # Get all file paths first, expanding directories
    log.color_print(f"🔍 Scanning for files to process...")
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
    log.color_print(f"📚 Starting file loading with {max_workers if max_workers else multiprocessing.cpu_count() - 1} workers...")
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
        log.inline_progress(f"📚 Loading files: 0/{total_files} (0%)")
        
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
                    log.inline_progress(f"📚 Loading files: {completed}/{total_files} ({progress_pct:.1f}%)")
                    
                    # Additional details for periodic detailed updates
                    if i % 10 == 0 or i == total_files - 1:  # Less frequent detailed updates
                        log.color_print(f"✅ Loaded file: {path} ({doc_count} documents)", same_line=False)
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
    
    # Splitting documents into chunks
    log.color_print(f"✂️ Splitting {total_docs} documents into chunks (size: {chunk_size}, overlap: {chunk_overlap})...")
    chunks = split_docs_to_chunks(
        all_docs,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    
    chunk_count = len(chunks)
    log.color_print(f"🧩 Created {chunk_count} chunks from {total_docs} documents")

    # Embedding chunks
    log.color_print(f"🔢 Generating embeddings for {chunk_count} chunks using {embedding_model.__class__.__name__}...")
    chunks = embedding_model.embed_chunks(chunks)
    log.color_print(f"✅ Successfully embedded {chunk_count} chunks")
    
    # Inserting into vector database
    log.color_print(f"💾 Inserting {chunk_count} chunks into vector database collection '{collection_name}'...")
    vector_db.insert_data(collection=collection_name, chunks=chunks)
    log.color_print(f"🎉 Data loading complete! {chunk_count} chunks successfully stored in collection '{collection_name}'")
    
    # Reset dev mode to original setting
    log.set_dev_mode(False)


def load_from_website(
    urls: Union[str, List[str]],
    collection_name: str = None,
    collection_description: str = None,
    force_new_collection: bool = False,
):
    # Enable progress logging regardless of dev mode
    log.set_dev_mode(True)
    
    log.color_print(f"🔄 Starting website loading process...")
    
    if isinstance(urls, str):
        urls = [urls]
    vector_db = configuration.vector_db
    embedding_model = configuration.embedding_model
    web_crawler = configuration.web_crawler

    if collection_name is None:
        collection_name = vector_db.default_collection
    collection_name = collection_name.replace(" ", "_").replace("-", "_")
    
    log.color_print(f"✅ Initializing vector database collection: {collection_name}")
    vector_db.init_collection(
        dim=embedding_model.dimension,
        collection=collection_name,
        description=collection_description,
        force_new_collection=force_new_collection,
    )

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
    
    # Splitting documents into chunks
    log.color_print(f"✂️ Splitting {total_docs} documents into chunks...")
    chunks = split_docs_to_chunks(all_docs)
    
    chunk_count = len(chunks)
    log.color_print(f"🧩 Created {chunk_count} chunks from {total_docs} documents")
    
    # Embedding chunks
    log.color_print(f"🔢 Generating embeddings for {chunk_count} chunks using {embedding_model.__class__.__name__}...")
    chunks = embedding_model.embed_chunks(chunks)
    log.color_print(f"✅ Successfully embedded {chunk_count} chunks")
    
    # Inserting into vector database
    log.color_print(f"💾 Inserting {chunk_count} chunks into vector database collection '{collection_name}'...")
    vector_db.insert_data(collection=collection_name, chunks=chunks)
    log.color_print(f"🎉 Data loading complete! {chunk_count} chunks successfully stored in collection '{collection_name}'")
    
    # Reset dev mode to original setting
    log.set_dev_mode(False)
