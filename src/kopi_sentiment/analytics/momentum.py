"""Momentum calculator for sentiment categories.

Calculates rate of change and EMA momentum for FFO categories:
- 1-day, 3-day, 7-day rate of change
- Trend classification (rising/falling/stable)
- Trend strength (weak/moderate/strong)
"""

from .config import AnalyticsConfig
from .models import (
    CategoryMomentum,
    DailySentimentScore,
    MomentumReport,
    SentimentTimeSeries,
    TrendDirection,
)


class MomentumCalculator:
    """Calculates momentum for FFO categories."""

    def __init__(self, config: AnalyticsConfig):
        self.config = config

    def calculate(self, timeseries: SentimentTimeSeries) -> MomentumReport:
        """Calculate momentum for all FFO categories.

        Args:
            timeseries: Sentiment time series with data points.

        Returns:
            MomentumReport with category-level momentum analysis.
        """
        data = timeseries.data_points
        report_date = data[-1].date

        momentum_results = {
            category: self._calculate_category_momentum(data, category)
            for category in ["fears", "frustrations", "optimism"]
        }

        rocs = {cat: m.roc_7d for cat, m in momentum_results.items()}
        fastest_rising = max(rocs, key=rocs.get)  # type: ignore
        fastest_falling = min(rocs, key=rocs.get)  # type: ignore

        return MomentumReport(
            report_date=report_date,
            lookback_days=min(7, len(data)),
            fears=momentum_results["fears"],
            frustrations=momentum_results["frustrations"],
            optimism=momentum_results["optimism"],
            fastest_rising=fastest_rising,
            fastest_falling=fastest_falling,
        )

    def _calculate_category_momentum(
        self,
        data: list[DailySentimentScore],
        category: str,
    ) -> CategoryMomentum:
        """Calculate momentum for a single category."""
        zscore_attr = f"{category}_zscore_sum"
        values = [getattr(dp, zscore_attr) for dp in data]

        current = values[-1]
        current_count = getattr(data[-1], f"{category}_count")

        roc_1d = self._rate_of_change(current, values, self.config.momentum.roc_1d_lookback)
        roc_3d = self._rate_of_change(current, values, self.config.momentum.roc_3d_lookback)
        roc_7d = self._rate_of_change(current, values, self.config.momentum.roc_7d_lookback)

        ema_momentum = self._calculate_ema_momentum(values)
        trend, strength = self._classify_trend(roc_7d)

        return CategoryMomentum(
            category=category,  # type: ignore
            current_count=current_count,
            current_zscore_sum=current,
            roc_1d=roc_1d,
            roc_3d=roc_3d,
            roc_7d=roc_7d,
            ema_momentum=ema_momentum,
            trend=trend,
            trend_strength=strength,  # type: ignore
        )

    def _rate_of_change(
        self, current: float, values: list[float], lookback: int
    ) -> float:
        """Calculate rate of change percentage."""
        if len(values) < lookback:
            return self._rate_of_change(current, values, len(values))

        past = values[-lookback]
        if past == 0:
            return 0.0 if current == 0 else 100.0
        return ((current - past) / abs(past)) * 100

    def _calculate_ema_momentum(self, values: list[float]) -> float:
        """Calculate EMA of daily changes."""
        if len(values) < 2:
            return 0.0

        daily_changes = [values[i] - values[i - 1] for i in range(1, len(values))]
        span = min(self.config.ema.span, len(daily_changes))
        alpha = 2 / (span + 1)

        ema = daily_changes[0]
        for v in daily_changes[1:]:
            ema = alpha * v + (1 - alpha) * ema
        return ema

    def _classify_trend(
        self, roc_7d: float
    ) -> tuple[TrendDirection, str]:
        """Classify trend direction and strength from 7-day ROC."""
        weak_threshold = self.config.trend.roc_weak_threshold
        strong_threshold = self.config.trend.roc_strong_threshold

        if abs(roc_7d) < weak_threshold:
            return TrendDirection.STABLE, "weak"

        direction = TrendDirection.RISING if roc_7d > 0 else TrendDirection.FALLING
        strength = "strong" if abs(roc_7d) > strong_threshold else "moderate"
        return direction, strength
