"""Weekly analytics calculator - generates analytics from weekly reports.

This module handles analytics generation from weekly sentiment reports,
creating a timeseries where each data point represents one week's aggregated data.

Following SOLID principles:
- SRP: Single responsibility for weekly report analytics
- OCP: Extends analytics capability without modifying AnalyticsCalculator
- DIP: Reuses existing calculators via composition
"""

import json
import logging
from datetime import date
from pathlib import Path
from statistics import mean, stdev

from .commentary import CommentaryGenerator
from .config import AnalyticsConfig, load_config
from .models import (
    AnalyticsReport,
    CategoryMomentum,
    DailySentimentScore,
    EntityDayData,
    EntityTrend,
    EntityTrendsReport,
    MomentumReport,
    SentimentTimeSeries,
    TrendDirection,
    VelocityReport,
)
from .momentum import MomentumCalculator
from .velocity import VelocityCalculator

logger = logging.getLogger(__name__)


class WeeklyAnalyticsCalculator:
    """Generates analytics from weekly sentiment reports.

    Unlike AnalyticsCalculator (which uses daily reports), this calculator
    reads weekly report JSONs and creates a timeseries across multiple weeks.

    Usage:
        calculator = WeeklyAnalyticsCalculator()
        report = calculator.generate_report(data_dir="web/public/data/weekly")
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

        self._momentum_calculator = MomentumCalculator(self.config)
        self._velocity_calculator = VelocityCalculator(self.config)
        self._commentary_generator = CommentaryGenerator(self.config)

    def generate_report(
        self,
        data_dir: str | Path = "web/public/data/weekly",
        min_weeks: int = 3,
    ) -> AnalyticsReport:
        """Generate analytics report from weekly reports.

        Args:
            data_dir: Directory containing weekly JSON reports.
            min_weeks: Minimum number of weeks required.

        Returns:
            Complete AnalyticsReport with week-over-week analysis.
        """
        data_path = Path(data_dir)
        weekly_reports = self._load_weekly_reports(data_path)

        if len(weekly_reports) < min_weeks:
            raise ValueError(
                f"Need at least {min_weeks} weeks of data, found {len(weekly_reports)}"
            )

        timeseries = self._build_weekly_timeseries(weekly_reports)
        momentum = self._calculate_momentum(timeseries, weekly_reports)
        velocity = self._velocity_calculator.calculate(timeseries)
        headline, insights = self._generate_insights(timeseries, momentum, velocity)
        # Entity trends use only the latest week (Main Characters = this week's topics)
        entity_trends = self._aggregate_entity_trends([weekly_reports[-1]])
        commentary = self._commentary_generator.generate(timeseries, weekly_reports)

        return AnalyticsReport(
            generated_at=date.today(),
            data_range_start=timeseries.start_date,
            data_range_end=timeseries.end_date,
            days_analyzed=len(timeseries.data_points),  # Actually weeks
            sentiment_timeseries=timeseries,
            momentum=momentum,
            velocity=velocity,
            headline=headline,
            key_insights=insights,
            sentiment_commentary=commentary,
            entity_trends=entity_trends,
            methodology="Weekly analytics from aggregated weekly reports. "
            "Each data point represents one week's sentiment. "
            "Momentum/velocity calculated week-over-week.",
        )

    def _load_weekly_reports(self, data_dir: Path) -> list[dict]:
        """Load weekly reports sorted by week ID.

        Args:
            data_dir: Directory containing weekly JSON reports.

        Returns:
            List of weekly report data, sorted by week_start date.
        """
        reports = []
        for file_path in sorted(data_dir.glob("*.json")):
            # Skip files that aren't week reports (e.g., 2026-W02.json)
            if not file_path.stem.startswith("202") or "-W" not in file_path.stem:
                continue

            with open(file_path) as f:
                report = json.load(f)
                # Skip empty reports
                all_quotes = report.get("all_quotes", {})
                total_quotes = sum(
                    len(all_quotes.get(cat, []))
                    for cat in ["fears", "frustrations", "optimism"]
                )
                if total_quotes == 0:
                    logger.debug(f"Skipping empty weekly report: {file_path.name}")
                    continue

                reports.append(report)

        # Sort by week_start date
        reports.sort(key=lambda r: r.get("week_start", ""))
        return reports

    def _build_weekly_timeseries(
        self, weekly_reports: list[dict]
    ) -> SentimentTimeSeries:
        """Build timeseries from weekly reports.

        Each weekly report becomes a single data point in the timeseries.

        Args:
            weekly_reports: List of weekly report dictionaries.

        Returns:
            SentimentTimeSeries with one point per week.
        """
        data_points = []

        for report in weekly_reports:
            data_point = self._weekly_report_to_data_point(report)
            data_points.append(data_point)

        # Calculate EMA for smoothing
        self._apply_ema(data_points)

        # Calculate statistics and trend
        scores = [dp.composite_score for dp in data_points]
        mean_score = mean(scores)
        std_dev = stdev(scores) if len(scores) > 1 else 1.0

        # Linear regression for trend
        trend_direction, slope, r_squared = self._calculate_trend(scores)

        return SentimentTimeSeries(
            start_date=data_points[0].date,
            end_date=data_points[-1].date,
            data_points=data_points,
            mean_score=mean_score,
            std_dev=std_dev,
            min_score=min(scores),
            max_score=max(scores),
            overall_trend=trend_direction,
            trend_slope=slope,
            trend_r_squared=r_squared,
        )

    def _weekly_report_to_data_point(self, report: dict) -> DailySentimentScore:
        """Convert a weekly report to a DailySentimentScore data point.

        Args:
            report: Weekly report dictionary.

        Returns:
            DailySentimentScore representing the week's aggregated sentiment.
        """
        all_quotes = report.get("all_quotes", {})

        # Count quotes per category
        fears_quotes = all_quotes.get("fears", [])
        frust_quotes = all_quotes.get("frustrations", [])
        optim_quotes = all_quotes.get("optimism", [])

        fears_count = len(fears_quotes)
        frust_count = len(frust_quotes)
        optim_count = len(optim_quotes)
        total_quotes = fears_count + frust_count + optim_count

        # Calculate z-score sums based on intensity
        fears_zscore = self._calculate_category_zscore(fears_quotes, "fears")
        frust_zscore = self._calculate_category_zscore(frust_quotes, "frustrations")
        optim_zscore = self._calculate_category_zscore(optim_quotes, "optimism")

        # Calculate engagement
        total_engagement = sum(
            q.get("comment_score", 0)
            for cat_quotes in [fears_quotes, frust_quotes, optim_quotes]
            for q in cat_quotes
        )
        avg_engagement = total_engagement / total_quotes if total_quotes > 0 else 0

        # Calculate dual sentiment scores
        negativity_score = fears_zscore + frust_zscore
        positivity_score = optim_zscore
        composite_score = positivity_score - negativity_score

        # Use week_end as the date for this data point
        week_end_str = report.get("week_end", report.get("week_start", ""))
        week_date = date.fromisoformat(week_end_str) if week_end_str else date.today()

        return DailySentimentScore(
            date=week_date,
            fears_count=fears_count,
            frustrations_count=frust_count,
            optimism_count=optim_count,
            total_quotes=total_quotes,
            fears_zscore_sum=fears_zscore,
            frustrations_zscore_sum=frust_zscore,
            optimism_zscore_sum=optim_zscore,
            negativity_score=negativity_score,
            positivity_score=positivity_score,
            composite_score=composite_score,
            total_engagement=total_engagement,
            avg_engagement=avg_engagement,
        )

    def _calculate_category_zscore(
        self, quotes: list[dict], category: str
    ) -> float:
        """Calculate z-score sum for a category based on quote intensities.

        Args:
            quotes: List of quote dictionaries.
            category: Category name (fears, frustrations, optimism).

        Returns:
            Sum of z-scores for the category.
        """
        if not quotes:
            return 0.0

        # Intensity weights from config
        intensity_config = self.config.intensity_z_scores
        intensity_weights = {
            "mild": intensity_config.mild,
            "moderate": intensity_config.moderate,
            "strong": intensity_config.strong,
        }

        total_zscore = 0.0
        for quote in quotes:
            intensity = quote.get("intensity", "moderate")
            intensity_z = intensity_weights.get(intensity, 0.0)
            total_zscore += intensity_z

        return total_zscore

    def _apply_ema(self, data_points: list[DailySentimentScore]) -> None:
        """Apply exponential moving average to data points.

        Args:
            data_points: List of data points to update in place.
        """
        # Calculate alpha from EMA span: alpha = 2 / (span + 1)
        alpha = 2 / (self.config.ema.span + 1)

        for i, dp in enumerate(data_points):
            if i == 0:
                dp.ema_score = dp.composite_score
                dp.ema_negativity = dp.negativity_score
                dp.ema_positivity = dp.positivity_score
            else:
                prev = data_points[i - 1]
                dp.ema_score = alpha * dp.composite_score + (1 - alpha) * (prev.ema_score or dp.composite_score)
                dp.ema_negativity = alpha * dp.negativity_score + (1 - alpha) * (prev.ema_negativity or dp.negativity_score)
                dp.ema_positivity = alpha * dp.positivity_score + (1 - alpha) * (prev.ema_positivity or dp.positivity_score)

    def _calculate_trend(
        self, scores: list[float]
    ) -> tuple[TrendDirection, float, float]:
        """Calculate linear trend from scores.

        Args:
            scores: List of composite scores.

        Returns:
            Tuple of (direction, slope, r_squared).
        """
        n = len(scores)
        if n < 2:
            return TrendDirection.STABLE, 0.0, 0.0

        # Linear regression
        x_mean = (n - 1) / 2
        y_mean = mean(scores)

        numerator = sum((i - x_mean) * (y - y_mean) for i, y in enumerate(scores))
        denominator = sum((i - x_mean) ** 2 for i in range(n))

        slope = numerator / denominator if denominator != 0 else 0.0

        # R-squared
        ss_res = sum((y - (y_mean + slope * (i - x_mean))) ** 2 for i, y in enumerate(scores))
        ss_tot = sum((y - y_mean) ** 2 for y in scores)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0

        # Determine direction
        slope_threshold = self.config.trend.slope_stable_threshold
        if slope > slope_threshold:
            direction = TrendDirection.RISING
        elif slope < -slope_threshold:
            direction = TrendDirection.FALLING
        else:
            direction = TrendDirection.STABLE

        return direction, slope, max(0, r_squared)

    def _calculate_momentum(
        self, timeseries: SentimentTimeSeries, weekly_reports: list[dict]
    ) -> MomentumReport:
        """Calculate week-over-week momentum.

        Args:
            timeseries: The weekly timeseries.
            weekly_reports: List of weekly report dictionaries.

        Returns:
            MomentumReport with week-over-week analysis.
        """
        # Use the momentum calculator with the timeseries
        return self._momentum_calculator.calculate(timeseries)

    def _aggregate_entity_trends(
        self, weekly_reports: list[dict]
    ) -> EntityTrendsReport | None:
        """Aggregate entity trends from weekly reports.

        Combines entities mentioned across weeks into a single trends report.

        Args:
            weekly_reports: List of weekly report dictionaries.

        Returns:
            EntityTrendsReport or None if no entities found.
        """
        # Aggregate entities from thematic_clusters (mirrors daily entity_calculator)
        entity_data: dict[str, dict] = {}

        for report in weekly_reports:
            week_end_str = report.get("week_end", report.get("week_start", ""))
            week_date = date.fromisoformat(week_end_str) if week_end_str else date.today()

            clusters = report.get("thematic_clusters", [])

            for cluster in clusters:
                entities = cluster.get("entities", [])
                engagement = cluster.get("engagement_score", 0)
                category = cluster.get("dominant_emotion", "")

                for entity in entities:
                    entity_normalized = entity.strip().upper()

                    if entity_normalized not in entity_data:
                        entity_data[entity_normalized] = {
                            "total_engagement": 0,
                            "total_mentions": 0,
                            "weeks_present": set(),
                            "weekly_data": {},
                            "categories": {},
                        }

                    entity_data[entity_normalized]["total_engagement"] += engagement
                    entity_data[entity_normalized]["total_mentions"] += 1
                    entity_data[entity_normalized]["weeks_present"].add(week_date)

                    if week_date not in entity_data[entity_normalized]["weekly_data"]:
                        entity_data[entity_normalized]["weekly_data"][week_date] = {
                            "engagement": 0,
                            "mentions": 0,
                            "categories": [],
                        }
                    entity_data[entity_normalized]["weekly_data"][week_date]["engagement"] += engagement
                    entity_data[entity_normalized]["weekly_data"][week_date]["mentions"] += 1
                    if category and category not in entity_data[entity_normalized]["weekly_data"][week_date]["categories"]:
                        entity_data[entity_normalized]["weekly_data"][week_date]["categories"].append(category)

                    entity_data[entity_normalized]["categories"][category] = (
                        entity_data[entity_normalized]["categories"].get(category, 0) + 1
                    )

        if not entity_data:
            return None

        # Convert to EntityTrend objects
        entity_trends = []
        for entity, data in entity_data.items():
            # Determine dominant category
            dominant_category = max(data["categories"], key=data["categories"].get)

            # Build daily_data (actually weekly data)
            daily_data = []
            for week_date in sorted(data["weekly_data"].keys()):
                week_info = data["weekly_data"][week_date]
                daily_data.append(
                    EntityDayData(
                        date=week_date,
                        engagement=week_info["engagement"],
                        mention_count=week_info["mentions"],
                        categories=week_info["categories"],
                    )
                )

            # Determine trend direction
            if len(daily_data) >= 2:
                first_half_eng = sum(d.engagement for d in daily_data[: len(daily_data) // 2])
                second_half_eng = sum(d.engagement for d in daily_data[len(daily_data) // 2:])
                if second_half_eng > first_half_eng * 1.2:
                    trend_direction = "rising"
                elif second_half_eng < first_half_eng * 0.8:
                    trend_direction = "falling"
                else:
                    trend_direction = "stable"
            else:
                trend_direction = "stable"

            entity_trends.append(
                EntityTrend(
                    entity=entity,
                    total_engagement=data["total_engagement"],
                    total_mentions=data["total_mentions"],
                    days_present=len(data["weeks_present"]),
                    daily_data=daily_data,
                    dominant_category=dominant_category,
                    trend_direction=trend_direction,
                )
            )

        # Sort by engagement and take top entities
        entity_trends.sort(key=lambda e: e.total_engagement, reverse=True)
        top_entities = entity_trends[:15]

        return EntityTrendsReport(
            generated_at=date.today(),
            days_analyzed=len(weekly_reports),  # Actually weeks
            top_entities=top_entities,
        )

    def _generate_insights(
        self,
        timeseries: SentimentTimeSeries,
        momentum: MomentumReport,
        velocity: VelocityReport,
    ) -> tuple[str, list[str]]:
        """Generate headline and insights for weekly analytics.

        Args:
            timeseries: Weekly timeseries.
            momentum: Momentum report.
            velocity: Velocity report.

        Returns:
            Tuple of (headline, list of insights).
        """
        latest = timeseries.data_points[-1]
        insights = []

        # Headline
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
            f"{dominant.title()} dominates this week with {dominant_count} quotes "
            f"(score: {categories[dominant]:+.1f})"
        )

        # Week-over-week change
        if len(timeseries.data_points) >= 2:
            prev_week = timeseries.data_points[-2]
            score_change = latest.composite_score - prev_week.composite_score
            direction = "up" if score_change > 0 else "down"
            insights.append(
                f"Overall sentiment {direction} {abs(score_change):.1f} points from last week"
            )

        # Momentum insight
        fastest = momentum.fastest_rising
        fastest_data = getattr(momentum, fastest)
        roc_direction = "up" if fastest_data.roc_7d > 0 else "down"
        insights.append(
            f"{fastest.title()} momentum {roc_direction} {abs(fastest_data.roc_7d):.0f}% "
            f"({fastest_data.trend_strength} trend)"
        )

        # Alert insight
        if velocity.alert_count > 0:
            alert = velocity.alerts[0] if velocity.alerts else None
            if alert:
                insights.append(f"Alert: {alert.description}")

        return headline, insights

    def _generate_headline(
        self,
        timeseries: SentimentTimeSeries,
        momentum: MomentumReport,
        latest: DailySentimentScore,
    ) -> str:
        """Generate data-driven headline.

        Args:
            timeseries: Weekly timeseries.
            momentum: Momentum report.
            latest: Latest week's data point.

        Returns:
            Headline string.
        """
        fastest = momentum.fastest_rising

        if timeseries.overall_trend == TrendDirection.RISING:
            return f"Weekly sentiment trending up, driven by {fastest}"

        if timeseries.overall_trend == TrendDirection.FALLING:
            falling = momentum.fastest_falling
            return f"Weekly sentiment declining, {falling} falling"

        if latest.composite_score > 0:
            return f"Stable positive sentiment this week (score: {latest.composite_score:+.1f})"
        if latest.composite_score < 0:
            return f"Stable negative sentiment this week (score: {latest.composite_score:+.1f})"
        return "Neutral weekly sentiment: positive and negative balanced"