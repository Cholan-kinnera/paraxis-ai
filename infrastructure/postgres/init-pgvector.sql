-- ==============================================================================
-- Paraxis AI - PostgreSQL Database Initialization
-- Enables UUID and Vector extensions for relational data and semantic retrieval
-- ==============================================================================

-- Enable UUID extension for canonical identifier generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pgvector extension for operational RAG and semantic embeddings
CREATE EXTENSION IF NOT EXISTS "vector";

-- Verify extensions
DO $$
BEGIN
    RAISE NOTICE 'UUID extension initialized: %', (SELECT extversion FROM pg_extension WHERE extname = 'uuid-ossp');
    RAISE NOTICE 'Vector extension initialized: %', (SELECT extversion FROM pg_extension WHERE extname = 'vector');
END $$;
