from fastapi import FastAPI, HTTPException, Body, Query, Depends, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Union, Dict, Any
import os
import shutil
import yaml
import json
import asyncio
from deepsearcher.configuration import Configuration, init_config
from deepsearcher.offline_loading import load_from_local_files, load_from_website
from deepsearcher.online_query import query, naive_rag_query
from deepsearcher.vector_db.base import BaseVectorDB
from deepsearcher.tools import log
import uvicorn

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load config
config_path = os.environ.get("CONFIG_PATH", "./config.yaml")
config = Configuration(config_path)
init_config(config)

# WebSocket connection manager for progress updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                # Remove dead connections
                self.active_connections = [
                    conn for conn in self.active_connections 
                    if conn != connection
                ]
                
manager = ConnectionManager()

# Progress update callback
def progress_callback(progress_data):
    if manager.active_connections:
        # We can't use await directly in a non-async function, so create a task
        # More detailed debug information for progress updates
        print(f"Progress update received: {len(progress_data)} tasks")
        for task_id, task in progress_data.items():
            task_type = task.get('type', 'unknown')
            # Print more details for embedding and storing tasks
            if task_type in ['embedding', 'storing']:
                percentage = task.get('percentage', 0)
                message = task.get('message', 'no message')
                timestamp = task.get('timestamp', 0)
                print(f"PROGRESS {task_id}: {task_type.upper()} - {percentage:.1f}% - {message} (t={timestamp})")
        
        asyncio.create_task(manager.broadcast(json.dumps(progress_data)))

# Register the callback with the log module
log.register_progress_callback(progress_callback)

# WebSocket route for progress updates
@app.websocket("/ws/progress")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    
    # Send current progress status immediately upon connection
    current_status = log.get_progress_status()
    if current_status:
        await websocket.send_text(json.dumps(current_status))
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        
# Endpoint to get current progress status
@app.get("/progress")
def get_progress():
    return log.get_progress_status()

# All API routes are defined below
# The static files mount will be done at the end of this file after all API routes are defined

@app.post("/load-files")
def load_files(
    paths: Union[str, List[str]] = Body(..., description="A list of file paths to be loaded.", examples=["/path/to/file1", "/path/to/file2", "/path/to/dir1"]),
    collection_name: str = Body(None, description="Optional name for the collection.", examples=["my_collection"]),
    collection_description: str = Body(None, description="Optional description for the collection.", examples=["This is a test collection."])
):
    try:
        load_from_local_files(paths_or_directory=paths, collection_name=collection_name, collection_description=collection_description)
        return {"message": "Files loaded successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/load-website")
def load_website(
    urls: Union[str, List[str]] = Body(..., description="A list of URLs of websites to be loaded.", examples=["https://milvus.io/docs/overview.md"]),
    collection_name: str = Body(None, description="Optional name for the collection.", examples=["my_collection"]),
    collection_description: str = Body(None, description="Optional description for the collection.", examples=["This is a test collection."])
):
    try:
        load_from_website(urls=urls, collection_name=collection_name, collection_description=collection_description)
        return {"message": "Website loaded successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/query")
def perform_query(
    original_query: str = Query(..., description="Your question here.", examples=["Write a report about Milvus."]),
    max_iter: int = Query(3, description="The maximum number of iterations for reflection.", ge=1, examples=[3])
):
    try:
        result, _, _ = query(original_query, max_iter)
        return {"result": result}
    except Exception as e:
        print(f"Error in perform_query: {e}")
        error_message = f"An error occurred during query processing: {str(e)}"
        # Return error as result instead of HTTP error
        return {"result": error_message}

@app.get("/naive-query")
def perform_naive_query(
    query: str = Query(..., description="Your question here.", examples=["What is Milvus?"]),
    collection: str = Query(None, description="Optional collection to search in.")
):
    try:
        result, _ = naive_rag_query(query, collection)
        return {"result": result}
    except Exception as e:
        print(f"Error in perform_naive_query: {e}")
        error_message = f"An error occurred during query processing: {str(e)}"
        # Return error as result instead of HTTP error
        return {"result": error_message}

@app.get("/collections")
def get_collections():
    try:
        from deepsearcher import configuration
        vector_db = configuration.vector_db
        try:
            collections = [col_info.collection_name for col_info in vector_db.list_collections()]
            return collections
        except Exception as collection_error:
            # Return an empty list if there's an error (like no collections exist yet)
            print(f"Error listing collections: {collection_error}")
            return []
    except Exception as e:
        print(f"Error in get_collections: {e}")
        # Return empty list instead of error for better UX
        return []

@app.get("/config")
def get_config():
    try:
        with open(config_path, "r") as file:
            config_data = yaml.safe_load(file)
            # Sanitize any sensitive information if needed
            return config_data
    except Exception as e:
        print(f"Error reading config: {e}")
        # Return a default config instead of error
        return {
            "provide_settings": {
                "llm": {"provider": "OpenAI", "config": {"model": "gpt-4o"}},
                "embedding": {"provider": "OpenAIEmbedding", "config": {"model": "text-embedding-3-small"}},
                "file_loader": {"provider": "PDFLoader", "config": {}},
                "web_crawler": {"provider": "FireCrawlCrawler", "config": {}},
                "vector_db": {"provider": "Milvus", "config": {"default_collection": "deepsearcher"}}
            },
            "query_settings": {"max_iter": 3},
            "load_settings": {"chunk_size": 1500, "chunk_overlap": 100}
        }

@app.post("/update-config")
def update_config(config_data: Dict[str, Any] = Body(...)):
    try:
        # Validate config structure
        if not all(key in config_data for key in ["provide_settings", "query_settings", "load_settings"]):
            raise ValueError("Invalid config structure")
            
        # Backup the current config
        backup_path = f"{config_path}.backup"
        shutil.copy2(config_path, backup_path)
        
        # Write the new config
        with open(config_path, "w") as file:
            yaml.dump(config_data, file, default_flow_style=False)
            
        # Reinitialize with the new config
        new_config = Configuration(config_path)
        init_config(new_config)
        
        return {"message": "Configuration updated successfully."}
    except Exception as e:
        # Restore backup if something went wrong
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, config_path)
        raise HTTPException(status_code=500, detail=str(e))

# Mount static files AFTER all API routes are defined
# This ensures that API routes take precedence over static file serving
app.mount("/", StaticFiles(directory="./frontend/build", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
