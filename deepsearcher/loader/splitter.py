## Sentence Window splitting strategy, ref:
#  https://github.com/milvus-io/bootcamp/blob/master/bootcamp/RAG/advanced_rag/sentence_window_with_langchain.ipynb

from typing import List
from langchain_core.documents import Document
from tqdm import tqdm
from deepsearcher.tools import log


class Chunk:
    def __init__(self, text: str, reference: str, metadata: dict = None, embedding: List[float] = None):
        self.text = text
        self.reference = reference
        self.metadata = metadata or {}
        self.embedding = embedding or None


from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter



def _sentence_window_split(
    split_docs: List[Document], original_document: Document, offset: int = 200
) -> List[Chunk]:
    chunks = []
    original_text = original_document.page_content
    for doc in split_docs:
        doc_text = doc.page_content
        start_index = original_text.index(doc_text)
        end_index = start_index + len(doc_text) - 1
        wider_text = original_text[
            max(0, start_index - offset) : min(len(original_text), end_index + offset)
        ]
        reference = doc.metadata.pop("reference", "")
        doc.metadata["wider_text"] = wider_text
        chunk = Chunk(text=doc_text, reference=reference, metadata=doc.metadata)
        chunks.append(chunk)
    return chunks



def split_docs_to_chunks(documents: List[Document], chunk_size: int = 1500, chunk_overlap=100) -> List[Chunk]:
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    all_chunks = []
    
    # Process documents in batches to provide progress updates
    batch_size = max(1, len(documents) // 10)  # Report progress ~10 times
    total_chunks = 0
    
    for i, doc in enumerate(tqdm(documents, desc="Splitting documents")):
        split_docs = text_splitter.split_documents([doc])
        split_chunks = _sentence_window_split(split_docs, doc, offset=300)
        all_chunks.extend(split_chunks)
        
        # Log progress periodically or for the last document
        if (i + 1) % batch_size == 0 or i == len(documents) - 1:
            new_chunks = len(all_chunks) - total_chunks
            total_chunks = len(all_chunks)
            progress_pct = ((i + 1) / len(documents)) * 100
            
            # Only log if log module is imported and available
            try:
                log.color_print(f"📄 Processed {i+1}/{len(documents)} documents ({progress_pct:.1f}%), generated {new_chunks} new chunks (total: {total_chunks})")
            except:
                pass  # Skip logging if log module not available
                
    return all_chunks
