"""Tests for the analyzer module."""

import pytest
import json
from kopi_sentiment.analyzer.models import Sentiment, FFGACategory, FFGAResult, AnalysisResult
from kopi_sentiment.analyzer.prompts import build_extract_prompt, build_sentiment_prompt
from kopi_sentiment.analyzer.base import BaseAnalyzer

class TestSentimentEnum:
    """Tests for Sentiment enum."""

    def test_sentiment_values(self):
        """All 5 sentiment levels exist."""
        assert Sentiment.STRONG_POSITIVE.value == "strong_positive"
        assert Sentiment.POSITIVE.value == "positive"
        assert Sentiment.MIXED.value == "mixed"
        assert Sentiment.NEGATIVE.value == "negative"
        assert Sentiment.STRONG_NEGATIVE.value == "strong_negative"

    def test_sentiment_from_string(self):
        """Sentiment can be created from string value."""
        sentiment = Sentiment("negative")
        assert sentiment == Sentiment.NEGATIVE


class TestFFGAResult:
    """Tests for FFGAResult model."""

    def test_create_ffga_result(self):
        """FFGAResult can be created with all fields."""
        result = FFGAResult(
            category=FFGACategory.FEAR,
            sentiment=Sentiment.NEGATIVE,
            summary="People are worried about housing.",
            quotes=["I can't afford a flat"],
        )
        assert result.category == FFGACategory.FEAR
        assert result.sentiment == Sentiment.NEGATIVE
        assert len(result.quotes) == 1

class TestBuildExtractPrompt:
    """Tests for build_extract_prompt function."""

    def test_formats_comments_with_scores(self, sample_comments):
        """Comments are formatted with [+score] prefix."""
        prompt = build_extract_prompt(
            title="Test Title",
            selftext="Test content",
            comments=sample_comments,
            subreddit="singapore",
        )
        assert "[+200]" in prompt
        assert "[+150]" in prompt
        assert "I'm worried about affording a flat" in prompt

    def test_handles_empty_selftext(self, sample_comments):
        """Empty selftext shows placeholder text."""
        prompt = build_extract_prompt(
            title="Test Title",
            selftext="",
            comments=sample_comments,
            subreddit="singapore",
        )
        assert "(No post content - this is a link post)" in prompt

    def test_handles_no_comments(self):
        """No comments shows placeholder text."""
        prompt = build_extract_prompt(
            title="Test Title",
            selftext="Some content",
            comments=[],
            subreddit="singapore",
        )
        assert "(No comments)" in prompt

class TestCleanJsonResponse:
    """Tests for _clean_json_response method."""

    def test_removes_json_code_block(self):
        """Strips ```json ... ``` wrapper."""
        # Create a concrete implementation for testing
        class TestAnalyzer(BaseAnalyzer):
            def _call_llm(self, system_prompt, user_prompt):
                return ""

        analyzer = TestAnalyzer()
        
        raw = '```json\n{"fears": []}\n```'
        cleaned = analyzer._clean_json_response(raw)
        assert cleaned == '{"fears": []}'

    def test_removes_plain_code_block(self):
        """Strips ``` ... ``` wrapper (no json tag)."""
        class TestAnalyzer(BaseAnalyzer):
            def _call_llm(self, system_prompt, user_prompt):
                return ""

        analyzer = TestAnalyzer()
        
        raw = '```\n{"fears": []}\n```'
        cleaned = analyzer._clean_json_response(raw)
        assert cleaned == '{"fears": []}'

    def test_leaves_clean_json_unchanged(self):
        """Clean JSON passes through unchanged."""
        class TestAnalyzer(BaseAnalyzer):
            def _call_llm(self, system_prompt, user_prompt):
                return ""

        analyzer = TestAnalyzer()
        
        raw = '{"fears": [], "frustrations": []}'
        cleaned = analyzer._clean_json_response(raw)
        assert cleaned == raw
