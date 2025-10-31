FROM python:3.10.12-slim

# Production backend deployment
ENV RAILWAY_CACHE_BUST=v4

WORKDIR /app

# Install PostgreSQL client
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

# Copy backend requirements
COPY backend/requirements-production.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-production.txt

# Copy backend application code
COPY backend/ .

# Expose port
EXPOSE 8000

# Start command - Railway will set PORT env variable
CMD ["python", "main.py"]
