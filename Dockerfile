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

# Make scripts executable
RUN chmod +x start.sh entrypoint.sh

# Expose port
EXPOSE 8000

# Set entrypoint that shells any provided command so $PORT expands even if Railway overrides CMD
ENTRYPOINT ["./entrypoint.sh"]

# Default command falls back to start script
CMD ["./start.sh"]
