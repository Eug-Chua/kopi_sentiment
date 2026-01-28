"""Analytics calculator - orchestrates sentiment metric computation.

This module coordinates the analytics pipeline:
1. Load daily reports
2. Build sentiment time series
3. Calculate category momentum
4. Calculate velocity and detect anomalies
5. Generate forecasts
6. Generate insights and LLM commentary
"""

import json
import logging
from datetime import date
from pathlib import Path
from statistics import mean, stdev
from typing import Any

from .commentary import CommentaryGenerator
from .config import AnalyticsConfig, load_config
from .entity_calculator import EntityTrendCalculator
from .models import (
    AnalyticsReport,
    MomentumReport,
    SentimentTimeSeries,
    TrendDirection,
    VelocityReport,
)
from .momentum import MomentumCalculator
from .timeseries import TimeSeriesBuilder
from .velocity import VelocityCalculator

logger = logging.getLogger(__name__)


class AnalyticsCalculator:
    """Orchestrates analytics computation from daily sentiment reports.

    Usage:
        calculator = AnalyticsCalculator()
        report = calculator.generate_report(data_dir="data/daily")
    """

    def __init__(
        self,
        config: AnalyticsConfig | None = None,
        llm_provider: str | None = None,
    ):
        """Initialize calculator with configuration.

        Args:
            config: Analytics configuration. Loads from file if not provided.
            llm_provider: LLM provider for generating commentary.
        """
        self.config = config or load_config()
        self.llm_provider = llm_provider

        self._timeseries_builder = TimeSeriesBuilder(self.config)
        self._momentum_calculator = MomentumCalculator(self.config)
        self._velocity_calculator = VelocityCalculator(self.config)
        self._commentary_generator = CommentaryGenerator(self.config)

    def generate_report(
        self, data_dir: str | Path = "data/daily"
    ) -> AnalyticsReport:
        """Generate complete analytics report from daily data.

        Args:
            data_dir: Directory containing daily JSON reports.

        Returns:
            Complete AnalyticsReport with all analyses.
        """
        data_path = Path(data_dir)
        daily_data = self._load_daily_reports(data_path)

        min_days = self.config.pipeline.min_days_required
        if len(daily_data) < min_days:
            raise ValueError(f"Need at least {min_days} days of data, found {len(daily_data)}")

        engagement_stats = self._compute_engagement_stats(daily_data)
        timeseries = self._timeseries_builder.build(daily_data, engagement_stats)
        momentum = self._momentum_calculator.calculate(timeseries)
        velocity = self._velocity_calculator.calculate(timeseries)
        headline, insights = self._generate_insights(timeseries, momentum, velocity)
        entity_trends = self._generate_entity_trends(data_path)
        commentary = self._commentary_generator.generate(timeseries, daily_data)

        return AnalyticsReport(
            generated_at=date.today(),
            data_range_start=timeseries.start_date,
            data_range_end=timeseries.end_date,
            days_analyzed=len(timeseries.data_points),
            sentiment_timeseries=timeseries,
            momentum=momentum,
            velocity=velocity,
            headline=headline,
            key_insights=insights,
            sentiment_commentary=commentary,
            entity_trends=entity_trends,
        )

    def _load_daily_reports(self, data_dir: Path) -> list[dict[str, Any]]:
        """Load all daily reports, sorted by date."""
        reports = []
        for file_path in sorted(data_dir.glob("*.json")):
            with open(file_path) as f:
                reports.append(json.load(f))
        return reports

    def _compute_engagement_stats(
        self, daily_data: list[dict[str, Any]]
    ) -> dict[str, float]:
        """Compute mean and std of engagement across all quotes."""
        all_scores = []
        for day in daily_data:
            for category in ["fears", "frustrations", "optimism"]:
                for quote in day["all_quotes"][category]:
                    all_scores.append(quote.get("comment_score", 0))

        if len(all_scores) < 2:
            return {"mean": 0, "std": 1}

        return {
            "mean": mean(all_scores),
            "std": stdev(all_scores) if len(all_scores) > 1 else 1,
        }

    def _generate_entity_trends(self, data_path: Path):
        """Generate entity trends report (optional)."""
        try:
            calculator = EntityTrendCalculator()
            return calculator.generate_report(data_path, top_n=10)
        except Exception:
            return None

    def _generate_insights(
        self,
        timeseries: SentimentTimeSeries,
        momentum: MomentumReport,
        velocity: VelocityReport,
    ) -> tuple[str, list[str]]:
        """Generate headline and key insights with data-driven details."""
        latest = timeseries.data_points[-1]
        insights = []

        headline = self._generate_headline(timeseries, momentum, latest)

        # Dominant category insight
        categories = {
            "fears": latest.fears_zscore_sum,
            "frustrations": latest.frustrations_zscore_sum,
            "optimism": latest.optimism_zscore_sum,
        }
        dominant = max(categories, key=lambda k: abs(categories[k]))
        dominant_count = getattr(latest, f"{dominant}_count")
        insights.append(
            f"{dominant.title()} dominates with {dominant_count} quotes "
            f"(score: {categories[dominant]:+.1f})"
        )

        # Momentum insight
        fastest = momentum.fastest_rising
        fastest_data = getattr(momentum, fastest)
        roc_direction = "up" if fastest_data.roc_7d > 0 else "down"
        insights.append(
            f"{fastest.title()} trending {roc_direction} {abs(fastest_data.roc_7d):.0f}% "
            f"over 7 days ({fastest_data.trend_strength} momentum)"
        )

        # Alert insight
        if velocity.alert_count > 0:
            alert = velocity.alerts[0] if velocity.alerts else None
            if alert:
                insights.append(
                    f"Alert: {alert.description}"
                )
        elif velocity.warning_count > 0:
            insights.append(
                f"{velocity.warning_count} warning(s) detected in velocity metrics"
            )

        # Engagement insight
        engagements = [dp.avg_engagement for dp in timeseries.data_points]
        avg_eng = mean(engagements)
        eng_pct_diff = ((engagements[-1] - avg_eng) / avg_eng * 100) if avg_eng > 0 else 0
        eng_direction = "above" if eng_pct_diff > 0 else "below"
        insights.append(
            f"Engagement {abs(eng_pct_diff):.0f}% {eng_direction} average "
            f"({engagements[-1]:.1f} vs {avg_eng:.1f})"
        )

        return headline, insights

    def _generate_headline(
        self,
        timeseries: SentimentTimeSeries,
        momentum: MomentumReport,
        latest,
    ) -> str:
        """Generate data-driven headline based on trend and momentum."""
        # Calculate week-over-week change
        if len(timeseries.data_points) >= 7:
            week_ago = timeseries.data_points[-7].composite_score
            current = latest.composite_score
            pct_change = ((current - week_ago) / abs(week_ago) * 100) if week_ago != 0 else 0
        else:
            pct_change = 0

        # Find the driving category
        fastest = momentum.fastest_rising

        if timeseries.overall_trend == TrendDirection.RISING:
            if abs(pct_change) > 5:
                return f"Sentiment up {abs(pct_change):.0f}% this week, driven by {fastest}"
            return f"Positive momentum building, led by {fastest}"

        if timeseries.overall_trend == TrendDirection.FALLING:
            falling = momentum.fastest_falling
            if abs(pct_change) > 5:
                return f"Sentiment down {abs(pct_change):.0f}% this week, {falling} declining"
            return f"Negative trend emerging in {falling}"

        # Stable trend
        if latest.composite_score > 0:
            return f"Stable positive sentiment (score: {latest.composite_score:+.1f})"
        if latest.composite_score < 0:
            return f"Stable negative sentiment (score: {latest.composite_score:+.1f})"
        return "Neutral sentiment: positive and negative balanced"
