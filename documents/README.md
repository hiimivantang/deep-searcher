# Documents Folder

This folder is mounted to the Docker container at `/data/documents`. Any files placed here will be accessible for loading into the DeepSearcher application.

## Usage

1. Copy your documents (PDF, TXT, MD files) to this folder
2. In the DeepSearcher web interface, go to "Load Data" tab
3. Enter the path `/data/documents` or specific file paths like `/data/documents/your-file.pdf`
4. Click "Load Files" to process the documents

## Supported File Types

- PDF (.pdf)
- Text (.txt)
- Markdown (.md)

## Notes

- Large files may take longer to process
- Make sure your files contain extractable text (scanned PDFs without OCR may not work)