"""
Content fetcher for ingesting learning content from various sources (RSS feeds, blogs, etc.)
"""

import feedparser
import requests
import ssl
import certifi
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure SSL context for feedparser to use certifi certificates
if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context


class ContentFetcher:
    """Fetches and parses learning content from various sources."""

    def __init__(self):
        """Initialize content fetcher."""
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Learning Coach Bot)"
        })

    async def fetch_rss_feed(
        self,
        feed_url: str,
        max_items: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Fetch and parse RSS feed.

        Args:
            feed_url: URL of the RSS feed
            max_items: Maximum number of items to fetch

        Returns:
            List of parsed feed items
        """
        try:
            feed = feedparser.parse(feed_url)

            if feed.bozo:
                logger.warning(f"Feed parsing warning for {feed_url}: {feed.bozo_exception}")

            items = []
            for entry in feed.entries[:max_items]:
                item = {
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "summary": entry.get("summary", ""),
                    "content": self._extract_content(entry),
                    "published": self._parse_date(entry),
                    "author": entry.get("author", ""),
                    "tags": self._extract_tags(entry),
                    "source_type": "rss",
                    "source_url": feed_url
                }
                items.append(item)

            logger.info(f"Fetched {len(items)} items from {feed_url}")
            return items

        except Exception as e:
            logger.error(f"Error fetching RSS feed {feed_url}: {str(e)}")
            return []

    async def fetch_blog_post(
        self,
        url: str
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch and parse a blog post.

        Args:
            url: URL of the blog post

        Returns:
            Parsed blog post data
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            # Extract title
            title = ""
            title_tag = soup.find("h1") or soup.find("title")
            if title_tag:
                title = title_tag.get_text(strip=True)

            # Extract main content
            content = self._extract_article_content(soup)

            # Extract metadata
            meta_description = ""
            meta_tag = soup.find("meta", attrs={"name": "description"})
            if meta_tag:
                meta_description = meta_tag.get("content", "")

            return {
                "title": title,
                "link": url,
                "summary": meta_description,
                "content": content,
                "published": datetime.utcnow().isoformat(),
                "author": self._extract_author(soup),
                "tags": self._extract_meta_tags(soup),
                "source_type": "blog",
                "source_url": url
            }

        except Exception as e:
            logger.error(f"Error fetching blog post {url}: {str(e)}")
            return None

    def _extract_content(self, entry: Any) -> str:
        """Extract content from RSS entry."""
        if hasattr(entry, "content"):
            return entry.content[0].value
        elif hasattr(entry, "summary"):
            return entry.summary
        elif hasattr(entry, "description"):
            return entry.description
        return ""

    def _extract_article_content(self, soup: BeautifulSoup) -> str:
        """
        Extract main article content from HTML.
        Looks for common article containers.
        """
        # Try common article selectors
        selectors = [
            "article",
            "main",
            ".post-content",
            ".entry-content",
            ".article-content",
            "#content"
        ]

        for selector in selectors:
            article = soup.select_one(selector)
            if article:
                # Remove script and style tags
                for tag in article.find_all(["script", "style", "nav", "footer"]):
                    tag.decompose()
                return article.get_text(separator="\n", strip=True)

        # Fallback: get all paragraph text
        paragraphs = soup.find_all("p")
        return "\n".join(p.get_text(strip=True) for p in paragraphs)

    def _extract_author(self, soup: BeautifulSoup) -> str:
        """Extract author from HTML."""
        # Try common author selectors
        author_selectors = [
            'meta[name="author"]',
            'meta[property="article:author"]',
            ".author",
            ".author-name"
        ]

        for selector in author_selectors:
            author_tag = soup.select_one(selector)
            if author_tag:
                if author_tag.name == "meta":
                    return author_tag.get("content", "")
                return author_tag.get_text(strip=True)

        return ""

    def _extract_tags(self, entry: Any) -> List[str]:
        """Extract tags from RSS entry."""
        tags = []
        if hasattr(entry, "tags"):
            tags = [tag.term for tag in entry.tags if hasattr(tag, "term")]
        return tags

    def _extract_meta_tags(self, soup: BeautifulSoup) -> List[str]:
        """Extract tags/keywords from HTML meta tags."""
        keywords_tag = soup.find("meta", attrs={"name": "keywords"})
        if keywords_tag:
            keywords = keywords_tag.get("content", "")
            return [k.strip() for k in keywords.split(",")]
        return []

    def _parse_date(self, entry: Any) -> str:
        """Parse publication date from RSS entry."""
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            return datetime(*entry.published_parsed[:6]).isoformat()
        elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
            return datetime(*entry.updated_parsed[:6]).isoformat()
        return datetime.utcnow().isoformat()

    async def fetch_multiple_sources(
        self,
        sources: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """
        Fetch content from multiple sources.

        Args:
            sources: List of source dicts with 'source_url' and 'source_type' keys

        Returns:
            Combined list of content items
        """
        all_content = []

        for source in sources:
            url = source.get("source_url", "")
            source_type = source.get("source_type", "rss")

            if source_type == "rss":
                items = await self.fetch_rss_feed(url)
                all_content.extend(items)
            elif source_type == "blog":
                item = await self.fetch_blog_post(url)
                if item:
                    all_content.append(item)

        return all_content


# Singleton instance
_content_fetcher: Optional[ContentFetcher] = None

def get_content_fetcher() -> ContentFetcher:
    """Get or create ContentFetcher instance."""
    global _content_fetcher
    if _content_fetcher is None:
        _content_fetcher = ContentFetcher()
    return _content_fetcher
