# Learning Coach MCP Server

An MCP (Model Context Protocol) server that acts as your personal AI Learning Coach. Tracks your learning progress, fetches relevant content, and generates personalized daily learning insights using RAG (Retrieval-Augmented Generation).

## Features

### 1. Content Management
- Store learning content from trusted sources (blogs, RSS feeds, Reddit)
- Track which week and topics you're currently learning
- Store your learning preferences and goals

### 2. Daily Learning Digest
- Generate 5-7 personalized learning insights each day
- Use RAG to find relevant content from your sources
- Adapt difficulty based on your current week

### 3. MCP Tools for LLM Clients (Claude App)
- `generate_daily_digest`: Create today's personalized learning insights
- `add_content_source`: Add new content sources (RSS/blogs)
- `update_progress`: Update your current week and learning topics
- `search_insights`: Search through past learning insights
- `get_progress`: View current learning progress
- `ingest_content_from_sources`: Manually trigger content ingestion
- `get_today_insights`: Retrieve today's generated insights

### 4. Semantic Search
- Use vector embeddings to find relevant content
- Match content to your current learning topics
- Score relevance of each insight using RAGAS-inspired metrics

## Tech Stack

- **FastMCP**: For building the MCP server
- **Supabase**: PostgreSQL database with pgvector extension
- **HuggingFace**: Open source sentence-transformers for embeddings
- **Groq**: Fast LLM inference (Llama 3.3 70B) for generating personalized insights
- **Python**: Programming language

## Project Structure

```
learning-coach-mcp/
├── src/
│   ├── server.py                    # Main MCP server with tools
│   ├── rag/
│   │   └── digest_generator.py      # RAG pipeline
│   ├── ingestion/
│   │   └── content_fetcher.py       # RSS feed & blog scraper
│   └── utils/
│       ├── database.py              # Supabase client
│       └── openai_client.py         # OpenAI client
├── .env.example                      # Environment variables template
├── requirements.txt                  # Python dependencies
└── README.md
```

## Setup Instructions

### 1. Clone and Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt
```

### 2. Set Up Supabase Database

Create a Supabase project and run the following SQL to set up your schema:

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Content sources table
CREATE TABLE content_sources (
    id SERIAL PRIMARY KEY,
    source_url TEXT NOT NULL UNIQUE,
    source_type TEXT NOT NULL, -- 'rss', 'blog', 'reddit'
    tags TEXT[],
    created_at TIMESTAMP DEFAULT NOW()
);

-- Learning content with embeddings
CREATE TABLE learning_content (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    source_url TEXT,
    embedding VECTOR(384), -- dimension for all-MiniLM-L6-v2
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create index for vector similarity search
CREATE INDEX ON learning_content USING ivfflat (embedding vector_cosine_ops);

-- User progress tracking
CREATE TABLE user_progress (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL UNIQUE,
    current_week INTEGER NOT NULL,
    current_topics TEXT[],
    learning_goals TEXT,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Daily insights
CREATE TABLE daily_insights (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    insight TEXT NOT NULL,
    content_id INTEGER REFERENCES learning_content(id),
    relevance_score FLOAT,
    week INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Function for vector similarity search
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
```

### 3. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
GROQ_API_KEY=your_groq_api_key
DEFAULT_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
MAX_DAILY_INSIGHTS=7
```

### 4. Run the MCP Server

```bash
# Run the server
python -m src.server
```

## Usage with Claude Desktop

Add this to your Claude Desktop MCP configuration:

```json
{
  "mcpServers": {
    "learning-coach": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/path/to/newsletter_mcp"
    }
  }
}
```

## Example Workflow

1. **Set up your learning profile:**
   ```
   Use update_progress to set:
   - current_week: 1
   - current_topics: ["Python", "Machine Learning", "RAG"]
   - learning_goals: "Build production ML applications"
   ```

2. **Add content sources:**
   ```
   Use add_content_source to add:
   - RSS feeds from tech blogs
   - Popular ML newsletters
   - Reddit threads
   ```

3. **Generate daily digest:**
   ```
   Use generate_daily_digest to get 5-7 personalized insights
   based on your topics and learning level
   ```

4. **Search past insights:**
   ```
   Use search_insights to find specific topics or concepts
   you've learned before
   ```

**Note:** This is a single-user system. All data is stored under a default user profile.

## How It Works

1. **Content Ingestion**: Fetches content from RSS feeds and blogs, generates embeddings using sentence-transformers
2. **Storage**: Stores content with vector embeddings in Supabase with pgvector
3. **Retrieval**: Uses semantic search to find content relevant to your current topics
4. **Generation**: Groq (Llama 3.3 70B) generates personalized insights based on your learning context
5. **Scoring**: RAGAS-inspired metrics score each insight for relevance

## Development

To extend this project:

- Add new content sources in `content_fetcher.py`
- Modify RAG pipeline in `digest_generator.py`
- Add new MCP tools in `server.py`
- Customize relevance scoring in digest generator

## License

MIT
