# Use a PyTorch base image with CUDA support
FROM pytorch/pytorch:2.2.1-cuda12.1-cudnn8-runtime

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV SKIP_LLM_LOAD "false"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    wget \
    build-essential \
    redis-server \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir git+https://github.com/huggingface/transformers.git

# Copy the rest of the application code
COPY . .

# Create directory for models
RUN mkdir -p models

# Expose the FastAPI port
EXPOSE 8000

# Script to start both Redis, Celery Worker, and FastAPI
# In a real production setup, these would be separate containers
# But for a portable prototype, we can use a small start script
RUN echo "#!/bin/bash\nredis-server --daemonize yes\ncelery -A tasks worker --loglevel=info --concurrency=1 & \nuvicorn main:app --host 0.0.0.0 --port 8000" > start.sh
RUN chmod +x start.sh

CMD ["./start.sh"]
