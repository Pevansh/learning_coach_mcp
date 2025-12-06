"""
Groq client for generating learning insights and summaries.
"""

import os
from typing import List, Dict, Any, Optional
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


class GroqClient:
    """Manages interactions with Groq API for content generation."""

    def __init__(self):
        """Initialize Groq client."""
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY must be set in environment")

        self.client = Groq(api_key=api_key)
        self.default_model = "qwen/qwen3-32b"

    def _extract_final_output(self, text: str) -> str:
        """
        Extract the final output from text that may contain <think> tags.

        Args:
            text: Raw text that may contain thinking process

        Returns:
            Cleaned final output without thinking tags
        """
        # If there are </think> tags, extract everything after the last one
        if "</think>" in text:
            parts = text.split("</think>")
            # Get everything after the last </think> tag
            final_output = parts[-1].strip()

            # If there's actual content after </think>, use it
            if final_output:
                return final_output

            # Otherwise, the model only generated thinking - return error message
            return "Error: Model only generated thinking process, no insight produced."

        # If no </think> tags but has <think>, it means incomplete response
        if "<think>" in text:
            return "Error: Incomplete response - thinking process not finished."

        # No think tags at all, return as-is
        return text.strip()

    async def generate_insight(
        self,
        content: str,
        user_context: Dict[str, Any],
        max_tokens: int = 500
    ) -> str:
        """
        Generate a personalized learning insight from content.

        Args:
            content: The source content to generate insight from
            user_context: User's learning context (week, topics, goals)
            max_tokens: Maximum tokens for the response

        Returns:
            Generated insight string
        """
        current_week = user_context.get("current_week", 1)
        topics = user_context.get("current_topics", [])
        goals = user_context.get("learning_goals", "")

        prompt = f"""You are an AI Learning Coach. Based on the following content and the learner's context, generate a concise, actionable learning insight.

Learner Context:
- Current Week: {current_week}
- Learning Topics: {', '.join(topics)}
- Learning Goals: {goals}

Content:
{content[:1000]}

Generate a single, focused learning insight that:
1. Is relevant to their current week and topics
2. Provides actionable advice or key takeaway
3. Is appropriate for their learning level
4. Is concise (2-3 sentences)

IMPORTANT: After your analysis, provide ONLY the final insight text without any thinking process, tags, or explanations.

Insight:"""

        response = self.client.chat.completions.create(
            model=self.default_model,
            messages=[
                {"role": "system", "content": "You are an expert AI Learning Coach who creates personalized, actionable learning insights. Provide only the final insight without showing your thinking process."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.7
        )

        raw_output = response.choices[0].message.content.strip()
        return self._extract_final_output(raw_output)

    async def generate_daily_digest_summary(
        self,
        insights: List[str],
        user_context: Dict[str, Any]
    ) -> str:
        """
        Generate a summary introduction for the daily digest.

        Args:
            insights: List of insights for the day
            user_context: User's learning context

        Returns:
            Summary introduction string
        """
        current_week = user_context.get("current_week", 1)
        topics = user_context.get("current_topics", [])

        prompt = f"""Create a brief, motivating introduction for today's learning digest.

Context:
- Week {current_week} of learning journey
- Focus topics: {', '.join(topics)}
- Number of insights: {len(insights)}

Write a 2-3 sentence introduction that:
1. Acknowledges their progress
2. Highlights the key theme of today's insights
3. Encourages engagement

Introduction:"""

        response = self.client.chat.completions.create(
            model=self.default_model,
            messages=[
                {"role": "system", "content": "You are a supportive AI Learning Coach."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.8
        )

        return response.choices[0].message.content.strip()

    async def score_content_relevance(
        self,
        content: str,
        user_topics: List[str]
    ) -> float:
        """
        Score how relevant content is to user's current topics (0.0 to 1.0).

        Args:
            content: The content to score
            user_topics: User's current learning topics

        Returns:
            Relevance score between 0.0 and 1.0
        """
        prompt = f"""Rate the relevance of this content to the following learning topics on a scale of 0.0 to 1.0.

Topics: {', '.join(user_topics)}

Content:
{content[:500]}

Provide only a single number between 0.0 (not relevant) and 1.0 (highly relevant).

Score:"""

        response = self.client.chat.completions.create(
            model="qwen/qwen3-32b",
            messages=[
                {"role": "system", "content": "You are a content relevance evaluator. Respond only with a decimal number."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=10,
            temperature=0.3
        )

        try:
            score = float(response.choices[0].message.content.strip())
            return max(0.0, min(1.0, score))
        except ValueError:
            return 0.5

    async def extract_key_concepts(
        self,
        content: str,
        max_concepts: int = 5
    ) -> List[str]:
        """
        Extract key concepts from content.

        Args:
            content: The content to analyze
            max_concepts: Maximum number of concepts to extract

        Returns:
            List of key concepts
        """
        prompt = f"""Extract up to {max_concepts} key technical concepts or topics from this content.
Return them as a comma-separated list.

Content:
{content[:1000]}

Key Concepts:"""

        response = self.client.chat.completions.create(
            model="qwen/qwen3-32b",
            messages=[
                {"role": "system", "content": "You are a content analyzer. Extract key concepts as a comma-separated list."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.3
        )

        concepts_text = response.choices[0].message.content.strip()
        concepts = [c.strip() for c in concepts_text.split(",")]
        return concepts[:max_concepts]


# Singleton instance
_groq_client: Optional[GroqClient] = None

def get_groq_client() -> GroqClient:
    """Get or create Groq client instance."""
    global _groq_client
    if _groq_client is None:
        _groq_client = GroqClient()
    return _groq_client
