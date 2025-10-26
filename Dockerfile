FROM python:3.10.12-slim

# Bust Railway's cache - changed base image
ENV RAILWAY_CACHE_BUST=v3

# Force rebuild - updated 2025-10-25
WORKDIR /app

# Install PostgreSQL client
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make start script executable
RUN chmod +x start.sh

# Expose port
EXPOSE 8000

# Start the application - inline everything to avoid Railway cache bugs
CMD ["/bin/bash", "-c", "echo '🚀 Starting Hermes' && echo 'PORT='${PORT} && alembic upgrade head && uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
