"""
Main MCP server for the AI Learning Coach.
Provides tools for generating daily digests, managing content sources, and tracking progress.
"""

from typing import Any
import logging
from datetime import datetime

from fastmcp import FastMCP
from pydantic import Field

from .utils.database import get_db_client
from .utils.groq_client import get_groq_client
from .ingestion.content_fetcher import get_content_fetcher
from .rag.digest_generator import get_digest_generator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("Learning Coach")

# Initialize components
db = get_db_client()
groq_client = get_groq_client()
content_fetcher = get_content_fetcher()
digest_generator = get_digest_generator()


@mcp.tool()
async def generate_daily_digest(
    num_insights: int = Field(default=7, description="Number of insights to generate (default: 7)")
) -> dict[str, Any]:
    """
    Generate personalized daily learning digest with insights based on current topics and week.

    This tool:
    1. Retrieves relevant content from the database using RAG
    2. Generates personalized insights using AI
    3. Scores each insight for relevance using RAGAS metrics
    4. Returns a curated digest of learning insights
    """
    try:
        logger.info("Generating daily digest")

        digest = await digest_generator.generate_daily_digest(
            num_insights=num_insights
        )

        return {
            "success": True,
            "digest": digest
        }

    except Exception as e:
        logger.error(f"Error generating daily digest: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def add_content_source(
    source_url: str = Field(description="URL of the content source (RSS feed or blog)"),
    source_type: str = Field(description="Type of source: 'rss' or 'blog'"),
    tags: list[str] = Field(default_factory=list, description="Tags to categorize the source"),
    ingest_now: bool = Field(default=True, description="Whether to immediately ingest content from this source")
) -> dict[str, Any]:
    """
    Add a new content source (blog, RSS feed, etc.) to the learning coach.

    Optionally ingests content immediately and stores it with embeddings for future retrieval.
    """
    try:
        logger.info(f"Adding content source: {source_url}")

        # Add source to database
        source = await db.add_content_source(
            source_url=source_url,
            source_type=source_type,
            tags=tags
        )

        ingested_count = 0

        # Optionally ingest content immediately
        if ingest_now:
            logger.info(f"Ingesting content from {source_url}")

            if source_type == "rss":
                content_items = await content_fetcher.fetch_rss_feed(source_url)
            elif source_type == "blog":
                content_item = await content_fetcher.fetch_blog_post(source_url)
                content_items = [content_item] if content_item else []
            else:
                return {
                    "success": False,
                    "error": f"Unsupported source_type: {source_type}"
                }

            # Ingest with embeddings
            stored_items = await digest_generator.ingest_content_with_embeddings(content_items)
            ingested_count = len(stored_items)

        return {
            "success": True,
            "source": source,
            "ingested_count": ingested_count
        }

    except Exception as e:
        logger.error(f"Error adding content source: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def update_progress(
    current_week: int = Field(description="Current week number in the learning journey"),
    current_topics: list[str] = Field(description="List of topics currently learning"),
    learning_goals: str = Field(default="", description="Learning goals (optional)")
) -> dict[str, Any]:
    """
    Update learning progress, including current week, topics, and goals.

    This information is used to personalize the daily digest.
    """
    try:
        logger.info("Updating progress")

        progress = await db.update_user_progress(
            current_week=current_week,
            current_topics=current_topics,
            learning_goals=learning_goals
        )

        return {
            "success": True,
            "progress": progress
        }

    except Exception as e:
        logger.error(f"Error updating progress: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def search_insights(
    query: str = Field(description="Search query for past insights"),
    limit: int = Field(default=10, description="Maximum number of results to return")
) -> dict[str, Any]:
    """
    Search through past learning insights using full-text search.

    Useful for reviewing previous learnings or finding specific topics.
    """
    try:
        logger.info(f"Searching insights: {query}")

        insights = await db.search_insights(
            search_query=query,
            limit=limit
        )

        return {
            "success": True,
            "query": query,
            "results": insights,
            "count": len(insights)
        }

    except Exception as e:
        logger.error(f"Error searching insights: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def get_progress() -> dict[str, Any]:
    """
    Get current learning progress.

    Returns current week, topics, and learning goals.
    """
    try:
        logger.info("Getting progress")

        progress = await db.get_user_progress()

        if not progress:
            return {
                "success": False,
                "error": "No progress found"
            }

        return {
            "success": True,
            "progress": progress
        }

    except Exception as e:
        logger.error(f"Error getting progress: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def ingest_content_from_sources(
    source_type: str = Field(default="all", description="Filter by source type: 'rss', 'blog', or 'all'"),
    max_items_per_source: int = Field(default=10, description="Maximum items to ingest per source")
) -> dict[str, Any]:
    """
    Manually trigger content ingestion from all configured sources.

    Fetches new content, generates embeddings, and stores in the database.
    """
    try:
        logger.info(f"Ingesting content from sources (type: {source_type})")

        # Get content sources
        if source_type == "all":
            sources = await db.get_content_sources()
        else:
            sources = await db.get_content_sources(source_type=source_type)

        if not sources:
            return {
                "success": False,
                "error": "No content sources found"
            }

        # Fetch content
        content_items = await content_fetcher.fetch_multiple_sources(sources)

        # Ingest with embeddings
        stored_items = await digest_generator.ingest_content_with_embeddings(content_items)

        return {
            "success": True,
            "sources_processed": len(sources),
            "items_ingested": len(stored_items)
        }

    except Exception as e:
        logger.error(f"Error ingesting content: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def get_today_insights() -> dict[str, Any]:
    """
    Retrieve today's generated insights.

    Returns previously generated insights from today if available.
    """
    try:
        logger.info("Getting today's insights")

        today = datetime.utcnow().date().isoformat()
        insights = await db.get_daily_insights(
            date=today
        )

        return {
            "success": True,
            "date": today,
            "insights": insights,
            "count": len(insights)
        }

    except Exception as e:
        logger.error(f"Error getting today's insights: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def debug_system_status() -> dict[str, Any]:
    """
    Get diagnostic information about the system status.

    Returns information about:
    - User progress
    - Number of content sources
    - Number of ingested content items
    - Sample content to verify embeddings
    """
    try:
        logger.info("Running system diagnostics")

        # Check user progress
        progress = await db.get_user_progress()

        # Check content sources
        sources = await db.get_content_sources()

        # Check total content count
        content_count_query = db.client.table("learning_content").select("id", count="exact").execute()
        content_count = content_count_query.count if hasattr(content_count_query, 'count') else 0

        # Get sample content
        sample_content = db.client.table("learning_content").select("id, title, created_at").limit(5).execute()

        # Check if embeddings exist
        embedding_check = db.client.table("learning_content").select("id, title").not_.is_("embedding", "null").limit(1).execute()
        has_embeddings = len(embedding_check.data) > 0

        return {
            "success": True,
            "diagnostics": {
                "user_progress": progress,
                "content_sources_count": len(sources),
                "content_sources": sources,
                "total_content_items": content_count,
                "sample_content": sample_content.data,
                "has_embeddings": has_embeddings
            }
        }

    except Exception as e:
        logger.error(f"Error running diagnostics: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def test_vector_search(
    test_query: str = Field(default="agents", description="Query text to test vector search with")
) -> dict[str, Any]:
    """
    Test vector search to debug why no content is being found.

    This tool helps diagnose issues by:
    - Generating an embedding for your query
    - Testing with multiple similarity thresholds
    - Showing what content exists in the database
    """
    try:
        logger.info(f"Testing vector search with query: {test_query}")

        # Generate embedding for test query
        query_embedding = digest_generator.generate_embedding(test_query)
        logger.info(f"Generated embedding with dimension: {len(query_embedding)}")

        # Test with different thresholds
        results = {}
        thresholds = [0.1, 0.3, 0.5, 0.6, 0.7, 0.8]

        for threshold in thresholds:
            content = await db.search_content_by_embedding(
                query_embedding=query_embedding,
                limit=5,
                similarity_threshold=threshold
            )
            results[f"threshold_{threshold}"] = {
                "count": len(content),
                "items": [{"title": item.get("title", ""), "similarity": item.get("similarity", 0)} for item in content]
            }

        # Get all content (to see what exists)
        all_content = db.client.table("learning_content").select("id, title").limit(10).execute()

        return {
            "success": True,
            "test_query": test_query,
            "embedding_dimension": len(query_embedding),
            "search_results_by_threshold": results,
            "total_content_in_db": len(all_content.data),
            "sample_content_titles": [item.get("title", "") for item in all_content.data]
        }

    except Exception as e:
        logger.error(f"Error testing vector search: {str(e)}")
        import traceback
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }


# Entry point for running the server
if __name__ == "__main__":
    logger.info("Starting Learning Coach MCP Server...")
    mcp.run()
