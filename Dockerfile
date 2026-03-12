# Use Python base image
FROM python:3.11-slim

# Environment settings
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy project files
COPY backend /app/backend
COPY frontend /app/frontend

# MongoDB connection (container name)
ENV MONGO_URI=mongodb://mongodb:27017/

# Expose Flask port
EXPOSE 5000

# Run Flask app
CMD ["python", "backend/app.py"]