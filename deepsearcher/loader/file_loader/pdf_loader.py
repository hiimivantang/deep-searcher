from typing import List
from deepsearcher.loader.file_loader.base import BaseLoader
from langchain_core.documents import Document



class PDFLoader(BaseLoader):
    def __init__(self):
        pass

    def load_file(self, file_path: str) -> List[Document]:
        import pdfplumber
        import os
        
        # Get file extension
        _, file_extension = os.path.splitext(file_path)
        file_extension = file_extension.lower().lstrip('.')
        
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"Error: File does not exist: {file_path}")
            return []
            
        # Handle PDF files
        if file_extension == "pdf":
            try:
                with pdfplumber.open(file_path) as file:
                    page_content = "\n\n".join([page.extract_text() or "" for page in file.pages])
                    if not page_content.strip():
                        print(f"Warning: No text extracted from PDF: {file_path}")
                    return [Document(page_content=page_content, metadata={"reference": file_path})]
            except Exception as e:
                print(f"Error processing PDF file {file_path}: {str(e)}")
                return []
                
        # Handle text and markdown files
        elif file_extension in ["txt", "md"]:
            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as file:
                    page_content = file.read()
                    return [Document(page_content=page_content, metadata={"reference": file_path})]
            except Exception as e:
                print(f"Error processing text file {file_path}: {str(e)}")
                return []
        else:
            print(f"Unsupported file type: {file_path}")
            return []

    @property
    def supported_file_types(self) -> List[str]:
        return ["pdf", "md", "txt"]