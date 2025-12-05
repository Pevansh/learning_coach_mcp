"""
Supabase database client with pgvector support for the Learning Coach MCP server.
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()


class SupabaseClient:
    """Manages interactions with Supabase database."""

    def __init__(self):
        """Initialize Supabase client."""
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")

        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment")

        self.client: Client = create_client(self.url, self.key)

    # Content Sources Management
    async def add_content_source(
        self,
        source_url: str,
        source_type: str,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Add a new content source (blog, RSS feed, etc.)."""
        data = {
            "source_url": source_url,
            "source_type": source_type,
            "tags": tags or [],
            "created_at": datetime.utcnow().isoformat()
        }

        result = self.client.table("content_sources").insert(data).execute()
        return result.data[0] if result.data else {}

    async def get_content_sources(self, source_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve all content sources or filter by type."""
        query = self.client.table("content_sources").select("*")

        if source_type:
            query = query.eq("source_type", source_type)

        result = query.execute()
        return result.data

    # Learning Content Storage
    async def store_content(
        self,
        title: str,
        content: str,
        source_url: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Store learning content with vector embedding."""
        data = {
            "title": title,
            "content": content,
            "source_url": source_url,
            "embedding": embedding,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat()
        }

        result = self.client.table("learning_content").insert(data).execute()
        return result.data[0] if result.data else {}

    async def search_content_by_embedding(
        self,
        query_embedding: List[float],
        limit: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search content using vector similarity."""
        # Using Supabase's pgvector similarity search
        result = self.client.rpc(
            "match_learning_content",
            {
                "query_embedding": query_embedding,
                "match_threshold": similarity_threshold,
                "match_count": limit
            }
        ).execute()

        return result.data

    # User Progress Management
    async def update_user_progress(
        self,
        current_week: int,
        current_topics: List[str],
        learning_goals: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update learning progress (single user system)."""
        data = {
            "user_id": "default",  # Single user system
            "current_week": current_week,
            "current_topics": current_topics,
            "learning_goals": learning_goals,
            "updated_at": datetime.utcnow().isoformat()
        }

        # Upsert - update if exists, insert if not
        result = self.client.table("user_progress").upsert(data).execute()
        return result.data[0] if result.data else {}

    async def get_user_progress(self) -> Optional[Dict[str, Any]]:
        """Get current learning progress (single user system)."""
        result = self.client.table("user_progress").select("*").eq("user_id", "default").execute()
        return result.data[0] if result.data else None

    # Daily Insights Management
    async def store_daily_insight(
        self,
        insight: str,
        content_id: int,
        relevance_score: float,
        week: int
    ) -> Dict[str, Any]:
        """Store a generated daily insight (single user system)."""
        data = {
            "user_id": "default",  # Single user system
            "insight": insight,
            "content_id": content_id,
            "relevance_score": relevance_score,
            "week": week,
            "created_at": datetime.utcnow().isoformat()
        }

        result = self.client.table("daily_insights").insert(data).execute()
        return result.data[0] if result.data else {}

    async def get_daily_insights(
        self,
        date: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Retrieve daily insights (single user system)."""
        query = self.client.table("daily_insights").select("*").eq("user_id", "default")

        if date:
            # Filter by specific date
            query = query.gte("created_at", f"{date}T00:00:00").lte("created_at", f"{date}T23:59:59")

        result = query.order("created_at", desc=True).limit(limit).execute()
        return result.data

    async def search_insights(
        self,
        search_query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search through past insights using full-text search (single user system)."""
        result = self.client.table("daily_insights") \
            .select("*") \
            .eq("user_id", "default") \
            .text_search("insight", search_query) \
            .limit(limit) \
            .execute()

        return result.data


# Singleton instance
_db_client: Optional[SupabaseClient] = None

def get_db_client() -> SupabaseClient:
    """Get or create Supabase client instance."""
    global _db_client
    if _db_client is None:
        _db_client = SupabaseClient()
    return _db_client
