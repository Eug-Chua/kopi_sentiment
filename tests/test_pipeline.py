from datetime import date, datetime
from kopi_sentiment.pipeline.weekly import WeeklyPipeline
from kopi_sentiment.analyzer.models import SubredditReport, PostAnalysis

def test_get_week_returns_iso_format():
    """Test that get_week returns ISO week format."""
    pipeline = WeeklyPipeline(
        subreddits=["singapore"],
        posts_per_subreddit=1,
        llm_provider="openai",
        storage_path="data/test"
    )

    # Test specific date
    result = pipeline.get_week(date(2026, 1, 14))
    assert result == "2026-W03"

    # Test another date
    result = pipeline.get_week(date(2025, 1, 1))
    assert result == "2025-W01"

def test_get_week_bounds_returns_monday_to_sunday():
    """Test that get_week_bounds returns correct Monday-Sunday range."""
    pipeline = WeeklyPipeline(
        subreddits=["singapore"],
        posts_per_subreddit=1,
        llm_provider="openai",
        storage_path="data/test"
    )

    week_start, week_end = pipeline.get_week_bounds("2026-W03")

    assert week_start == date(2026, 1, 12)  # Monday
    assert week_end == date(2026, 1, 18)    # Sunday
    assert week_start.weekday() == 0        # Monday = 0
    assert week_end.weekday() == 6          # Sunday = 6

def test_aggregate_quotes_collects_all_quotes(sample_analysis_result):
    """Test that aggregate_quotes collects quotes from all posts."""
    pipeline = WeeklyPipeline(
        subreddits=["singapore"],
        posts_per_subreddit=1,
        llm_provider="openai",
        storage_path="data/test"
    )

    # Create a mock SubredditReport
    post_analysis = PostAnalysis(
        id="t3_abc123",
        title="Test Post",
        url="https://reddit.com/test",
        score=100,
        num_comments=10,
        created_at=datetime.now(),
        subreddit="singapore",
        analysis=sample_analysis_result
    )

    report = SubredditReport(
        name="singapore",
        posts_analyzed=1,
        comments_analyzed=10,
        top_posts=[post_analysis]
    )

    all_quotes = pipeline.aggregate_quotes([report])

    assert len(all_quotes.fears) == 1
    assert len(all_quotes.frustrations) == 1
    assert len(all_quotes.optimism) == 1
    assert all_quotes.fears[0].text == "I'm worried about affording a flat"