"""Tests for Reddit scraper module"""

import pytest
from datetime import datetime
from unittest.mock import Mock
from bs4 import BeautifulSoup

from kopi_sentiment.scraper.reddit import (
    RedditScraper, RedditPost, Comment,
    JsonRedditFetcher, HtmlRedditFetcher, EmptyListingError,
    _parse_html_post, _parse_json_post,
)
from kopi_sentiment.scraper.browser import BrowserRedditFetcher, BrowserSessionError

class TestCommentModel:
    """Tests for Comment Pydantic model."""

    def test_create_comment(self):
        """Comment can be created with text and score."""
        comment = Comment(text="This is a comment", score=50)
        assert comment.text == "This is a comment"
        assert comment.score == 50

    def test_comment_with_negative_score(self):
        """Comment can have negative score (downvoted)."""
        comment = Comment(text="Unpopular opinion", score=-10)
        assert comment.score == -10


class TestRedditPostModel:
    """Tests for RedditPost Pydantic model."""

    def test_create_post_with_required_fields(self):
        """Post can be created with required fields only."""
        post = RedditPost(
            id="t3_abc123",
            title="Test title",
            url="https://reddit.com/test",
            score=100,
            num_comments=50,
            created_at=datetime.now(),
        )
        assert post.id == "t3_abc123"
        assert post.selftext == ""  # default
        assert post.comments == []  # default

    def test_create_post_with_comments(self, sample_comments):
        """Post can include comments."""
        post = RedditPost(
            id="t3_abc123",
            title="Test",
            url="https://reddit.com/test",
            score=100,
            num_comments=4,
            created_at=datetime.now(),
            comments=sample_comments,
        )
        assert len(post.comments) == 4

class TestParsePost:
    """Tests for HTML and JSON post parsing."""

    def test_parse_html_post_extracts_all_fields(self):
        """_parse_html_post extracts id, title, score, etc from HTML."""
        html = """
        <div class="thing" data-fullname="t3_abc123" data-score="500"
             data-comments-count="100" data-timestamp="1704067200000"
             data-permalink="/r/singapore/comments/abc123/test_post/"
             data-subreddit="singapore">
            <a class="title">Test Post Title</a>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        element = soup.find("div", class_="thing")

        post = _parse_html_post(element)

        assert post.id == "t3_abc123"
        assert post.title == "Test Post Title"
        assert post.score == 500
        assert post.num_comments == 100
        assert post.subreddit == "singapore"

    def test_parse_html_post_missing_title(self):
        """Post with missing title element returns empty string."""
        html = """
        <div class="thing" data-fullname="t3_abc123" data-score="100"
             data-comments-count="10" data-timestamp="1704067200000"
             data-permalink="/r/singapore/comments/abc123/test/"
             data-subreddit="singapore">
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        element = soup.find("div", class_="thing")

        post = _parse_html_post(element)

        assert post.title == ""

    def test_parse_json_post_extracts_all_fields(self):
        """_parse_json_post extracts fields from JSON data."""
        post_data = {
            "name": "t3_abc123",
            "title": "Test Post Title",
            "score": 500,
            "num_comments": 100,
            "created_utc": 1704067200.0,
            "permalink": "/r/singapore/comments/abc123/test_post/",
            "subreddit": "singapore",
            "selftext": "Hello world",
        }

        post = _parse_json_post(post_data)

        assert post.id == "t3_abc123"
        assert post.title == "Test Post Title"
        assert post.score == 500
        assert post.num_comments == 100
        assert post.subreddit == "singapore"
        assert post.selftext == "Hello world"

class TestFetchPosts:
    """Tests for fetch_posts with mocked HTTP."""

    def test_fetch_posts_json_returns_list(self, mocker):
        """fetch_posts returns list of RedditPost objects via JSON."""
        mock_json = {
            "data": {
                "children": [
                    {
                        "data": {
                            "name": "t3_post1",
                            "title": "First Post",
                            "score": 100,
                            "num_comments": 10,
                            "created_utc": 1704067200.0,
                            "permalink": "/r/singapore/comments/post1/first/",
                            "subreddit": "singapore",
                            "selftext": "",
                        }
                    }
                ]
            }
        }
        mock_response = Mock()
        mock_response.json.return_value = mock_json
        mock_response.raise_for_status = Mock()

        json_fetcher = JsonRedditFetcher()
        mocker.patch.object(json_fetcher.session, "get", return_value=mock_response)

        scraper = RedditScraper(fetchers=[json_fetcher])
        posts = scraper.fetch_posts(limit=10)

        assert len(posts) == 1
        assert posts[0].title == "First Post"

    def test_fetch_posts_fallback_to_html(self, mocker):
        """fetch_posts falls back to HTML when JSON fails."""
        mock_html = """
        <html><body>
            <div class="thing" data-fullname="t3_post1" data-score="100"
                 data-comments-count="10" data-timestamp="1704067200000"
                 data-permalink="/r/singapore/comments/post1/first/"
                 data-subreddit="singapore">
                <a class="title">First Post</a>
            </div>
        </body></html>
        """
        # JSON fetcher fails
        json_fetcher = JsonRedditFetcher()
        mocker.patch.object(json_fetcher.session, "get", side_effect=Exception("403 Blocked"))

        # HTML fetcher succeeds
        html_fetcher = HtmlRedditFetcher()
        mock_response = Mock()
        mock_response.text = mock_html
        mock_response.raise_for_status = Mock()
        mocker.patch.object(html_fetcher.session, "get", return_value=mock_response)

        scraper = RedditScraper(fetchers=[json_fetcher, html_fetcher])
        posts = scraper.fetch_posts(limit=10)

        assert len(posts) == 1
        assert posts[0].title == "First Post"

    def test_fetch_posts_all_empty_raises(self, mocker):
        """An empty listing from every fetcher raises instead of returning [].

        Guards against login walls parsed as "no posts" silently producing
        empty reports downstream.
        """
        mock_json = {"data": {"children": []}}
        mock_response = Mock()
        mock_response.json.return_value = mock_json
        mock_response.raise_for_status = Mock()

        json_fetcher = JsonRedditFetcher()
        mocker.patch.object(json_fetcher.session, "get", return_value=mock_response)

        scraper = RedditScraper(fetchers=[json_fetcher])
        with pytest.raises(EmptyListingError):
            scraper.fetch_posts()

    def test_fetch_posts_empty_listing_falls_back(self, mocker):
        """A fetcher returning zero posts is treated as failed; the next fetcher is tried."""
        empty_fetcher = Mock()
        empty_fetcher.fetch_posts.return_value = []

        good_fetcher = Mock()
        good_fetcher.fetch_posts.return_value = [
            RedditPost(
                id="t3_post1", title="First Post", url="https://old.reddit.com/r/singapore/comments/post1/",
                score=100, num_comments=10, created_at=datetime.now(), subreddit="singapore",
            )
        ]

        scraper = RedditScraper(fetchers=[empty_fetcher, good_fetcher])
        posts = scraper.fetch_posts(limit=10)

        assert len(posts) == 1
        assert posts[0].title == "First Post"


class FakeChromeSession:
    """Test double for ChromeSession: serves canned JSON per URL substring."""

    def __init__(self, responses: dict):
        self.responses = responses
        self.requested_urls = []

    def get_json(self, url: str):
        self.requested_urls.append(url)
        for fragment, payload in self.responses.items():
            if fragment in url:
                if isinstance(payload, Exception):
                    raise payload
                return payload
        raise AssertionError(f"Unexpected URL requested: {url}")


class TestBrowserRedditFetcher:
    """Tests for the browser strategy via an injected fake session (no browser)."""

    LISTING_JSON = {
        "data": {
            "children": [
                {
                    "data": {
                        "name": "t3_post1",
                        "title": "First Post",
                        "score": 100,
                        "num_comments": 10,
                        "created_utc": 1704067200.0,
                        "permalink": "/r/singapore/comments/post1/first/",
                        "subreddit": "singapore",
                        "selftext": "body text",
                    }
                }
            ]
        }
    }

    THREAD_JSON = [
        {"data": {"children": [{"data": {"selftext": "full selftext"}}]}},
        {
            "data": {
                "children": [
                    {"kind": "t1", "data": {"body": "top comment", "score": 42}},
                    {"kind": "t1", "data": {"body": "low comment", "score": 3}},
                    {"kind": "more", "data": {}},
                ]
            }
        },
    ]

    def test_fetch_posts_parses_listing(self):
        session = FakeChromeSession({"/r/singapore/top.json": self.LISTING_JSON})
        fetcher = BrowserRedditFetcher(session=session)

        posts = fetcher.fetch_posts("singapore", limit=10, sort="top", time_filter="day")

        assert len(posts) == 1
        assert posts[0].title == "First Post"
        assert posts[0].selftext == "body text"

    def test_fetch_post_comments_sorted_by_score(self):
        session = FakeChromeSession({"/comments/post1/": self.THREAD_JSON})
        fetcher = BrowserRedditFetcher(session=session)
        post = RedditPost(
            id="t3_post1", title="First Post",
            url="https://old.reddit.com/r/singapore/comments/post1/first/",
            score=100, num_comments=2, created_at=datetime.now(), subreddit="singapore",
        )

        comments = fetcher.fetch_post_comments(post, limit=25)

        assert [c.text for c in comments] == ["top comment", "low comment"]
        assert comments[0].score == 42

    def test_session_error_falls_back_to_next_fetcher(self, mocker):
        """A login-walled browser session fails over to the next strategy."""
        session = FakeChromeSession(
            {"/r/singapore/top.json": BrowserSessionError("login wall")}
        )
        browser_fetcher = BrowserRedditFetcher(session=session)

        good_fetcher = Mock()
        good_fetcher.fetch_posts.return_value = [
            RedditPost(
                id="t3_post1", title="Fallback Post", url="https://old.reddit.com/r/singapore/comments/post1/",
                score=1, num_comments=0, created_at=datetime.now(), subreddit="singapore",
            )
        ]

        scraper = RedditScraper(fetchers=[browser_fetcher, good_fetcher])
        posts = scraper.fetch_posts(limit=10, sort="top", time_filter="day")

        assert posts[0].title == "Fallback Post"
