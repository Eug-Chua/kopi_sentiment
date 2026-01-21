"""Base interface for LLM analyzers"""

import json
import logging
from abc import ABC, abstractmethod
from kopi_sentiment.analyzer.models import (
    Intensity,
    FFGACategory,
    FFGAResult,
    ExtractedQuote,
    AnalysisResult,
    CategorySummary,
    OverallSentiment,
    IntensityBreakdown,
    ThematicCluster,
    WeeklyInsights,
    ThemeCluster,
    Signal,
    SignalType,
)
from kopi_sentiment.analyzer.prompts import (
    EXTRACT_SYSTEM_PROMPT,
    INTENSITY_SYSTEM_PROMPT,
    WEEKLY_SUMMARY_SYSTEM_PROMPT,
    THEMATIC_CLUSTERS_SYSTEM_PROMPT,
    WEEKLY_INSIGHTS_SYSTEM_PROMPT,
    THEME_CLUSTERING_SYSTEM_PROMPT,
    SIGNAL_DETECTION_SYSTEM_PROMPT,
    build_extract_prompt,
    build_intensity_prompt,
    build_weekly_summary_prompt,
    build_thematic_clusters_prompt,
    build_weekly_insights_prompt,
    build_theme_clustering_prompt,
    build_signal_detection_prompt,
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

    def _extract_quotes(self, post: RedditPost) -> dict[str, list[ExtractedQuote]]:
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
            raw_data = json.loads(response)
            # Convert to ExtractedQuote objects, handling both old (string) and new (dict) formats
            result = {}
            for key in ["fears", "frustrations", "goals", "aspirations"]:
                quotes = []
                for item in raw_data.get(key, []):
                    if isinstance(item, str):
                        # Old format: just a string
                        quotes.append(ExtractedQuote(quote=item, score=0))
                    elif isinstance(item, dict):
                        # New format: {"quote": "...", "score": N}
                        quotes.append(ExtractedQuote(
                            quote=item.get("quote", ""),
                            score=item.get("score", 0)
                        ))
                result[key] = quotes
            return result
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse extraction response: {e}")
            return {"fears": [], "frustrations": [], "goals": [], "aspirations": []}


    def _assess_intensity(self, title: str, quotes: dict[str, list[ExtractedQuote]]) -> dict:
        """Step 2: Assess intensity for categorized quotes."""
        # Extract just the quote text for intensity assessment
        user_prompt = build_intensity_prompt(
            title=title,
            fears=[q.quote for q in quotes.get("fears", [])],
            frustrations=[q.quote for q in quotes.get("frustrations", [])],
            goals=[q.quote for q in quotes.get("goals", [])],
            aspirations=[q.quote for q in quotes.get("aspirations", [])],
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
                           quotes: dict[str, list[ExtractedQuote]],
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
                               quotes: dict[str, list[ExtractedQuote]],
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
        is_daily: bool = False,
    ) -> OverallSentiment:
        """Step 3: Generate 2-sentence summaries for each FFGA category.

        Args:
            week_id: ISO week format (e.g., "2025-W02") or date (e.g., "2025-01-15")
            analyses: List of post analysis results
            all_quotes: Dict with lists of quotes per category
            is_daily: If True, use daily framing instead of weekly

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
            is_daily=is_daily,
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

    def detect_thematic_clusters(
        self,
        post_titles: list[str],
        all_quotes: dict[str, list[str]],
    ) -> list[ThematicCluster]:
        """Step 4: Detect thematic clusters (what people are discussing).

        Identifies the main topics being discussed, weighted by engagement.

        Args:
            post_titles: List of post titles with scores (e.g., "[+500] Title")
            all_quotes: Dict with lists of quotes per category

        Returns:
            List of ThematicCluster objects
        """
        user_prompt = build_thematic_clusters_prompt(
            post_titles=post_titles,
            sample_fears=all_quotes.get("fears", [])[:10],
            sample_frustrations=all_quotes.get("frustrations", [])[:10],
            sample_goals=all_quotes.get("goals", [])[:10],
            sample_aspirations=all_quotes.get("aspirations", [])[:10],
        )

        response = self._call_llm(THEMATIC_CLUSTERS_SYSTEM_PROMPT, user_prompt)
        response = self._clean_json_response(response)

        try:
            data = json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse thematic clusters response: {e}")
            return []

        clusters = []
        for cluster_data in data.get("thematic_clusters", []):
            try:
                clusters.append(ThematicCluster(
                    topic=cluster_data["topic"],
                    engagement_score=cluster_data.get("engagement_score", 0),
                    dominant_emotion=FFGACategory(cluster_data["dominant_emotion"]),
                    sample_posts=cluster_data.get("sample_posts", [])[:3],
                ))
            except (KeyError, ValueError) as e:
                logger.warning(f"Skipping invalid thematic cluster: {e}")

        return clusters

    def generate_weekly_insights(
        self,
        week_id: str,
        overall_sentiment: OverallSentiment,
        trend_summary: str,
        high_engagement_quotes: list[str],
        trending_topics: list[str],
    ) -> WeeklyInsights:
        """Step 5: Generate strategic insights and recommendations.

        Args:
            week_id: ISO week format (e.g., "2025-W02")
            overall_sentiment: The OverallSentiment from weekly summary
            trend_summary: Text summary of week-over-week trends
            high_engagement_quotes: Quotes with high upvotes
            trending_topics: List of trending topic names

        Returns:
            WeeklyInsights with headline, takeaways, opportunities, risks
        """
        user_prompt = build_weekly_insights_prompt(
            week_id=week_id,
            fears_summary=overall_sentiment.fears.summary,
            fears_intensity=overall_sentiment.fears.intensity.value,
            fears_count=overall_sentiment.fears.quote_count,
            frustrations_summary=overall_sentiment.frustrations.summary,
            frustrations_intensity=overall_sentiment.frustrations.intensity.value,
            frustrations_count=overall_sentiment.frustrations.quote_count,
            goals_summary=overall_sentiment.goals.summary,
            goals_intensity=overall_sentiment.goals.intensity.value,
            goals_count=overall_sentiment.goals.quote_count,
            aspirations_summary=overall_sentiment.aspirations.summary,
            aspirations_intensity=overall_sentiment.aspirations.intensity.value,
            aspirations_count=overall_sentiment.aspirations.quote_count,
            trend_summary=trend_summary,
            high_engagement_quotes=high_engagement_quotes,
            trending_topics=trending_topics,
        )

        response = self._call_llm(WEEKLY_INSIGHTS_SYSTEM_PROMPT, user_prompt)
        response = self._clean_json_response(response)

        try:
            data = json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse weekly insights response: {e}")
            data = {}

        return WeeklyInsights(
            headline=data.get("headline", "No headline available."),
            key_takeaways=data.get("key_takeaways", []),
            opportunities=data.get("opportunities", []),
            risks=data.get("risks", []),
        )

    def cluster_themes(
        self,
        all_quotes: dict[str, list[str]],
    ) -> list[ThemeCluster]:
        """Step 6: Cluster quotes into meaningful themes.

        Args:
            all_quotes: Dict with lists of quotes per category

        Returns:
            List of ThemeCluster objects
        """
        user_prompt = build_theme_clustering_prompt(
            fears_quotes=all_quotes.get("fears", []),
            frustrations_quotes=all_quotes.get("frustrations", []),
            goals_quotes=all_quotes.get("goals", []),
            aspirations_quotes=all_quotes.get("aspirations", []),
        )

        response = self._call_llm(THEME_CLUSTERING_SYSTEM_PROMPT, user_prompt)
        response = self._clean_json_response(response)

        try:
            data = json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse theme clustering response: {e}")
            return []

        clusters = []
        for cluster_data in data.get("clusters", []):
            try:
                clusters.append(ThemeCluster(
                    theme=cluster_data["theme"],
                    description=cluster_data["description"],
                    category=FFGACategory(cluster_data["category"]),
                    quote_count=cluster_data["quote_count"],
                    sample_quotes=cluster_data.get("sample_quotes", [])[:3],
                    avg_score=cluster_data.get("avg_score", 0.0),
                ))
            except (KeyError, ValueError) as e:
                logger.warning(f"Skipping invalid theme cluster: {e}")

        return clusters

    def detect_signals(
        self,
        intensity_counts: dict[str, dict[str, int]],
        previous_week_comparison: str,
        high_engagement_quotes: list[str],
        trending_topics: list[str],
    ) -> list[Signal]:
        """Step 7: Detect notable signals that warrant attention.

        Args:
            intensity_counts: Dict of intensity breakdowns per category
            previous_week_comparison: Text comparison with previous week
            high_engagement_quotes: Quotes with high upvotes
            trending_topics: List of trending topic names

        Returns:
            List of Signal objects
        """
        user_prompt = build_signal_detection_prompt(
            fears_count=sum(intensity_counts.get("fears", {}).values()),
            fears_mild=intensity_counts.get("fears", {}).get("mild", 0),
            fears_moderate=intensity_counts.get("fears", {}).get("moderate", 0),
            fears_strong=intensity_counts.get("fears", {}).get("strong", 0),
            frustrations_count=sum(intensity_counts.get("frustrations", {}).values()),
            frustrations_mild=intensity_counts.get("frustrations", {}).get("mild", 0),
            frustrations_moderate=intensity_counts.get("frustrations", {}).get("moderate", 0),
            frustrations_strong=intensity_counts.get("frustrations", {}).get("strong", 0),
            goals_count=sum(intensity_counts.get("goals", {}).values()),
            goals_mild=intensity_counts.get("goals", {}).get("mild", 0),
            goals_moderate=intensity_counts.get("goals", {}).get("moderate", 0),
            goals_strong=intensity_counts.get("goals", {}).get("strong", 0),
            aspirations_count=sum(intensity_counts.get("aspirations", {}).values()),
            aspirations_mild=intensity_counts.get("aspirations", {}).get("mild", 0),
            aspirations_moderate=intensity_counts.get("aspirations", {}).get("moderate", 0),
            aspirations_strong=intensity_counts.get("aspirations", {}).get("strong", 0),
            previous_week_comparison=previous_week_comparison,
            high_engagement_quotes=high_engagement_quotes,
            trending_topics=trending_topics,
        )

        response = self._call_llm(SIGNAL_DETECTION_SYSTEM_PROMPT, user_prompt)
        response = self._clean_json_response(response)

        try:
            data = json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse signal detection response: {e}")
            return []

        signals = []
        for signal_data in data.get("signals", []):
            try:
                category = signal_data.get("category")
                signals.append(Signal(
                    signal_type=SignalType(signal_data["signal_type"]),
                    title=signal_data["title"],
                    description=signal_data["description"],
                    category=FFGACategory(category) if category else None,
                    related_quotes=signal_data.get("related_quotes", [])[:3],
                    urgency=signal_data.get("urgency", "medium"),
                ))
            except (KeyError, ValueError) as e:
                logger.warning(f"Skipping invalid signal: {e}")

        return signals

def create_analyzer(provider: str | None = None) -> BaseAnalyzer:
    """Factory function to create analyzer by provider name."""
    from kopi_sentiment.analyzer.claude import ClaudeAnalyzer
    from kopi_sentiment.analyzer.openai import OpenAIAnalyzer
    from kopi_sentiment.analyzer.hybrid import HybridAnalyzer
    from kopi_sentiment.config.settings import settings
    
    provider = provider or settings.llm_provider
    
    analyzers = {
        "claude": ClaudeAnalyzer,
        "openai": OpenAIAnalyzer,
        "hybrid": HybridAnalyzer,
    }
    
    if provider not in analyzers:
        raise ValueError(f"Unknown provider: {provider}")
    
    return analyzers[provider]()
