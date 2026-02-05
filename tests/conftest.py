"""Shared pytest fixtures for kopi_sentiment tests."""

import pytest
from datetime import datetime
from kopi_sentiment.scraper.reddit import RedditPost, Comment
from kopi_sentiment.analyzer.models import Intensity, FFOCategory, FFOResult, AnalysisResult, ExtractedQuote


@pytest.fixture
def sample_comment():
    """A single sample comment."""
    return Comment(text="HDB prices are crazy nowadays", score=150)


@pytest.fixture
def sample_comments():
    """A list of sample comments."""
    return [
        Comment(text="I'm worried about affording a flat", score=200),
        Comment(text="The government needs to do something", score=150),
        Comment(text="BTO is the only way for young couples", score=100),
        Comment(text="Hope prices stabilize soon", score=75),
    ]


@pytest.fixture
def sample_post(sample_comments):
    """A sample Reddit post with comments."""
    return RedditPost(
        id="t3_abc123",
        title="HDB prices hit new record high",
        url="https://old.reddit.com/r/singapore/comments/abc123/hdb_prices_hit_new_record_high",
        score=500,
        num_comments=150,
        created_at=datetime(2024, 1, 15, 10, 30, 0),
        subreddit="singapore",
        selftext="Just saw the news that HDB resale prices have hit a new record.",
        comments=sample_comments,
    )


@pytest.fixture
def sample_post_no_comments():
    """A sample Reddit post without comments."""
    return RedditPost(
        id="t3_xyz789",
        title="New MRT line opening soon",
        url="https://old.reddit.com/r/singapore/comments/xyz789/new_mrt_line",
        score=100,
        num_comments=0,
        created_at=datetime(2024, 1, 20, 14, 0, 0),
        subreddit="singapore",
        selftext="",
        comments=[],
    )


@pytest.fixture
def sample_extraction_response():
    """Sample LLM response for quote extraction."""
    return {
        "fears": ["I'm worried about affording a flat"],
        "frustrations": ["The government needs to do something"],
        "optimism": ["Hope prices stabilize soon"],
    }


@pytest.fixture
def sample_intensity_response():
    """Sample LLM response for intensity assessment."""
    return {
        "fears": {
            "intensity": "strong",
            "summary": "Anxiety about housing affordability."
        },
        "frustrations": {
            "intensity": "strong",
            "summary": "Frustration with government inaction."
        },
        "optimism": {
            "intensity": "mild",
            "summary": "Hope for policy interventions to stabilize prices."
        },
    }


@pytest.fixture
def sample_ffo_result():
    """A sample FFOResult."""
    return FFOResult(
        category=FFOCategory.FEAR,
        intensity=Intensity.STRONG,
        summary="Anxiety about housing affordability.",
        quotes=[ExtractedQuote(quote="I'm worried about affording a flat", score=200)],
    )


@pytest.fixture
def sample_analysis_result(sample_post):
    """A complete sample AnalysisResult."""
    return AnalysisResult(
        post_id=sample_post.id,
        post_title=sample_post.title,
        fears=FFOResult(
            category=FFOCategory.FEAR,
            intensity=Intensity.STRONG,
            summary="Anxiety about housing affordability.",
            quotes=[ExtractedQuote(quote="I'm worried about affording a flat", score=200)],
        ),
        frustrations=FFOResult(
            category=FFOCategory.FRUSTRATION,
            intensity=Intensity.STRONG,
            summary="Frustration with government inaction.",
            quotes=[ExtractedQuote(quote="The government needs to do something", score=150)],
        ),
        optimism=FFOResult(
            category=FFOCategory.OPTIMISM,
            intensity=Intensity.MILD,
            summary="Hope for price stabilization.",
            quotes=[ExtractedQuote(quote="Hope prices stabilize soon", score=75)],
        ),
    )