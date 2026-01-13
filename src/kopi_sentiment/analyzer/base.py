"""Base interface for LLM analyzers"""

import json
import logging
from abc import ABC, abstractmethod
from kopi_sentiment.analyzer.models import (
    Intensity,
    FFGACategory,
    FFGAResult,
    AnalysisResult,
    CategorySummary,
    OverallSentiment,
    IntensityBreakdown,
    TrendingTopic,
)
from kopi_sentiment.analyzer.prompts import (
    EXTRACT_SYSTEM_PROMPT,
    INTENSITY_SYSTEM_PROMPT,
    WEEKLY_SUMMARY_SYSTEM_PROMPT,
    TRENDING_TOPICS_SYSTEM_PROMPT,
    build_extract_prompt,
    build_intensity_prompt,
    build_weekly_summary_prompt,
    build_trending_topics_prompt,
)

from kopi_sentiment.scraper.reddit import RedditPost

logger = logging.getLogger(__name__)

class BaseAnalyzer:
    """Abstract base class for sentiment analyzers"""

    @abstractmethod
    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Make a call to the LLM provider
        
        Each provider (Claude, OpenAI) implements this differently.
        """
        pass

    def _extract_quotes(self, post: RedditPost) -> dict[str, list[str]]:
        """Step 1: Extract and categorize quotes from post."""
        user_prompt = build_extract_prompt(
            title=post.title,
            selftext=post.selftext,
            comments=post.comments,
            subreddit=post.subreddit,
        )

        response = self._call_llm(EXTRACT_SYSTEM_PROMPT, user_prompt)
        response = self._clean_json_response(response)

        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse extraction response: {e}")
            return {"fears": [], "frustrations": [], "goals": [], "aspirations": []}


    def _assess_intensity(self, title: str, quotes: dict[str, list[str]]) -> dict:
        """Step 2: Assess intensity for categorized quotes."""
        user_prompt = build_intensity_prompt(
            title=title,
            fears=quotes.get("fears", []),
            frustrations=quotes.get("frustrations", []),
            goals=quotes.get("goals", []),
            aspirations=quotes.get("aspirations", []),
        )

        response = self._call_llm(INTENSITY_SYSTEM_PROMPT, user_prompt)
        response = self._clean_json_response(response)

        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse intensity response: {e}")
            return {}

        
    def _clean_json_response(self, response: str) -> str:
        """Remove markdown code blocks from LLM response."""
        response = response.strip()
        
        # Remove ```json or ``` at start
        if response.startswith("```json"):
            response = response.removeprefix("```json")
        elif response.startswith("```"):
            response = response.removeprefix("```")
        
        # Remove ``` at end
        if response.endswith("```"):
            response = response.removesuffix("```")
        
        return response.strip()

    def _build_ffga_result(self,
                           category: FFGACategory,
                           key: str,
                           quotes: dict,
                           intensity_data: dict) -> FFGAResult:
        """Build a single FFGA result"""

        data = intensity_data.get(key, {})
        return FFGAResult(category=category,
                          intensity=data.get('intensity', 'moderate'),
                          summary=data.get('summary', 'No analysis available.'),
                          quotes=quotes.get(key, [])
        )

    def _build_analysis_result(self,
                               post: RedditPost,
                               quotes: dict,
                               intensity_data: dict) -> AnalysisResult:
        """Build the complete analysis result"""
        fears = self._build_ffga_result(FFGACategory.FEAR, "fears", quotes, intensity_data)
        frustrations = self._build_ffga_result(FFGACategory.FRUSTRATION, "frustrations", quotes, intensity_data)
        goals = self._build_ffga_result(FFGACategory.GOAL, "goals", quotes, intensity_data)
        aspirations = self._build_ffga_result(FFGACategory.ASPIRATION, "aspirations", quotes, intensity_data)

        return AnalysisResult(post_id=post.id,
                              post_title=post.title,
                              fears=fears,
                              frustrations=frustrations,
                              goals=goals,
                              aspirations=aspirations)

    def analyze(self, post: RedditPost) -> AnalysisResult:
        """Analyze a Reddit post and return FFGA analysis"""
        quotes = self._extract_quotes(post)
        intensity_data = self._assess_intensity(post.title, quotes)
        return self._build_analysis_result(post, quotes, intensity_data)

    def analyze_batch(self, posts: list[RedditPost]) -> list[AnalysisResult]:
        """Analyze multiple Reddit posts"""
        results = []
        for post in posts:
            try:
                result = self.analyze(post)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to analyze post {post.id}: {e}")

        return results

    def generate_weekly_summary(
        self,
        week_id: str,
        analyses: list[AnalysisResult],
        all_quotes: dict[str, list[str]],
    ) -> OverallSentiment:
        """Step 3: Generate 2-sentence weekly summaries for each FFGA category.

        Args:
            week_id: ISO week format (e.g., "2025-W02")
            analyses: List of post analysis results
            all_quotes: Dict with lists of quotes per category

        Returns:
            OverallSentiment with 2-sentence summaries per category
        """
        # Count quotes and intensity breakdown per category
        intensity_counts = {
            "fears": {"mild": 0, "moderate": 0, "strong": 0},
            "frustrations": {"mild": 0, "moderate": 0, "strong": 0},
            "goals": {"mild": 0, "moderate": 0, "strong": 0},
            "aspirations": {"mild": 0, "moderate": 0, "strong": 0},
        }

        for analysis in analyses:
            for key, result in [
                ("fears", analysis.fears),
                ("frustrations", analysis.frustrations),
                ("goals", analysis.goals),
                ("aspirations", analysis.aspirations),
            ]:
                intensity = result.intensity.value if hasattr(result.intensity, 'value') else result.intensity
                if intensity in intensity_counts[key]:
                    intensity_counts[key][intensity] += len(result.quotes)

        # Build post summaries for context
        post_summaries = []
        for analysis in analyses:
            summary = f"{analysis.post_title}: "
            parts = []
            if analysis.fears.quotes:
                parts.append(f"{len(analysis.fears.quotes)} fear quotes ({analysis.fears.intensity})")
            if analysis.frustrations.quotes:
                parts.append(f"{len(analysis.frustrations.quotes)} frustration quotes ({analysis.frustrations.intensity})")
            if analysis.goals.quotes:
                parts.append(f"{len(analysis.goals.quotes)} goal quotes ({analysis.goals.intensity})")
            if analysis.aspirations.quotes:
                parts.append(f"{len(analysis.aspirations.quotes)} aspiration quotes ({analysis.aspirations.intensity})")
            summary += ", ".join(parts) if parts else "no significant quotes"
            post_summaries.append(summary)

        # Build the prompt
        user_prompt = build_weekly_summary_prompt(
            week_id=week_id,
            post_summaries=post_summaries,
            fear_count=len(all_quotes.get("fears", [])),
            fear_mild=intensity_counts["fears"]["mild"],
            fear_moderate=intensity_counts["fears"]["moderate"],
            fear_strong=intensity_counts["fears"]["strong"],
            frustration_count=len(all_quotes.get("frustrations", [])),
            frustration_mild=intensity_counts["frustrations"]["mild"],
            frustration_moderate=intensity_counts["frustrations"]["moderate"],
            frustration_strong=intensity_counts["frustrations"]["strong"],
            goal_count=len(all_quotes.get("goals", [])),
            goal_mild=intensity_counts["goals"]["mild"],
            goal_moderate=intensity_counts["goals"]["moderate"],
            goal_strong=intensity_counts["goals"]["strong"],
            aspiration_count=len(all_quotes.get("aspirations", [])),
            aspiration_mild=intensity_counts["aspirations"]["mild"],
            aspiration_moderate=intensity_counts["aspirations"]["moderate"],
            aspiration_strong=intensity_counts["aspirations"]["strong"],
            sample_fears=all_quotes.get("fears", [])[:5],
            sample_frustrations=all_quotes.get("frustrations", [])[:5],
            sample_goals=all_quotes.get("goals", [])[:5],
            sample_aspirations=all_quotes.get("aspirations", [])[:5],
        )

        response = self._call_llm(WEEKLY_SUMMARY_SYSTEM_PROMPT, user_prompt)
        response = self._clean_json_response(response)

        try:
            data = json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse weekly summary response: {e}")
            data = {}

        # Build CategorySummary for each category
        def build_category_summary(key: str) -> CategorySummary:
            cat_data = data.get(key, {})
            counts = intensity_counts[key]
            return CategorySummary(
                intensity=Intensity(cat_data.get("intensity", "moderate")),
                summary=cat_data.get("summary", "No summary available."),
                quote_count=len(all_quotes.get(key, [])),
                intensity_breakdown=IntensityBreakdown(
                    mild=counts["mild"],
                    moderate=counts["moderate"],
                    strong=counts["strong"],
                ),
            )

        return OverallSentiment(
            fears=build_category_summary("fears"),
            frustrations=build_category_summary("frustrations"),
            goals=build_category_summary("goals"),
            aspirations=build_category_summary("aspirations"),
        )

    def detect_trending_topics(
        self,
        post_titles: list[str],
        all_quotes: dict[str, list[str]],
    ) -> list[TrendingTopic]:
        """Step 4: Detect trending topics across all analyzed posts.

        Args:
            post_titles: List of post titles analyzed
            all_quotes: Dict with lists of quotes per category

        Returns:
            List of TrendingTopic objects
        """
        user_prompt = build_trending_topics_prompt(
            post_titles=post_titles,
            sample_fears=all_quotes.get("fears", [])[:10],
            sample_frustrations=all_quotes.get("frustrations", [])[:10],
            sample_goals=all_quotes.get("goals", [])[:10],
            sample_aspirations=all_quotes.get("aspirations", [])[:10],
        )

        response = self._call_llm(TRENDING_TOPICS_SYSTEM_PROMPT, user_prompt)
        response = self._clean_json_response(response)

        try:
            data = json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse trending topics response: {e}")
            return []

        topics = []
        for topic_data in data.get("trending_topics", []):
            try:
                topics.append(TrendingTopic(
                    topic=topic_data["topic"],
                    mentions=topic_data["mentions"],
                    dominant_emotion=FFGACategory(topic_data["dominant_emotion"]),
                    sentiment_shift=topic_data["sentiment_shift"],
                ))
            except (KeyError, ValueError) as e:
                logger.warning(f"Skipping invalid trending topic: {e}")

        return topics

