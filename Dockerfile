FROM node:18 AS frontend-builder

WORKDIR /app

# Copy only needed frontend files and install dependencies
COPY ./frontend/package*.json ./frontend/
RUN cd frontend && npm install

# Copy only the source files needed for build (exclude node_modules)
COPY ./frontend/public ./frontend/public/
COPY ./frontend/src ./frontend/src/
COPY ./frontend/*.js ./frontend/
COPY ./frontend/*.json ./frontend/

# Build the frontend
RUN cd frontend && npm run build

# Python base image
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (exclude unnecessary directories to save space)
COPY deepsearcher ./deepsearcher/
COPY examples ./examples/
COPY documents ./documents/
COPY *.py ./
COPY *.sh ./
COPY *.txt ./
COPY *.yaml ./
COPY *.md ./

# Copy the built frontend from the frontend-builder stage
COPY --from=frontend-builder /app/frontend/build ./frontend/build

# Set environment variables
ENV CONFIG_PATH=/config/config.yaml
ENV PYTHONPATH=/app
ENV MULTIPROCESSING_FORK_ENABLE=1

# Set default number of workers for multiprocessing
ENV MAX_WORKERS=2

# Expose ports for the application
EXPOSE 8000

# Create a Docker-specific run script
COPY docker-run.sh /app/docker-run.sh
RUN chmod +x /app/docker-run.sh

# Provide a default command that starts the application
CMD ["/app/docker-run.sh"]
