-- Hermes Database Initialization Script
-- This runs automatically when PostgreSQL container starts

-- Install pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create indexes for better performance (will be created by SQLAlchemy too, but good to have)
-- These will be created after tables exist via migrations
