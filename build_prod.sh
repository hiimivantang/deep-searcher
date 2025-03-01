#!/bin/bash

echo "Building DeepSearcher production deployment..."

# Check if frontend dependencies are installed
if [ ! -d "frontend/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd frontend && npm install && cd ..
fi

# Build the frontend
echo "Building React frontend..."
cd frontend && npm run build && cd ..

# Create static directory if it doesn't exist
if [ ! -d "static" ]; then
    mkdir -p static
fi

# Copy the build to the static directory
echo "Copying frontend build to static directory..."
cp -r frontend/build/* static/

# Update FastAPI to serve the static files
echo "Enabling static file serving in FastAPI..."
sed -i.bak -e 's|# app.mount("/", StaticFiles(directory="./frontend/build", html=True), name="static")|app.mount("/", StaticFiles(directory="./static", html=True), name="static")|' main.py

echo "Production build complete!"
echo "To run the application in production mode:"
echo "python main.py"
echo ""
echo "Note: To revert to development mode, restore the commented line in main.py"