import os
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Union, Tuple

from tqdm import tqdm

from deepsearcher.loader.splitter import split_docs_to_chunks

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
    vector_db = configuration.vector_db
    if collection_name is None:
        collection_name = vector_db.default_collection
    collection_name = collection_name.replace(" ", "_").replace("-", "_")
    embedding_model = configuration.embedding_model
    file_loader = configuration.file_loader
    vector_db.init_collection(
        dim=embedding_model.dimension,
        collection=collection_name,
        description=collection_description,
        force_new_collection=force_new_collection,
    )
    if isinstance(paths_or_directory, str):
        paths_or_directory = [paths_or_directory]
    
    # Get all file paths first, expanding directories
    all_file_paths = []
    for path in paths_or_directory:
        if os.path.isdir(path):
            for file in os.listdir(path):
                file_path = os.path.join(path, file)
                if os.path.isfile(file_path) and any(file.endswith(suffix) for suffix in file_loader.supported_file_types):
                    all_file_paths.append(file_path)
        else:
            all_file_paths.append(path)
    
    # Use multiprocessing for file loading
    all_docs = []
    if max_workers is None:
        max_workers = max(1, multiprocessing.cpu_count() - 1)  # Leave one core free
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(file_loader.load_file, path): path 
                  for path in all_file_paths}
        
        for future in tqdm(as_completed(futures), total=len(futures), desc="Loading files"):
            try:
                docs = future.result()
                all_docs.extend(docs)
            except Exception as e:
                path = futures[future]
                print(f"Error loading {path}: {e}")
    
    # print("Splitting docs to chunks...")
    chunks = split_docs_to_chunks(
        all_docs,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    chunks = embedding_model.embed_chunks(chunks)
    vector_db.insert_data(collection=collection_name, chunks=chunks)


def load_from_website(
    urls: Union[str, List[str]],
    collection_name: str = None,
    collection_description: str = None,
    force_new_collection: bool = False,
):
    if isinstance(urls, str):
        urls = [urls]
    vector_db = configuration.vector_db
    embedding_model = configuration.embedding_model
    web_crawler = configuration.web_crawler

    vector_db.init_collection(
        dim=embedding_model.dimension,
        collection=collection_name,
        description=collection_description,
        force_new_collection=force_new_collection,
    )

    all_docs = []
    for url in tqdm(urls, desc="Loading from websites"):
        docs = web_crawler.crawl_url(url)
        all_docs.extend(docs)

    chunks = split_docs_to_chunks(all_docs)
    chunks = embedding_model.embed_chunks(chunks)
    vector_db.insert_data(collection=collection_name, chunks=chunks)
