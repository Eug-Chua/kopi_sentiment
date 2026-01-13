from kopi_sentiment.analyzer.prompts import (build_extract_prompt,
                                             build_intensity_prompt,
                                             build_weekly_summary_prompt,
                                             build_trending_topics_prompt,
                                             WEEKLY_SUMMARY_SYSTEM_PROMPT,
                                             TRENDING_TOPICS_SYSTEM_PROMPT)

class TestWeeklySummaryPrompts:
    """Tests for weekly summary prompt functions."""

    def test_weekly_summary_system_prompt_exists(self):
        """System prompt is defined and has content."""
        assert len(WEEKLY_SUMMARY_SYSTEM_PROMPT) > 100
        assert "2 sentences" in WEEKLY_SUMMARY_SYSTEM_PROMPT.lower() or "two sentences" in WEEKLY_SUMMARY_SYSTEM_PROMPT.lower()

    def test_build_weekly_summary_prompt(self):
        """Weekly summary prompt builds correctly with all parameters."""
        prompt = build_weekly_summary_prompt(
            week_id="2025-W02",
            post_summaries=["HDB complaints dominated", "Job concerns rising"],
            fear_count=10, fear_mild=2, fear_moderate=5, fear_strong=3,
            frustration_count=25, frustration_mild=5, frustration_moderate=15, frustration_strong=5,
            goal_count=8, goal_mild=3, goal_moderate=4, goal_strong=1,
            aspiration_count=5, aspiration_mild=4, aspiration_moderate=1, aspiration_strong=0,
            sample_fears=["I worry about job security"],
            sample_frustrations=["NEA enforcement is so lax"],
            sample_goals=["Trying to get BTO"],
            sample_aspirations=["Hope for better balance"],
        )
        assert "2025-W02" in prompt
        assert "HDB complaints dominated" in prompt
        assert "fear" in prompt.lower()

    def test_build_weekly_summary_prompt_empty_lists(self):
        """Handles empty quote lists gracefully."""
        prompt = build_weekly_summary_prompt(
            week_id="2025-W02",
            post_summaries=[],
            fear_count=0, fear_mild=0, fear_moderate=0, fear_strong=0,
            frustration_count=0, frustration_mild=0, frustration_moderate=0, frustration_strong=0,
            goal_count=0, goal_mild=0, goal_moderate=0, goal_strong=0,
            aspiration_count=0, aspiration_mild=0, aspiration_moderate=0, aspiration_strong=0,
            sample_fears=[],
            sample_frustrations=[],
            sample_goals=[],
            sample_aspirations=[],
        )
        assert "(none)" in prompt or "(No posts" in prompt


class TestTrendingTopicsPrompts:
    """Tests for trending topics prompt functions."""

    def test_trending_topics_system_prompt_exists(self):
        """System prompt is defined and mentions topics."""
        assert len(TRENDING_TOPICS_SYSTEM_PROMPT) > 100
        assert "topic" in TRENDING_TOPICS_SYSTEM_PROMPT.lower()

    def test_build_trending_topics_prompt(self):
        """Trending topics prompt builds correctly."""
        prompt = build_trending_topics_prompt(
            post_titles=["Smoking in HDB", "Job market concerns", "BTO waiting time"],
            sample_fears=["I worry about job security"],
            sample_frustrations=["NEA enforcement is lax"],
            sample_goals=["Trying to get BTO"],
            sample_aspirations=["Hope for balance"],
        )
        assert "Smoking in HDB" in prompt
        assert "Job market concerns" in prompt
