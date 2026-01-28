"""LLM-powered sentiment commentary generator.

Generates plain-language commentary about sentiment scores
using Claude for synthesis.
"""

import logging
from typing import Any

from .config import AnalyticsConfig
from .models import SentimentTimeSeries

logger = logging.getLogger(__name__)


class CommentaryGenerator:
    """Generates LLM-powered sentiment commentary."""

    def __init__(self, config: AnalyticsConfig):
        self.config = config

    def generate(
        self,
        timeseries: SentimentTimeSeries,
        daily_data: list[dict[str, Any]],
    ) -> str:
        """Generate plain-language commentary about sentiment scores.

        Args:
            timeseries: The sentiment time series with data points.
            daily_data: Raw daily report data for intensity breakdown.

        Returns:
            Plain-language commentary string, or empty string if unavailable.
        """
        if len(timeseries.data_points) < 2:
            return ""

        try:
            from anthropic import Anthropic
            from kopi_sentiment.config.settings import settings
            from kopi_sentiment.analyzer.prompts import (
                SENTIMENT_COMMENTARY_SYSTEM_PROMPT,
                build_sentiment_commentary_prompt,
            )

            prompt_data = self._build_prompt_data(timeseries, daily_data)
            user_prompt = build_sentiment_commentary_prompt(**prompt_data)

            client = Anthropic(api_key=settings.anthropic_api_key)
            response = client.messages.create(
                model=self.config.commentary.model,
                max_tokens=self.config.commentary.max_tokens,
                system=SENTIMENT_COMMENTARY_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )
            commentary = response.content[0].text.strip()

            if commentary.startswith('"') and commentary.endswith('"'):
                commentary = commentary[1:-1]

            logger.info(f"Generated sentiment commentary: {commentary[:100]}...")
            return commentary

        except Exception as e:
            logger.warning(f"Could not generate sentiment commentary: {e}")
            return ""

    def _build_prompt_data(
        self,
        timeseries: SentimentTimeSeries,
        daily_data: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Build data dictionary for commentary prompt."""
        today = timeseries.data_points[-1]
        yesterday = timeseries.data_points[-2]
        latest_report = daily_data[-1]

        fears_intensity = self._get_intensity(latest_report, "fears")
        frustrations_intensity = self._get_intensity(latest_report, "frustrations")
        optimism_intensity = self._get_intensity(latest_report, "optimism")

        all_fears = [dp.fears_zscore_sum for dp in timeseries.data_points]
        all_frustrations = [dp.frustrations_zscore_sum for dp in timeseries.data_points]
        all_optimism = [dp.optimism_zscore_sum for dp in timeseries.data_points]

        scores = {
            "Fears": today.fears_zscore_sum,
            "Frustrations": today.frustrations_zscore_sum,
            "Optimism": today.optimism_zscore_sum,
        }
        dominant_category = max(scores, key=lambda k: abs(scores[k]))

        return {
            "fears_score": today.fears_zscore_sum,
            "fears_yesterday": yesterday.fears_zscore_sum,
            "fears_count": today.fears_count,
            "fears_min": min(all_fears),
            "fears_max": max(all_fears),
            "fears_strong": fears_intensity.get("strong", 0),
            "fears_moderate": fears_intensity.get("moderate", 0),
            "fears_mild": fears_intensity.get("mild", 0),
            "frustrations_score": today.frustrations_zscore_sum,
            "frustrations_yesterday": yesterday.frustrations_zscore_sum,
            "frustrations_count": today.frustrations_count,
            "frustrations_min": min(all_frustrations),
            "frustrations_max": max(all_frustrations),
            "frustrations_strong": frustrations_intensity.get("strong", 0),
            "frustrations_moderate": frustrations_intensity.get("moderate", 0),
            "frustrations_mild": frustrations_intensity.get("mild", 0),
            "optimism_score": today.optimism_zscore_sum,
            "optimism_yesterday": yesterday.optimism_zscore_sum,
            "optimism_count": today.optimism_count,
            "optimism_min": min(all_optimism),
            "optimism_max": max(all_optimism),
            "optimism_strong": optimism_intensity.get("strong", 0),
            "optimism_moderate": optimism_intensity.get("moderate", 0),
            "optimism_mild": optimism_intensity.get("mild", 0),
            "dominant_category": dominant_category,
            "trend_direction": timeseries.overall_trend.value,
            "days_analyzed": len(timeseries.data_points),
        }

    def _get_intensity(
        self, report: dict[str, Any], category: str
    ) -> dict[str, int]:
        """Extract intensity breakdown from report."""
        overall = report.get("overall_sentiment", {})
        cat_data = overall.get(category, {})
        return cat_data.get(
            "intensity_breakdown", {"mild": 0, "moderate": 0, "strong": 0}
        )
