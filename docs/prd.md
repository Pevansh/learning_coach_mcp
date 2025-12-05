---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
inputDocuments: ['details.txt']
workflowType: 'prd'
lastStep: 10
project_name: 'newsletter_mcp'
user_name: 'Pevanshgulati'
date: '2025-12-01'
---

# Product Requirements Document - newsletter_mcp

**Author:** Pevanshgulati
**Date:** 2025-12-01

## Executive Summary

**newsletter_mcp** is a personalized learning companion MCP server that helps self-directed learners retain knowledge as they progress through structured curricula. Instead of generic daily newsletters or rigid learning platforms, it provides intelligent, context-aware insights generated from the learner's own curated content sources.

The product addresses the core challenge of self-directed learning: **information overload without personalized guidance leads to poor retention and abandoned goals.** Learners start with motivation but struggle to maintain momentum when they're buried in content that isn't contextually relevant to their current learning stage.

**Target Users:** Self-directed learners following week-by-week curricula - bootcamp students, developers learning new stacks, career changers, anyone on a structured learning path who wants to actually retain what they learn.

**Core Value Proposition:** Through RAG-powered daily digests, learners receive 5-7 high-quality insights that are:
- **Personalized** to their current week and topics
- **Filtered** using RAGAS evaluation for quality and relevance
- **Customizable** based on their own content sources
- **Intelligent** about timing and context for optimal retention

The MCP architecture means this works across any AI client (Claude, GPT, etc.), making it learning infrastructure rather than just another app.

### What Makes This Special

**Personalized, not prescriptive:** Unlike traditional learning platforms that push generic content, newsletter_mcp works with content the learner already trusts. They curate their sources (favorite blogs, Twitter follows, Reddit communities), and the system intelligently synthesizes insights matched to their learning stage.

**Retention-focused, not completion-focused:** The goal isn't just to finish Week 12 of a bootcamp - it's to retain and recall concepts weeks later. Daily digests provide spaced repetition of key concepts at contextually optimal moments.

**Infrastructure, not siloed app:** Built as an MCP server, this becomes universal learning infrastructure. Any LLM can become a personalized learning coach, not locked into one ecosystem.

**Quality-controlled intelligence:** RAGAS evaluation ensures insights meet minimum quality thresholds (faithfulness, relevance, context precision). It's not just content summarization - it's intelligent curation.

**User feedback drives improvement:** The system learns from user feedback, improving insight quality and relevance over time. The more you use it, the better it understands your learning style.

**The "Aha!" moment:** When a learner realizes their scattered content sources are being intelligently synthesized into perfectly-timed insights that actually help them understand and retain concepts - that's when they know this is different.

## Project Classification

**Technical Type:** api_backend
**Domain:** edtech
**Complexity:** medium

This is fundamentally a backend service exposing tools via the MCP protocol. The MCP server provides four core tools (generate_daily_digest, add_content_source, update_progress, search_insights) that any MCP-compatible AI client can invoke.

**Technical Architecture:** FastMCP server with RAG pipeline, Supabase (PostgreSQL + pgvector) for storage and semantic search, HuggingFace embeddings for vector operations, RAGAS for insight evaluation.

**Domain Considerations:** As an edtech product focused on students/learners, we must consider content moderation and age-appropriate filtering, though this is V1 focused on adult self-learners. Privacy around learning progress and content sources is important but not at COPPA/FERPA compliance levels.

**Complexity Rationale:** Medium complexity due to RAG implementation, vector search optimization, and quality evaluation pipelines. Not high complexity because V1 targets adult learners without stringent regulatory requirements.

## Success Criteria

### User Success

**Primary Success Indicators:**
- **Read rates**: Users consistently engage with daily digests (not just another ignored notification)
- **Retention**: Users can recall and apply concepts from previous weeks of their learning journey

**Observable Success Behaviors:**
- Users return to the digest daily or multiple times per week
- Users actively use `search_insights` to recall past learning
- Users continue updating their progress week-over-week (indicating sustained engagement)
- Users provide positive feedback on insight relevance and quality

**The Success Moment:** When a learner realizes their curated content sources are being intelligently synthesized into perfectly-timed insights that actually help them understand and retain concepts.

### Business Success

**V1 Focus:** Prove the concept works with real learners
- Validate that RAG + RAGAS produces high-quality, relevant insights
- Confirm users find value in personalized daily digests
- Demonstrate MCP infrastructure model is viable across different AI clients
- Gather user feedback to inform post-MVP iterations

**Measured Through:**
- User engagement patterns (digest generation frequency, search usage)
- Qualitative feedback from early adopters
- RAGAS quality scores trending above 0.7 threshold
- Successful MCP integration with multiple AI clients

### Technical Success

**Infrastructure:**
- MCP server successfully connects to Claude and other MCP-compatible clients
- All four core tools (`generate_daily_digest`, `add_content_source`, `update_progress`, `search_insights`) are functional and reliable
- Supabase vector search performs efficiently at initial scale

**RAG Pipeline:**
- Content chunking and embedding pipeline processes sources correctly
- Vector similarity search returns relevant results
- RAGAS evaluation accurately filters low-quality insights (minimum threshold: 0.7)
- Digest generation completes within reasonable timeframe (< 30 seconds for 5-7 insights)

**Data Quality:**
- Embeddings are generated correctly and stored in pgvector
- Content metadata is extracted and stored accurately
- User profile and progress tracking persists reliably

### Measurable Outcomes

**For V1, success means:**
- A working MCP server that any compatible AI client can connect to
- Daily digests that consistently score above 0.7 on RAGAS metrics
- Users can curate their own content sources and see them reflected in personalized insights
- Search functionality returns semantically relevant past insights
- The system works end-to-end: add sources → update progress → generate digest → search insights

## Product Scope

### MVP - Minimum Viable Product (V1)

**Core MCP Tools (All Required):**

1. **`generate_daily_digest`**
   - Fetches user profile (current week, topics, preferences)
   - Generates semantic queries based on current learning context
   - Retrieves top-k relevant content chunks via vector search
   - Uses LLM to generate 5-7 candidate insights from retrieved context
   - Evaluates insights with RAGAS (faithfulness, relevance, context precision)
   - Filters insights with minimum score threshold (0.7)
   - Returns formatted digest to user

2. **`add_content_source`**
   - Accepts source URL and type (blog, article, manual input)
   - Fetches content from URL
   - Extracts and stores metadata
   - Chunks content intelligently (512 tokens, 50 token overlap)
   - Generates embeddings using HuggingFace models
   - Stores in Supabase with vector index

3. **`update_progress`**
   - Updates user profile with current week number
   - Updates current topics being studied
   - Records completed topics
   - Updates learning preferences
   - Returns updated profile summary

4. **`search_insights`**
   - Accepts semantic query from user
   - Generates query embedding
   - Performs vector similarity search across past insights
   - Applies optional filters (date range, topics, week number)
   - Ranks by relevance and recency
   - Returns formatted results with context

**Infrastructure Requirements:**
- FastMCP server with MCP protocol support
- Supabase database with PostgreSQL + pgvector extension
- HuggingFace embeddings service (sentence-transformers model)
- RAGAS evaluation pipeline
- Basic error handling and logging

**Data Schema:**
- User profile and learning state
- Content sources and raw content storage
- Vector embeddings (content + insights)
- Daily digests and individual insights
- Progress tracking

**Quality Requirements:**
- RAGAS minimum threshold: 0.7 composite score
- Digest generation: 5-7 insights per request
- Vector search: returns relevant results
- Content chunking: preserves context with overlap

### Growth Features (Post-MVP)

**Automated Content Fetching:**
- Twitter integration for auto-fetching tweets from followed accounts
- Reddit integration for subreddit monitoring
- RSS feed support for blog auto-updates
- Scheduled content refresh

**Advanced Personalization:**
- Feedback loop: users rate insights to improve future recommendations
- Adaptive difficulty based on user performance
- Learning pattern detection and optimization
- Spaced repetition scheduling based on retention curves

**Multi-User & Collaboration:**
- Support for multiple user profiles
- Shared content sources across learning cohorts
- Collaborative insights and discussions
- Team/cohort progress tracking

**Analytics & Insights:**
- User engagement dashboard
- Learning progress visualization
- Content source effectiveness metrics
- RAGAS quality trend analysis

**Enhanced Search:**
- Cross-reference between related insights
- Concept mapping and knowledge graphs
- "Similar insights" recommendations
- Export/save favorite insights

### Vision (Future)

**Universal Learning Infrastructure:**
- MCP protocol becomes standard for AI learning assistants
- Integration with major learning platforms and LMS systems
- Open ecosystem of curated content sources
- Community-driven insight quality improvements

**Advanced AI Capabilities:**
- Multi-modal learning (video, audio, code snippets)
- Interactive practice problems generated from insights
- Adaptive curriculum recommendations
- Real-time concept clarification via AI tutor

**Scale & Platform:**
- Support for diverse learning domains beyond tech/bootcamps
- Enterprise learning & development platform integration
- Mobile-optimized digest delivery
- Offline-first capabilities

## Functional Requirements

### MCP Server Infrastructure

- **FR1**: The system can accept connections from MCP-compatible AI clients (Claude, GPT, etc.)
- **FR2**: The system can expose tools via MCP protocol for client invocation
- **FR3**: The system can handle concurrent tool invocations from multiple clients
- **FR4**: The system can return structured responses to MCP tool calls

### User Profile & Learning Progress

- **FR5**: Users can set their current learning week number
- **FR6**: Users can define their current learning topics
- **FR7**: Users can mark topics as completed
- **FR8**: Users can update their learning preferences (difficulty level, content types)
- **FR9**: The system can persist user profile data across sessions
- **FR10**: Users can view their updated profile summary after changes

### Content Source Management

- **FR11**: Users can add content sources by providing a URL
- **FR12**: Users can specify the source type (blog, article, manual input)
- **FR13**: The system can fetch content from provided URLs
- **FR14**: The system can extract metadata from content sources (title, author, publish date)
- **FR15**: The system can chunk content into semantically meaningful segments
- **FR16**: The system can generate vector embeddings for content chunks
- **FR17**: The system can store content and embeddings in the database with vector index

### Daily Digest Generation

- **FR18**: Users can generate a personalized daily learning digest
- **FR19**: The system can retrieve user profile context (current week, topics, preferences) for digest generation
- **FR20**: The system can generate semantic queries based on user's current learning context
- **FR21**: The system can perform vector similarity search to retrieve relevant content chunks
- **FR22**: The system can use LLM to generate candidate insights from retrieved content
- **FR23**: The system can generate 5-7 insights per digest request
- **FR24**: The system can evaluate each insight using RAGAS metrics (faithfulness, relevance, context precision)
- **FR25**: The system can filter insights below quality threshold (0.7 composite score)
- **FR26**: The system can return formatted digest with high-quality insights to the user
- **FR27**: The system can complete digest generation within 30 seconds

### Insight Search & Retrieval

- **FR28**: Users can search past insights using semantic queries
- **FR29**: The system can generate query embeddings for search requests
- **FR30**: The system can perform vector similarity search across stored insights
- **FR31**: Users can apply filters to search results (date range, topics, week number)
- **FR32**: The system can rank search results by relevance and recency
- **FR33**: The system can return formatted search results with contextual information

### Quality Assurance & Evaluation

- **FR34**: The system can measure faithfulness of generated insights to source content
- **FR35**: The system can measure answer relevancy against user's learning context
- **FR36**: The system can measure context precision of retrieved content
- **FR37**: The system can compute composite RAGAS scores for each insight
- **FR38**: The system can reject insights that don't meet minimum quality standards

### Data Persistence & Management

- **FR39**: The system can store user profiles and learning state persistently
- **FR40**: The system can store content sources and raw content
- **FR41**: The system can store vector embeddings with efficient retrieval capabilities
- **FR42**: The system can store daily digests and individual insights
- **FR43**: The system can track progress history over time
- **FR44**: The system can maintain referential integrity between related data (users, content, insights)

### Content Processing Pipeline

- **FR45**: The system can process content in configurable chunk sizes (512 tokens default)
- **FR46**: The system can apply overlapping windows for context preservation (50 tokens default)
- **FR47**: The system can handle various content formats from different source types
- **FR48**: The system can extract and preserve content structure and formatting

### Personalization & Adaptation

- **FR49**: The system can tailor digest insights to user's current learning week
- **FR50**: The system can tailor digest insights to user's specified topics
- **FR51**: The system can adjust content selection based on user preferences
- **FR52**: The system can prioritize recent and relevant content for current learning stage

### Error Handling & Logging

- **FR53**: The system can handle errors gracefully during content fetching
- **FR54**: The system can handle errors gracefully during embedding generation
- **FR55**: The system can handle errors gracefully during digest generation
- **FR56**: The system can log errors and system events for debugging
- **FR57**: The system can return meaningful error messages to users when operations fail

## Non-Functional Requirements

### Performance

**Response Time Requirements:**
- **NFR1**: MCP tool invocations return responses within 30 seconds for digest generation
- **NFR2**: Simple tool calls (`update_progress`, `add_content_source`) complete within 5 seconds
- **NFR3**: Search queries return results within 3 seconds for up to 1000 stored insights

**Throughput Requirements:**
- **NFR4**: The system can handle at least 10 concurrent digest generation requests without performance degradation
- **NFR5**: Vector similarity search maintains sub-3-second response times with up to 100,000 embedded content chunks

**Processing Efficiency:**
- **NFR6**: Content chunking and embedding generation processes at least 10 articles (average 2000 words each) per minute
- **NFR7**: RAGAS evaluation processes 20 candidate insights in parallel within the 30-second digest generation window

### Security

**Data Protection:**
- **NFR8**: All data at rest in Supabase is encrypted using AES-256 encryption
- **NFR9**: All data in transit uses TLS 1.2 or higher for connections between components
- **NFR10**: Database credentials and API keys are stored securely using environment variables or secret management systems

**Access Control:**
- **NFR11**: User profile data is isolated per user with proper access controls preventing cross-user data access
- **NFR12**: MCP client connections are authenticated before tool invocation is permitted
- **NFR13**: Content source URLs are validated and sanitized to prevent injection attacks

**Privacy:**
- **NFR14**: User learning progress, topics, and content sources are treated as private data and not shared without explicit consent
- **NFR15**: System logs do not contain sensitive user information (learning topics, personal preferences)

### Scalability

**User Growth:**
- **NFR16**: The system architecture supports scaling from 10 initial users to 1,000 users with minimal configuration changes
- **NFR17**: Database schema and vector index design accommodate 10x growth in stored content without requiring migration

**Data Growth:**
- **NFR18**: Vector search performance remains acceptable (< 5 second queries) with up to 1 million embedded content chunks
- **NFR19**: Storage architecture supports at least 100 GB of content and embeddings for V1

**Concurrent Load:**
- **NFR20**: The system handles at least 50 concurrent MCP client connections without dropped connections
- **NFR21**: Background processing (embedding generation, RAGAS evaluation) scales horizontally to handle increased load

### Reliability

**Availability:**
- **NFR22**: The MCP server maintains 95% uptime during business hours (9 AM - 6 PM user timezone)
- **NFR23**: Database connections automatically retry on transient failures with exponential backoff

**Data Integrity:**
- **NFR24**: User profile updates are atomic - partial updates do not corrupt user state
- **NFR25**: Content embeddings and source content maintain referential integrity - no orphaned embeddings
- **NFR26**: Failed digest generation attempts do not leave incomplete data in the database

**Error Recovery:**
- **NFR27**: Content fetching failures return meaningful error messages and do not crash the server
- **NFR28**: Embedding service failures are logged and retry automatically up to 3 times before reporting failure
- **NFR29**: MCP tool calls that fail return structured error responses to clients for proper error handling

**Monitoring & Observability:**
- **NFR30**: System logs capture error events with sufficient detail for debugging (error type, stack trace, context)
- **NFR31**: Critical failures (database connection loss, embedding service unavailable) trigger alerts
- **NFR32**: Performance metrics (digest generation time, search latency, RAGAS scores) are logged for analysis
