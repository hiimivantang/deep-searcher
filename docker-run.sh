#!/bin/bash

echo "Starting DeepSearcher in Docker..."

# Start the backend server (which also serves the frontend)
echo "Starting backend server..."
python main.py

echo "DeepSearcher is running!"
echo "Application available at: http://localhost:8000"