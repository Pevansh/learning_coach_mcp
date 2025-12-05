---
stepsCompleted: [1, 2, 3]
inputDocuments: ['docs/prd.md']
workflowType: 'architecture'
lastStep: 3
project_name: 'newsletter_mcp'
user_name: 'Pevanshgulati'
date: '2025-12-01'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**

The system implements a personalized learning companion as an MCP server with four core tools:

1. **MCP Server Infrastructure (FR1-FR4)**: Accept connections from MCP-compatible AI clients, expose tools via MCP protocol, handle concurrent invocations, return structured responses

2. **User Profile & Learning Progress (FR5-FR10)**: Track learning state (current week, topics, completed topics), persist preferences, provide profile updates

3. **Content Source Management (FR11-FR17)**: Ingest URLs, fetch/extract content, chunk intelligently (512 tokens, 50 overlap), generate embeddings, store in vector-indexed database

4. **Daily Digest Generation (FR18-FR27)**: Core RAG pipeline - retrieve user context, generate semantic queries, perform vector similarity search, use LLM to create 5-7 candidate insights, evaluate with RAGAS (faithfulness, relevance, context precision), filter below 0.7 threshold, complete within 30 seconds

5. **Insight Search & Retrieval (FR28-FR33)**: Semantic search across past insights with filters (date, topics, week), ranked by relevance and recency

6. **Quality Assurance & Evaluation (FR34-FR38)**: RAGAS evaluation measuring faithfulness, relevancy, context precision, composite scoring, minimum quality enforcement

7. **Data Persistence (FR39-FR44)**: Store user profiles, content sources, vector embeddings, digests, insights, progress history with referential integrity

8. **Content Processing Pipeline (FR45-FR48)**: Configurable chunking, overlapping windows, multi-format handling, structure preservation

9. **Personalization & Adaptation (FR49-FR52)**: Tailor insights to current week/topics, adjust based on preferences, prioritize contextually relevant content

10. **Error Handling & Logging (FR53-FR57)**: Graceful error handling across content fetching, embedding generation, digest generation, with meaningful error messages

**Non-Functional Requirements:**

**Performance (NFR1-NFR7):**
- Digest generation: ≤ 30 seconds
- Simple operations: ≤ 5 seconds
- Search queries: ≤ 3 seconds (up to 1,000 insights)
- Concurrent load: 10+ simultaneous digest requests without degradation
- Vector search: sub-3-second with up to 100,000 chunks
- Content processing: 10 articles/minute (2,000 words each)
- RAGAS evaluation: 20 insights in parallel within 30-second window

**Security (NFR8-NFR15):**
- Data at rest: AES-256 encryption
- Data in transit: TLS 1.2+
- Secure credential management (environment variables/secrets)
- User data isolation with access controls
- MCP client authentication
- URL validation and sanitization
- Privacy protection for learning data
- No sensitive data in logs

**Scalability (NFR16-NFR21):**
- User growth: 10 → 1,000 users with minimal configuration changes
- Database schema: supports 10x content growth without migration
- Vector search: acceptable performance (< 5s) with 1M chunks
- Storage: 100 GB capacity for V1
- Concurrent connections: 50+ MCP clients
- Horizontal scaling for background processing

**Reliability (NFR22-NFR32):**
- Uptime: 95% during business hours
- Automatic retry with exponential backoff
- Atomic profile updates
- Referential integrity (no orphaned embeddings)
- No partial data on failures
- Graceful error handling with meaningful messages
- Automatic retry (up to 3 attempts) for embedding service
- Structured error responses for MCP clients
- Comprehensive error logging
- Critical failure alerts
- Performance metrics logging

**Scale & Complexity:**

- Primary domain: **API Backend (MCP Server)**
- Complexity level: **Medium**
- Estimated architectural components: **7-9 major components**
  - MCP protocol handler
  - RAG pipeline orchestrator
  - Vector embedding service
  - RAGAS evaluation engine
  - Content ingestion pipeline
  - Database layer (PostgreSQL + pgvector)
  - Search and retrieval service

### Technical Constraints & Dependencies

**Required Technologies (from PRD):**
- **FastMCP**: MCP server framework
- **Supabase**: PostgreSQL database with pgvector extension for vector operations
- **HuggingFace**: Sentence-transformers models for embeddings
- **RAGAS**: Quality evaluation framework for generated insights

**Known Constraints:**
- Must comply with MCP protocol specification for tool exposure
- Vector embeddings must use consistent dimensionality across all content
- RAGAS evaluation requires minimum 0.7 composite score threshold
- Chunk size fixed at 512 tokens with 50 token overlap for context preservation
- Target adult self-learners (V1 scope - no COPPA/FERPA compliance needed)

**External Dependencies:**
- HuggingFace embedding service availability and latency
- Content source URL accessibility and format variability
- LLM service for insight generation
- Supabase service reliability

### Cross-Cutting Concerns Identified

**Data Consistency:**
- Vector embeddings must remain synchronized with source content
- User profile updates must be atomic to prevent state corruption
- Referential integrity between users, content, embeddings, and insights

**Performance Optimization:**
- Vector similarity search optimization critical for user experience
- Parallel RAGAS evaluation to meet 30-second digest generation SLA
- Efficient chunking strategy to balance context preservation vs. search granularity
- Database query optimization for vector operations at scale

**Error Recovery & Resilience:**
- Retry logic for transient failures (network, external services)
- Graceful degradation when embedding service unavailable
- Content fetching failures shouldn't block other operations
- Failed digest generation must not corrupt database state

**Security & Privacy:**
- User learning data isolation (profiles, progress, custom content)
- Secure handling of external URLs to prevent injection attacks
- Credentials and API keys must never be logged or exposed
- Encryption for data at rest and in transit

**Observability:**
- Performance metrics tracking (digest time, search latency, RAGAS scores)
- Error logging with sufficient context for debugging
- Alerting for critical failures (database connection, embedding service)

**Quality Assurance:**
- RAGAS evaluation pipeline ensures consistent insight quality
- Minimum quality threshold enforcement across all digest generation
- Quality metrics trending for continuous improvement

## Starter Template Evaluation

### Primary Technology Domain

**API Backend (MCP Server with RAG Pipeline)** based on project requirements analysis.

The project is a Python-based MCP server exposing RAG-powered tools, requiring vector database integration with Supabase/pgvector, embedding generation, and quality evaluation pipelines.

### Starter Options Considered

**1. Python MCP Server Starter Template (ltwlf)**
- Opinionated starter kit for MCP servers in Python
- Provides clean project scaffold with typed code
- Docker and GitHub Actions ready out-of-the-box
- Uses official MCP Python SDK
- Includes VS Code debug integration
- Available at: [Python MCP Starter Template](https://mcp.so/server/python-mcp-starter/ltwlf)

**2. Crawl4AI RAG MCP Server (coleam00)**
- Comprehensive RAG + MCP implementation
- Pre-configured Supabase pgvector integration
- Includes vector search and RAG tools
- OpenAI embeddings integration
- Advanced features: contextual embeddings, hybrid search, reranking
- Available at: [GitHub - coleam00/mcp-crawl4ai-rag](https://github.com/coleam00/mcp-crawl4ai-rag)

**3. Custom uv-based FastMCP Project**
- Modern Python project management with `uv`
- FastMCP 2.0 framework (actively maintained)
- Full control over architecture
- Requires manual Supabase/pgvector setup
- Initialization: `uv init` + `uv add mcp[cli]`
- Reference: [FastMCP GitHub](https://github.com/jlowin/fastmcp)

### Selected Starter: Custom uv-based FastMCP Project

**Rationale for Selection:**

While the Crawl4AI RAG MCP server provides an excellent reference implementation with Supabase integration, your project has unique requirements (RAGAS evaluation, custom chunking strategy, specific learning domain models) that warrant a custom foundation. The Python MCP Starter Template is too generic and doesn't include RAG/vector database patterns.

**Key reasons for custom approach:**
1. **RAGAS Integration**: No existing starter includes RAGAS quality evaluation pipeline
2. **Learning-Domain Specificity**: Personalized learning insights require custom prompt engineering and context management
3. **Flexibility**: Full control over chunking strategy (512 tokens, 50 overlap), embedding models, and quality thresholds
4. **Clean Foundation**: Start lean with modern tooling (uv) and add only what's needed
5. **Reference Available**: Can learn from Crawl4AI RAG patterns for Supabase integration without inheriting unnecessary complexity

**Initialization Commands:**

```bash
# Create project directory
mkdir newsletter_mcp
cd newsletter_mcp

# Initialize uv project
uv init

# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate  # On Windows

# Install core dependencies
uv add mcp[cli]
uv add fastmcp
uv add supabase
uv add sentence-transformers
uv add ragas
uv add python-dotenv
uv add pydantic
uv add httpx

# Sync dependencies
uv sync
```

**Architectural Decisions Provided by Starter:**

**Language & Runtime:**
- **Python 3.11+** with type hints for safety and IDE support
- **uv** for dependency management (faster than pip, modern lock files)
- **FastMCP 2.0** for MCP protocol implementation
- Type-safe decorators for tool definitions
- Async/await support for concurrent operations

**Project Structure:**
```
newsletter_mcp/
├── src/
│   ├── server.py              # Main MCP server entry point
│   ├── config.py              # Environment configuration
│   ├── tools/                 # MCP tool implementations
│   │   ├── __init__.py
│   │   ├── generate_digest.py
│   │   ├── add_content.py
│   │   ├── update_progress.py
│   │   └── search_insights.py
│   ├── services/              # Business logic layer
│   │   ├── __init__.py
│   │   ├── rag_pipeline.py
│   │   ├── embedding_service.py
│   │   ├── ragas_evaluator.py
│   │   └── content_processor.py
│   ├── database/              # Database layer
│   │   ├── __init__.py
│   │   ├── client.py          # Supabase client
│   │   └── models.py          # Pydantic models
│   └── utils/                 # Utilities
│       ├── __init__.py
│       ├── chunking.py
│       └── logger.py
├── tests/                     # Test suite
│   ├── unit/
│   └── integration/
├── .env.example               # Environment template
├── .gitignore
├── pyproject.toml             # Python project config
├── uv.lock                    # Dependency lock file
├── Dockerfile                 # Container config (for Vercel)
└── README.md
```

**Build Tooling:**
- **uv** for fast dependency resolution and virtual environment management
- **pyproject.toml** for modern Python packaging (PEP 518)
- **uv.lock** for reproducible builds across environments
- No complex build steps - Python interpreted language

**Testing Framework:**
- **pytest** for unit and integration testing
- **pytest-asyncio** for async test support
- **pytest-mock** for mocking external services
- Separate test directories for unit vs integration tests

**Code Organization:**
- **Layered architecture**: Tools → Services → Database
- **Dependency injection**: Services injected into tools
- **Type safety**: Pydantic models for data validation
- **Configuration**: python-dotenv for environment management
- **Logging**: Structured logging for observability

**Development Experience:**
- **FastMCP decorators**: Simple tool registration with `@mcp.tool()`
- **Type hints**: Full IDE autocomplete and type checking
- **Hot reloading**: FastMCP supports development mode
- **VS Code integration**: Debug configurations for MCP server
- **Environment management**: `.env` for local development, secrets for production

**Deployment (Vercel):**
- **Dockerfile**: Container-based deployment
- **Environment variables**: Supabase credentials, API keys via Vercel secrets
- **Serverless-ready**: Stateless design for horizontal scaling
- **Health checks**: `/health` endpoint for monitoring

**Note:** Project initialization using these commands should be the first implementation task. Reference the [Crawl4AI RAG MCP Server](https://github.com/coleam00/mcp-crawl4ai-rag) for Supabase pgvector integration patterns.
