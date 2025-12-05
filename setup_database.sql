-- Setup script for Supabase database
-- Run this in your Supabase SQL editor

-- Enable pgvector extension for vector similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- Content sources table
-- Stores RSS feeds, blogs, and other content sources
CREATE TABLE content_sources (
    id SERIAL PRIMARY KEY,
    source_url TEXT NOT NULL UNIQUE,
    source_type TEXT NOT NULL, -- 'rss', 'blog', 'reddit'
    tags TEXT[],
    created_at TIMESTAMP DEFAULT NOW()
);

-- Learning content with embeddings
-- Stores actual content with vector embeddings for semantic search
CREATE TABLE learning_content (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    source_url TEXT,
    embedding VECTOR(384), -- dimension for all-MiniLM-L6-v2 model
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create index for fast vector similarity search
-- Using ivfflat index with cosine similarity
CREATE INDEX ON learning_content USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- User progress tracking
-- Tracks each user's current learning week, topics, and goals
CREATE TABLE user_progress (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL UNIQUE,
    current_week INTEGER NOT NULL,
    current_topics TEXT[],
    learning_goals TEXT,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Daily insights
-- Stores generated learning insights for each user
CREATE TABLE daily_insights (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    insight TEXT NOT NULL,
    content_id INTEGER REFERENCES learning_content(id),
    relevance_score FLOAT,
    week INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for faster queries
CREATE INDEX idx_daily_insights_user_date ON daily_insights(user_id, created_at DESC);
CREATE INDEX idx_content_sources_type ON content_sources(source_type);

-- Function for vector similarity search
-- Returns content similar to the query embedding
CREATE OR REPLACE FUNCTION match_learning_content(
    query_embedding VECTOR(384),
    match_threshold FLOAT,
    match_count INT
)
RETURNS TABLE (
    id INT,
    title TEXT,
    content TEXT,
    source_url TEXT,
    metadata JSONB,
    similarity FLOAT
)
LANGUAGE SQL STABLE
AS $$
    SELECT
        id,
        title,
        content,
        source_url,
        metadata,
        1 - (embedding <=> query_embedding) AS similarity
    FROM learning_content
    WHERE 1 - (embedding <=> query_embedding) > match_threshold
    ORDER BY similarity DESC
    LIMIT match_count;
$$;

-- Example: Insert a test user
INSERT INTO user_progress (user_id, current_week, current_topics, learning_goals)
VALUES (
    'test_user',
    1,
    ARRAY['Python', 'Machine Learning', 'RAG'],
    'Build production ML applications'
)
ON CONFLICT (user_id) DO NOTHING;

-- Example: Insert test content sources
INSERT INTO content_sources (source_url, source_type, tags)
VALUES
    ('https://python.libhunt.com/newsletter/feed', 'rss', ARRAY['python', 'programming']),
    ('https://machinelearningmastery.com/blog/feed/', 'rss', ARRAY['machine-learning', 'ai'])
ON CONFLICT (source_url) DO NOTHING;
