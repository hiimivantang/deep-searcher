FROM node:18 AS frontend-builder

WORKDIR /app

# Copy frontend code and install dependencies
COPY ./frontend/package*.json ./frontend/
RUN cd frontend && npm install

# Copy and build the frontend
COPY ./frontend ./frontend/
RUN cd frontend && npm run build

# Python base image
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy the built frontend from the frontend-builder stage
COPY --from=frontend-builder /app/frontend/build ./frontend/build

# Static files are already configured in main.py

# Set environment variable to read config from mounted volume
ENV CONFIG_PATH=/config/config.yaml

# Expose ports for the application
EXPOSE 8000

# Create a Docker-specific run script
COPY docker-run.sh /app/docker-run.sh
RUN chmod +x /app/docker-run.sh

# Provide a default command that starts the application
CMD ["/app/docker-run.sh"]