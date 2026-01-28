"""Time series builder for sentiment analytics.

Builds sentiment time series from daily reports with:
- Z-score weighted scoring per category
- Exponential moving average smoothing
- Linear regression for trend direction
"""

from datetime import date
from statistics import mean, stdev
from typing import Any

from .config import AnalyticsConfig, get_intensity_z
from .models import DailySentimentScore, SentimentTimeSeries, TrendDirection


class TimeSeriesBuilder:
    """Builds sentiment time series from daily reports."""

    def __init__(self, config: AnalyticsConfig):
        self.config = config

    def build(
        self,
        daily_data: list[dict[str, Any]],
        engagement_stats: dict[str, float],
    ) -> SentimentTimeSeries:
        """Build sentiment time series from daily reports.

        Args:
            daily_data: List of daily report dictionaries.
            engagement_stats: Mean and std of engagement scores.

        Returns:
            SentimentTimeSeries with trend analysis.
        """
        data_points = [
            self._calculate_daily_score(day, engagement_stats)
            for day in daily_data
        ]

        self._apply_ema(data_points)

        scores = [dp.composite_score for dp in data_points]
        mean_score = mean(scores)
        std_score = stdev(scores) if len(scores) > 1 else 0

        slope, r_squared = self._linear_regression(scores)
        trend = self._classify_trend(slope)

        return SentimentTimeSeries(
            start_date=data_points[0].date,
            end_date=data_points[-1].date,
            data_points=data_points,
            mean_score=mean_score,
            std_dev=std_score,
            min_score=min(scores),
            max_score=max(scores),
            overall_trend=trend,
            trend_slope=slope,
            trend_r_squared=r_squared,
        )

    def _calculate_daily_score(
        self,
        day_data: dict[str, Any],
        engagement_stats: dict[str, float],
    ) -> DailySentimentScore:
        """Calculate z-score weighted sentiment for one day."""
        report_date = date.fromisoformat(day_data["date_id"])

        category_scores = {}
        category_counts = {}
        total_engagement = 0

        for category in ["fears", "frustrations", "optimism"]:
            quotes = day_data["all_quotes"][category]
            zscore_sum = 0.0

            for quote in quotes:
                engagement = quote.get("comment_score", 0)
                intensity = quote["intensity"]

                engagement_z = self._calculate_engagement_z(
                    engagement, engagement_stats
                )
                intensity_z = get_intensity_z(intensity, self.config)

                quote_score = engagement_z + intensity_z
                zscore_sum += quote_score
                total_engagement += engagement

            category_scores[category] = zscore_sum
            category_counts[category] = len(quotes)

        negativity = category_scores["fears"] + category_scores["frustrations"]
        positivity = category_scores["optimism"]
        composite = positivity - negativity
        total_quotes = sum(category_counts.values())

        return DailySentimentScore(
            date=report_date,
            fears_count=category_counts["fears"],
            frustrations_count=category_counts["frustrations"],
            optimism_count=category_counts["optimism"],
            total_quotes=total_quotes,
            fears_zscore_sum=category_scores["fears"],
            frustrations_zscore_sum=category_scores["frustrations"],
            optimism_zscore_sum=category_scores["optimism"],
            negativity_score=negativity,
            positivity_score=positivity,
            composite_score=composite,
            ema_score=None,
            ema_negativity=None,
            ema_positivity=None,
            total_engagement=total_engagement,
            avg_engagement=total_engagement / total_quotes if total_quotes > 0 else 0,
        )

    def _calculate_engagement_z(
        self, engagement: int, stats: dict[str, float]
    ) -> float:
        """Calculate engagement z-score with floor."""
        if stats["std"] > 0:
            z = (engagement - stats["mean"]) / stats["std"]
        else:
            z = 0
        return max(z, self.config.engagement.z_floor)

    def _apply_ema(self, data_points: list[DailySentimentScore]) -> None:
        """Apply exponential moving average to scores."""
        span = self.config.ema.span
        min_periods = self.config.ema.min_periods
        alpha = 2 / (span + 1)

        for i, dp in enumerate(data_points):
            if i < min_periods - 1:
                dp.ema_score = None
                dp.ema_negativity = None
                dp.ema_positivity = None
            elif i == min_periods - 1:
                dp.ema_score = mean(p.composite_score for p in data_points[: i + 1])
                dp.ema_negativity = mean(p.negativity_score for p in data_points[: i + 1])
                dp.ema_positivity = mean(p.positivity_score for p in data_points[: i + 1])
            else:
                prev = data_points[i - 1]
                if prev.ema_score is not None:
                    dp.ema_score = alpha * dp.composite_score + (1 - alpha) * prev.ema_score
                if prev.ema_negativity is not None:
                    dp.ema_negativity = alpha * dp.negativity_score + (1 - alpha) * prev.ema_negativity
                if prev.ema_positivity is not None:
                    dp.ema_positivity = alpha * dp.positivity_score + (1 - alpha) * prev.ema_positivity

    def _linear_regression(self, values: list[float]) -> tuple[float, float]:
        """Fit linear regression and return (slope, r_squared)."""
        n = len(values)
        if n < 2:
            return 0.0, 0.0

        x = list(range(n))
        x_mean = mean(x)
        y_mean = mean(values)

        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return 0.0, 0.0

        slope = numerator / denominator

        ss_tot = sum((y - y_mean) ** 2 for y in values)
        if ss_tot == 0:
            return slope, 1.0

        intercept = y_mean - slope * x_mean
        predictions = [slope * x[i] + intercept for i in range(n)]
        ss_res = sum((values[i] - predictions[i]) ** 2 for i in range(n))
        r_squared = 1 - (ss_res / ss_tot)

        return slope, max(0, r_squared)

    def _classify_trend(self, slope: float) -> TrendDirection:
        """Classify trend direction from slope."""
        threshold = self.config.trend.slope_stable_threshold
        if abs(slope) < threshold:
            return TrendDirection.STABLE
        return TrendDirection.RISING if slope > 0 else TrendDirection.FALLING