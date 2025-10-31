FROM python:3.10.12-slim

# Production backend deployment
ENV RAILWAY_CACHE_BUST=v6

WORKDIR /app

# Install PostgreSQL client
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY backend/requirements-production.txt ./backend/

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r backend/requirements-production.txt

# Copy hermes package (needed by backend/main.py imports)
COPY hermes/ ./hermes/

# Copy backend application code maintaining structure
COPY backend/ ./backend/

# Expose port
EXPOSE 8000

# Start command - run from /app with backend.main structure
CMD ["python", "-m", "backend.main"]
