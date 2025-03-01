#!/bin/bash

# Function to kill background processes on script exit
cleanup() {
    echo "Stopping services..."
    kill $FRONTEND_PID $BACKEND_PID 2>/dev/null
    exit 0
}

# Setup trap to catch interrupt signals
trap cleanup INT TERM

echo "Starting DeepSearcher..."

# Check if the frontend is built
if [ ! -d "frontend/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd frontend && npm install && cd ..
fi

# Start the backend server
echo "Starting backend server..."
python main.py &
BACKEND_PID=$!
echo "Backend server running with PID: $BACKEND_PID"

# Wait for backend to start
echo "Waiting for backend to start..."
sleep 5

# Start the frontend development server
echo "Starting frontend server..."
cd frontend && npm start &
FRONTEND_PID=$!
echo "Frontend server running with PID: $FRONTEND_PID"

echo "DeepSearcher is running!"
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:8000"
echo "Press Ctrl+C to stop all services."

# Wait for both processes to finish (or until script is interrupted)
wait