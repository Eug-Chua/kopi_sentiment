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
    comments: list[str] = []

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

    def fetch_posts(self, limit: int=25, sort: str = "hot", time_filter: str = "week") -> list[RedditPost]:
        """Fetch posts from subreddit.

        Args:
            limit: Maximum number of posts to fetch
            sort: Sort order - "hot", "new", "top", "rising"
            time_filter: Time range for "top" sort - "hour", "day", "week", "month", "year", "all"
        """
        # Build URL based on sort type
        if sort == "hot":
            url = f"{settings.reddit_base_url}/r/{self.subreddit}"
        else:
            url = f"{settings.reddit_base_url}/r/{self.subreddit}/{sort}"

        # Add time filter for "top" sort
        params = {}
        if sort == "top":
            params["t"] = time_filter

        posts = []
        response = self.session.get(url, params=params)
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
            subreddit = post_element.get('data-subreddit', "")

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
                subreddit=subreddit,
                created_at=created_at,
                selftext=""
            )
        except Exception as e:
            logger.error(f"Error parsing post: {e}")
            return None
        
    def fetch_post_content(self, post: RedditPost) -> str:
        """Fetch the full selftext content from a post's page."""
        try:
            response = self.session.get(post.url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Find the main post area (siteTable contains the OP)
            site_table = soup.find("div", id="siteTable")
            if not site_table:
                return ""
            
            # Find the post's expando (contains selftext for text posts)
            expando = site_table.find("div", class_="expando")
            if not expando:
                return ""  # This is a link post - no selftext
            
            # Find usertext-body within the expando
            usertext = expando.find("div", class_="usertext-body")
            if usertext:
                paragraphs = usertext.find_all("p")
                if paragraphs:
                    return "\n\n".join(p.get_text(strip=True) for p in paragraphs)
            
            return ""
            
        except Exception as e:
            logger.error(f"Error fetching post content: {e}")
            return ""

    
    def fetch_posts_with_content(self, limit: int=25, delay: float=1.0, sort: str = "hot", time_filter: str = "week") -> list[RedditPost]:
        """Fetch posts and their full content with rate limiting.

        Args:
            limit: Maximum number of posts to fetch
            delay: Delay between requests to avoid rate limiting
            sort: Sort order - "hot", "new", "top", "rising"
            time_filter: Time range for "top" sort - "hour", "day", "week", "month", "year", "all"
        """
        posts = self.fetch_posts(limit=limit, sort=sort, time_filter=time_filter)
        for post in posts:
            post.selftext = self.fetch_post_content(post)
            post.comments = self.fetch_post_comments(post)
            time.sleep(delay)

        return posts

    def fetch_post_comments(self, post: RedditPost, limit:int = 25) -> list[str]:
        """Fetch top comments"""
        try:
            response = self.session.get(post.url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # find comment area
            comments_area = soup.find('div', class_='commentarea')
            if not comments_area:
                return []

            # find all comment containers
            comment_containers = comments_area.find_all('div',
                                                        class_='thing',
                                                        attrs={'data-type':'comment'},
                                                        limit=limit)

            comments = []
            for container in comment_containers:
                # get score
                score_elem = container.find('span', class_='score unvoted')
                score = 0
                if score_elem:
                    score_text = score_elem.get_text(strip=True)
                    try:
                        score = int(score_text.split()[0])
                    except (ValueError, IndexError):
                        score = 0
                else:
                    # check if score is hidden
                    hidden_elem = container.find('span', class_='score-hidden')
                    if hidden_elem:
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
        
        except Exception as e:
            logger.error(f"Error fetching comments: {e}")
            return []
        
    def search_posts(self, query: str, limit: int = 25, sort: str = "comments", time_filter: str = "month") -> list[RedditPost]:
        """Search for posts matching a query."""
        url = f"{settings.reddit_base_url}/r/{self.subreddit}/search"
        params = {
            "q": query,
            "restrict_sr": "on",
            "sort": sort,
            "t": time_filter,
        }
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Search results use "search-result" class, not "thing"
            result_elements = soup.find_all("div", class_="search-result", limit=limit)
            
            posts = []
            for element in result_elements:
                post = self._parse_search_result(element)
                if post:
                    posts.append(post)
            
            return posts
            
        except Exception as e:
            logger.error(f"Error searching posts: {e}")
            return []

    def _parse_search_result(self, element) -> RedditPost | None:
        """Parse a single post from search results HTML."""
        try:
            # Get post ID from data-fullname
            post_id = element.get("data-fullname", "")
            
            # Get title
            title_elem = element.find("a", class_="search-title")
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            # Get URL (permalink)
            url = title_elem.get("href", "") if title_elem else ""
            if url and not url.startswith("http"):
                url = f"{settings.reddit_base_url}{url}"
            
            # Get score - "274 points"
            score_elem = element.find("span", class_="search-score")
            score = 0
            if score_elem:
                score_text = score_elem.get_text(strip=True)
                try:
                    score = int(score_text.split()[0])
                except (ValueError, IndexError):
                    score = 0
            
            # Get comment count - "162 comments"
            comments_elem = element.find("a", class_="search-comments")
            num_comments = 0
            if comments_elem:
                comments_text = comments_elem.get_text(strip=True)
                try:
                    num_comments = int(comments_text.split()[0])
                except (ValueError, IndexError):
                    num_comments = 0
            
            # Get timestamp
            time_elem = element.find("time")
            created_at = datetime.now()
            if time_elem and time_elem.get("datetime"):
                from datetime import timezone
                dt_str = time_elem.get("datetime")
                created_at = datetime.fromisoformat(dt_str.replace("+00:00", ""))
            
            # Get subreddit
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
            post.selftext = self.fetch_post_content(post)
            post.comments = self.fetch_post_comments(post)
            time.sleep(delay)
        
        return posts



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