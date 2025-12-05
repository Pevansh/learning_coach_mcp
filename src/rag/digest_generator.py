"""
RAG pipeline for generating personalized daily learning digests using vector embeddings and RAGAS.
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from sentence_transformers import SentenceTransformer
import logging

from ..utils.database import get_db_client
from ..utils.groq_client import get_groq_client
from ..ingestion.content_fetcher import get_content_fetcher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DigestGenerator:
    """Generates personalized daily learning digests using RAG."""

    def __init__(self):
        """Initialize the digest generator."""
        self.db = get_db_client()
        self.groq = get_groq_client()
        self.fetcher = get_content_fetcher()

        # Load embedding model
        model_name = os.getenv("DEFAULT_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        logger.info(f"Loading embedding model: {model_name}")
        self.embedding_model = SentenceTransformer(model_name)

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate vector embedding for text.

        Args:
            text: Input text

        Returns:
            Vector embedding as list of floats
        """
        embedding = self.embedding_model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    async def ingest_content_with_embeddings(
        self,
        content_items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Ingest content items and store with embeddings.

        Args:
            content_items: List of content items to ingest

        Returns:
            List of stored content records
        """
        stored_items = []

        for item in content_items:
            try:
                # Combine title and content for embedding
                text_for_embedding = f"{item['title']}\n\n{item['content']}"

                # Generate embedding
                embedding = self.generate_embedding(text_for_embedding)

                # Store in database
                stored_item = await self.db.store_content(
                    title=item["title"],
                    content=item["content"],
                    source_url=item["link"],
                    embedding=embedding,
                    metadata={
                        "summary": item.get("summary", ""),
                        "author": item.get("author", ""),
                        "published": item.get("published", ""),
                        "tags": item.get("tags", []),
                        "source_type": item.get("source_type", "")
                    }
                )

                stored_items.append(stored_item)
                logger.info(f"Ingested content: {item['title'][:50]}...")

            except Exception as e:
                logger.error(f"Error ingesting content '{item.get('title', 'Unknown')}': {str(e)}")

        return stored_items

    async def retrieve_relevant_content(
        self,
        user_context: Dict[str, Any],
        top_k: int = 15
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant content for user based on their topics.

        Args:
            user_context: User's learning context (topics, week, goals)
            top_k: Number of relevant items to retrieve

        Returns:
            List of relevant content items
        """
        # Create query from user's topics
        topics = user_context.get("current_topics", [])
        query_text = " ".join(topics)

        if not query_text:
            logger.warning("No topics provided for content retrieval")
            return []

        logger.info(f"Searching for content with topics: {topics}")
        logger.info(f"Query text: {query_text}")

        # Generate query embedding
        query_embedding = self.generate_embedding(query_text)
        logger.info(f"Generated query embedding with dimension: {len(query_embedding)}")

        # Search database with reasonable threshold
        # Note: Typical semantic similarity scores range from 0.3-0.8 for related content
        relevant_content = await self.db.search_content_by_embedding(
            query_embedding=query_embedding,
            limit=top_k,
            similarity_threshold=0.25  # Lowered from 0.6 to capture more relevant content
        )

        logger.info(f"Retrieved {len(relevant_content)} relevant content items")
        if len(relevant_content) == 0:
            logger.warning("No content found with similarity threshold 0.25")
            logger.warning("Trying with very low threshold 0.15...")
            relevant_content = await self.db.search_content_by_embedding(
                query_embedding=query_embedding,
                limit=top_k,
                similarity_threshold=0.15  # Lowered from 0.3 as fallback
            )
            logger.info(f"Retrieved {len(relevant_content)} items with lower threshold")

        return relevant_content

    async def generate_insights_from_content(
        self,
        content_items: List[Dict[str, Any]],
        user_context: Dict[str, Any],
        max_insights: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Generate personalized insights from content items.

        Args:
            content_items: Retrieved relevant content
            user_context: User's learning context
            max_insights: Maximum number of insights to generate

        Returns:
            List of generated insights with metadata
        """
        insights = []

        for i, item in enumerate(content_items[:max_insights]):
            try:
                # Generate insight using Groq
                insight_text = await self.groq.generate_insight(
                    content=item["content"],
                    user_context=user_context
                )

                # Score relevance
                relevance_score = await self._calculate_relevance_score(
                    item=item,
                    user_context=user_context
                )

                insight = {
                    "insight": insight_text,
                    "content_id": item.get("id"),
                    "title": item.get("title", ""),
                    "source_url": item.get("source_url", ""),
                    "relevance_score": relevance_score,
                    "similarity_score": item.get("similarity", 0.0),
                    "metadata": item.get("metadata", {})
                }

                insights.append(insight)
                logger.info(f"Generated insight {i+1}/{max_insights}")

            except Exception as e:
                logger.error(f"Error generating insight from content: {str(e)}")

        # Sort by relevance score
        insights.sort(key=lambda x: x["relevance_score"], reverse=True)

        return insights

    async def _calculate_relevance_score(
        self,
        item: Dict[str, Any],
        user_context: Dict[str, Any]
    ) -> float:
        """
        Calculate relevance score using RAGAS-inspired metrics.

        Combines:
        - Semantic similarity score
        - Topic relevance from Groq
        - Freshness (newer content scores higher)

        Args:
            item: Content item
            user_context: User context

        Returns:
            Combined relevance score (0.0 to 1.0)
        """
        # Semantic similarity (from vector search)
        similarity_score = item.get("similarity", 0.5)

        # Topic relevance from Groq
        topics = user_context.get("current_topics", [])
        topic_relevance = await self.groq.score_content_relevance(
            content=item["content"][:500],
            user_topics=topics
        )

        # Freshness score (decay over time)
        freshness_score = self._calculate_freshness(
            item.get("metadata", {}).get("published", "")
        )

        # Weighted combination
        relevance_score = (
            0.4 * similarity_score +
            0.4 * topic_relevance +
            0.2 * freshness_score
        )

        return round(relevance_score, 3)

    def _calculate_freshness(self, published_date: str) -> float:
        """Calculate freshness score based on publication date."""
        if not published_date:
            return 0.5

        try:
            pub_date = datetime.fromisoformat(published_date.replace("Z", "+00:00"))
            now = datetime.utcnow()
            days_old = (now - pub_date).days

            # Exponential decay: 1.0 for today, 0.5 for 30 days, 0.1 for 90+ days
            if days_old <= 0:
                return 1.0
            elif days_old <= 7:
                return 0.9
            elif days_old <= 30:
                return 0.7
            elif days_old <= 90:
                return 0.4
            else:
                return 0.2

        except Exception:
            return 0.5

    async def generate_daily_digest(
        self,
        num_insights: int = 7
    ) -> Dict[str, Any]:
        """
        Generate complete daily digest.

        Args:
            num_insights: Number of insights to generate

        Returns:
            Complete daily digest
        """
        # Get user progress/context (default user)
        user_progress = await self.db.get_user_progress()
        if not user_progress:
            raise ValueError("No progress found. Please set your learning progress first using update_progress.")

        user_context = {
            "current_week": user_progress["current_week"],
            "current_topics": user_progress["current_topics"],
            "learning_goals": user_progress.get("learning_goals", "")
        }

        # Retrieve relevant content
        relevant_content = await self.retrieve_relevant_content(
            user_context=user_context,
            top_k=num_insights * 2  # Fetch more than needed
        )

        if not relevant_content:
            return {
                "date": datetime.utcnow().isoformat(),
                "insights": [],
                "summary": "No relevant content found for your topics today."
            }

        # Generate insights
        insights = await self.generate_insights_from_content(
            content_items=relevant_content,
            user_context=user_context,
            max_insights=num_insights
        )

        # Store insights in database
        for insight in insights:
            await self.db.store_daily_insight(
                insight=insight["insight"],
                content_id=insight["content_id"],
                relevance_score=insight["relevance_score"],
                week=user_context["current_week"]
            )

        # Generate summary
        summary = await self.groq.generate_daily_digest_summary(
            insights=[i["insight"] for i in insights],
            user_context=user_context
        )

        return {
            "date": datetime.utcnow().isoformat(),
            "week": user_context["current_week"],
            "topics": user_context["current_topics"],
            "summary": summary,
            "insights": insights,
            "total_insights": len(insights)
        }


# Singleton instance
_digest_generator: Optional[DigestGenerator] = None

def get_digest_generator() -> DigestGenerator:
    """Get or create DigestGenerator instance."""
    global _digest_generator
    if _digest_generator is None:
        _digest_generator = DigestGenerator()
    return _digest_generator
