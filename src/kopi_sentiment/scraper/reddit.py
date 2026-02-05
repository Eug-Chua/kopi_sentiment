"""Reddit scraper with pluggable fetch strategies (JSON primary, HTML fallback).

Uses the Strategy Pattern (OCP) so new fetch methods can be added without
modifying existing code. Each strategy implements the RedditFetcher protocol.
"""

import time
from datetime import datetime
from typing import Protocol
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
from kopi_sentiment.config.settings import settings
import logging

logger = logging.getLogger(__name__)


# ---- Models ----

class Comment(BaseModel):
    """Represents a Reddit comment"""
    text: str
    score: int

class RedditPost(BaseModel):
    """Represents a Reddit post"""
    id: str
    title: str
    url: str
    score: int
    num_comments: int
    created_at: datetime
    subreddit: str = ""
    selftext: str = ""
    comments: list[Comment] = []


# ---- Fetcher Protocol (ISP / DIP) ----

class RedditFetcher(Protocol):
    """Protocol for Reddit data fetching strategies."""

    def fetch_posts(self, subreddit: str, limit: int, sort: str, time_filter: str) -> list[RedditPost]: ...
    def fetch_post_content(self, post: RedditPost) -> str: ...
    def fetch_post_comments(self, post: RedditPost, limit: int) -> list[Comment]: ...
    def search_posts(self, subreddit: str, query: str, limit: int, sort: str, time_filter: str) -> list[RedditPost]: ...


# ---- JSON Fetcher Strategy ----

class JsonRedditFetcher:
    """Fetches Reddit data using old.reddit.com JSON endpoints."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': settings.reddit_user_agent,
            'Accept': 'application/json',
        })

    def fetch_posts(self, subreddit: str, limit: int, sort: str, time_filter: str) -> list[RedditPost]:
        if sort == "hot":
            url = f"{settings.reddit_base_url}/r/{subreddit}.json"
        else:
            url = f"{settings.reddit_base_url}/r/{subreddit}/{sort}.json"

        params = {"limit": limit}
        if sort == "top":
            params["t"] = time_filter

        response = self.session.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        posts = []
        for child in data.get("data", {}).get("children", []):
            post = _parse_json_post(child.get("data", {}))
            if post:
                posts.append(post)
        return posts

    def fetch_post_content(self, post: RedditPost) -> str:
        url = post.url.rstrip("/") + ".json"
        response = self.session.get(url)
        response.raise_for_status()

        data = response.json()
        if isinstance(data, list) and len(data) > 0:
            children = data[0].get("data", {}).get("children", [])
            if children:
                return children[0].get("data", {}).get("selftext", "")
        return ""

    def fetch_post_comments(self, post: RedditPost, limit: int) -> list[Comment]:
        url = post.url.rstrip("/") + ".json"
        params = {"limit": limit}
        response = self.session.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        if not isinstance(data, list) or len(data) < 2:
            return []

        comment_children = data[1].get("data", {}).get("children", [])
        comments = []
        for child in comment_children:
            if child.get("kind") != "t1":
                continue
            cdata = child.get("data", {})
            body = cdata.get("body", "")
            score = cdata.get("score", 0)
            if body:
                comments.append(Comment(text=body, score=score))

        comments.sort(key=lambda x: x.score, reverse=True)
        return comments

    def search_posts(self, subreddit: str, query: str, limit: int, sort: str, time_filter: str) -> list[RedditPost]:
        url = f"{settings.reddit_base_url}/r/{subreddit}/search.json"
        params = {
            "q": query,
            "restrict_sr": "on",
            "sort": sort,
            "t": time_filter,
            "limit": limit,
        }

        response = self.session.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        posts = []
        for child in data.get("data", {}).get("children", []):
            post = _parse_json_post(child.get("data", {}))
            if post:
                posts.append(post)
        return posts


# ---- HTML Scraping Fetcher Strategy ----

class HtmlRedditFetcher:
    """Fetches Reddit data by scraping old.reddit.com HTML pages."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        })

    def fetch_posts(self, subreddit: str, limit: int, sort: str, time_filter: str) -> list[RedditPost]:
        if sort == "hot":
            url = f"{settings.reddit_base_url}/r/{subreddit}"
        else:
            url = f"{settings.reddit_base_url}/r/{subreddit}/{sort}"

        params = {}
        if sort == "top":
            params["t"] = time_filter

        response = self.session.get(url, params=params)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        post_elements = soup.find_all('div', class_='thing', limit=limit)

        posts = []
        for element in post_elements:
            post = _parse_html_post(element)
            if post:
                posts.append(post)
        return posts

    def fetch_post_content(self, post: RedditPost) -> str:
        response = self.session.get(post.url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        site_table = soup.find("div", id="siteTable")
        if not site_table:
            return ""

        expando = site_table.find("div", class_="expando")
        if not expando:
            return ""

        usertext = expando.find("div", class_="usertext-body")
        if usertext:
            paragraphs = usertext.find_all("p")
            if paragraphs:
                return "\n\n".join(p.get_text(strip=True) for p in paragraphs)
        return ""

    def fetch_post_comments(self, post: RedditPost, limit: int) -> list[Comment]:
        response = self.session.get(post.url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        comments_area = soup.find('div', class_='commentarea')
        if not comments_area:
            return []

        comment_containers = comments_area.find_all('div',
                                                    class_='thing',
                                                    attrs={'data-type': 'comment'},
                                                    limit=limit)
        comments = []
        for container in comment_containers:
            score_elem = container.find('span', class_='score unvoted')
            score = 0
            if score_elem:
                score_text = score_elem.get_text(strip=True)
                try:
                    score = int(score_text.split()[0])
                except (ValueError, IndexError):
                    score = 0

            body_div = container.find('div', class_='usertext-body')
            if body_div:
                paragraphs = body_div.find_all('p')
                if paragraphs:
                    text = " ".join(p.get_text(strip=True) for p in paragraphs)
                    if text:
                        comments.append(Comment(text=text, score=score))

        comments.sort(key=lambda x: x.score, reverse=True)
        return comments

    def search_posts(self, subreddit: str, query: str, limit: int, sort: str, time_filter: str) -> list[RedditPost]:
        url = f"{settings.reddit_base_url}/r/{subreddit}/search"
        params = {
            "q": query,
            "restrict_sr": "on",
            "sort": sort,
            "t": time_filter,
        }

        response = self.session.get(url, params=params)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        result_elements = soup.find_all("div", class_="search-result", limit=limit)

        posts = []
        for element in result_elements:
            post = _parse_search_result(element)
            if post:
                posts.append(post)
        return posts


# ---- Orchestrator (SRP: only handles fallback logic and composition) ----

class RedditScraper:
    """Orchestrates Reddit fetching with fallback strategies.

    Tries each fetcher in order until one succeeds. Default order:
    JSON endpoints first, HTML scraping as fallback.
    """

    def __init__(self, subreddit: str | None = None, fetchers: list[RedditFetcher] | None = None):
        self.subreddit = subreddit or settings.reddit_subreddit[0]
        self.fetchers: list[RedditFetcher] = fetchers or [JsonRedditFetcher(), HtmlRedditFetcher()]

    def _try_fetchers(self, operation: str, func):
        """Try each fetcher in order until one succeeds (DRY)."""
        last_error = None
        for fetcher in self.fetchers:
            try:
                return func(fetcher)
            except Exception as e:
                fetcher_name = type(fetcher).__name__
                logger.warning(f"{fetcher_name}.{operation} failed: {e}")
                last_error = e
        raise last_error

    def fetch_posts(self, limit: int = 25, sort: str = "hot", time_filter: str = "week") -> list[RedditPost]:
        """Fetch posts from subreddit, trying each strategy in order."""
        return self._try_fetchers(
            "fetch_posts",
            lambda f: f.fetch_posts(self.subreddit, limit, sort, time_filter)
        )

    def fetch_post_content(self, post: RedditPost) -> str:
        """Fetch the full selftext content for a post."""
        return self._try_fetchers(
            "fetch_post_content",
            lambda f: f.fetch_post_content(post)
        )

    def fetch_post_comments(self, post: RedditPost, limit: int = 25) -> list[Comment]:
        """Fetch top comments for a post."""
        return self._try_fetchers(
            "fetch_post_comments",
            lambda f: f.fetch_post_comments(post, limit)
        )

    def search_posts(self, query: str, limit: int = 25, sort: str = "comments", time_filter: str = "month") -> list[RedditPost]:
        """Search for posts matching a query."""
        return self._try_fetchers(
            "search_posts",
            lambda f: f.search_posts(self.subreddit, query, limit, sort, time_filter)
        )

    def fetch_posts_with_content(self, limit: int = 25, delay: float = 1.0, sort: str = "hot", time_filter: str = "week") -> list[RedditPost]:
        """Fetch posts and their full content with rate limiting.

        Args:
            limit: Maximum number of posts to fetch
            delay: Delay between requests to avoid rate limiting
            sort: Sort order - "hot", "new", "top", "rising"
            time_filter: Time range for "top" sort - "hour", "day", "week", "month", "year", "all"
        """
        raw_posts = self.fetch_posts(limit=limit + 2, sort=sort, time_filter=time_filter)
        posts = [p for p in raw_posts if p.subreddit == self.subreddit][:limit]

        for post in posts:
            # JSON listing already includes selftext; only fetch if empty
            if not post.selftext:
                post.selftext = self.fetch_post_content(post)
            post.comments = self.fetch_post_comments(post)
            time.sleep(delay)

        return posts

    def search_posts_with_content(self, query: str, limit: int = 10, sort: str = "comments",
                                  time_filter: str = "month", delay: float = 1.0) -> list[RedditPost]:
        """Search for posts and fetch their content and comments.

        Args:
            query: Search term (e.g., "layoffs", "AI", "HDB")
            limit: Maximum number of posts to return
            sort: Sort order - "relevance", "new", "top", "comments"
            time_filter: Time range - "hour", "day", "week", "month", "year", "all"
            delay: Delay between requests to avoid rate limiting
        """
        posts = self.search_posts(query, limit=limit, sort=sort, time_filter=time_filter)

        for post in posts:
            if not post.selftext:
                post.selftext = self.fetch_post_content(post)
            post.comments = self.fetch_post_comments(post)
            time.sleep(delay)

        return posts


# ---- Parsing helpers (pure functions, no state) ----

def _parse_json_post(post_data: dict) -> RedditPost | None:
    """Parse a single post from Reddit JSON response."""
    try:
        created_utc = post_data.get("created_utc", 0)
        return RedditPost(
            id=post_data.get("name", ""),
            title=post_data.get("title", ""),
            url=f"{settings.reddit_base_url}{post_data.get('permalink', '')}",
            score=post_data.get("score", 0),
            num_comments=post_data.get("num_comments", 0),
            created_at=datetime.fromtimestamp(created_utc),
            subreddit=post_data.get("subreddit", ""),
            selftext=post_data.get("selftext", ""),
        )
    except Exception as e:
        logger.error(f"Error parsing JSON post: {e}")
        return None


def _parse_html_post(post_element) -> RedditPost | None:
    """Parse a single post from old.reddit.com HTML."""
    try:
        post_id = post_element.get('data-fullname', "")
        score = int(post_element.get('data-score', 0))
        num_comments = int(post_element.get('data-comments-count', 0))
        timestamp_ms = int(post_element.get('data-timestamp', 0))
        permalink = post_element.get('data-permalink', "")
        subreddit = post_element.get('data-subreddit', "")

        title_element = post_element.find('a', class_='title')
        title = title_element.get_text(strip=True) if title_element else ""
        created_at = datetime.fromtimestamp(timestamp_ms / 1000)
        url = f"{settings.reddit_base_url}{permalink}"

        return RedditPost(
            id=post_id,
            title=title,
            url=url,
            score=score,
            num_comments=num_comments,
            subreddit=subreddit,
            created_at=created_at,
            selftext=""
        )
    except Exception as e:
        logger.error(f"Error parsing HTML post: {e}")
        return None


def _parse_search_result(element) -> RedditPost | None:
    """Parse a single post from search results HTML."""
    try:
        post_id = element.get("data-fullname", "")

        title_elem = element.find("a", class_="search-title")
        title = title_elem.get_text(strip=True) if title_elem else ""

        url = title_elem.get("href", "") if title_elem else ""
        if url and not url.startswith("http"):
            url = f"{settings.reddit_base_url}{url}"

        score_elem = element.find("span", class_="search-score")
        score = 0
        if score_elem:
            score_text = score_elem.get_text(strip=True)
            try:
                score = int(score_text.split()[0])
            except (ValueError, IndexError):
                score = 0

        comments_elem = element.find("a", class_="search-comments")
        num_comments = 0
        if comments_elem:
            comments_text = comments_elem.get_text(strip=True)
            try:
                num_comments = int(comments_text.split()[0])
            except (ValueError, IndexError):
                num_comments = 0

        time_elem = element.find("time")
        created_at = datetime.now()
        if time_elem and time_elem.get("datetime"):
            dt_str = time_elem.get("datetime")
            created_at = datetime.fromisoformat(dt_str.replace("+00:00", ""))

        subreddit_elem = element.find("a", class_="search-subreddit-link")
        subreddit = ""
        if subreddit_elem:
            subreddit = subreddit_elem.get_text(strip=True).replace("r/", "")

        return RedditPost(
            id=post_id,
            title=title,
            url=url,
            score=score,
            num_comments=num_comments,
            created_at=created_at,
            subreddit=subreddit,
            selftext="",
            comments=[],
        )
    except Exception as e:
        logger.error(f"Error parsing search result: {e}")
        return None