"""Tests for Reddit scraper module"""

import pytest
from datetime import datetime
from unittest.mock import Mock
from bs4 import BeautifulSoup

from kopi_sentiment.scraper.reddit import (
    RedditScraper, RedditPost, Comment,
    JsonRedditFetcher, HtmlRedditFetcher,
    _parse_html_post, _parse_json_post,
)

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

    def test_fetch_posts_empty_page(self, mocker):
        """fetch_posts returns empty list for page with no posts."""
        mock_json = {"data": {"children": []}}
        mock_response = Mock()
        mock_response.json.return_value = mock_json
        mock_response.raise_for_status = Mock()

        json_fetcher = JsonRedditFetcher()
        mocker.patch.object(json_fetcher.session, "get", return_value=mock_response)

        scraper = RedditScraper(fetchers=[json_fetcher])
        posts = scraper.fetch_posts()
        assert posts == []
