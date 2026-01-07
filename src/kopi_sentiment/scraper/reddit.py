"""Reddit scaper using webscraping (fallback when API not available)"""

import time
from datetime import datetime
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
from kopi_sentiment.config.settings import settings
import logging

logger = logging.getLogger(__name__)

class RedditPost(BaseModel):
    """Represents a Reddit post"""
    id: str
    title: str
    url: str
    score: int
    num_comments: int
    created_at: datetime
    selftext: str = ""

class RedditScraper:
    """Scrapes Reddit posts from old.reddit.com"""

    def __init__(self, subreddit: str | None = None):
        # use provided subreddit or first from settings
        self.subreddit = subreddit or settings.reddit_subreddit[0]
        # use sessions so we appear as a normal user browsing and not a script/bot
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': settings.reddit_user_agent
        })

    def fetch_posts(self, limit: int=25) -> list[RedditPost]:
        """Fetch posts from subreddit"""
        url = f"{settings.reddit_base_url}/r/{self.subreddit}"
        posts = []
        response = self.session.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        post_elements = soup.find_all('div', class_='thing', limit=limit)

        for element in post_elements:
            post = self._parse_post(element)
            if post:
                posts.append(post)
        
        return posts

    def _parse_post(self, post_element):
        """Parse a single post from HTML"""
        try:
            # get data from attributes
            post_id = post_element.get('data-fullname', "")
            score = int(post_element.get('data-score', 0))
            num_comments = int(post_element.get('data-comments-count', 0))
            timestamp_ms = int(post_element.get('data-timestamp', 0))
            permalink = post_element.get('data-permalink', "")

            # get title
            title_element = post_element.find('a', class_='title')
            title = title_element.get_text(strip=True) if title_element else ""

            # convert timestamp to datetime
            created_at = datetime.fromtimestamp(timestamp_ms / 1000)

            # build full URL
            url = f"{settings.reddit_base_url}{permalink}"

            return RedditPost(
                id = post_id,
                title=title,
                url=url,
                score=score,
                num_comments=num_comments,
                created_at=created_at,
                selftext=""
            )
        except Exception as e:
            logger.error(f"Error parsing post: {e}")
            return None
        
    def fetch_post_content(self, post: RedditPost) -> str:
        """Fetch the full selftext content from a post's page"""
        try:
            response = self.session.get(post.url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # find the post's selftext div
            selftext_div = soup.find('div', class_='usertext-body')

            if selftext_div:
                return selftext_div.get_text(strip=True)
            return ""
        except Exception as e:
            logger.error(f"Error fetching post content: {e}")
            return ""
    
    def fetch_posts_with_content(self, limit: int=25, delay: float=1.0) -> list[RedditPost]:
        """Fetch posts and their full content with rate limiting"""
        posts = self.fetch_posts(limit=limit)
        for post in posts:
            post.selftext = self.fetch_post_content(post)
            time.sleep(delay)

        return posts