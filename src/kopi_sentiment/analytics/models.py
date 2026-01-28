"""Data models for analytics and trend analysis.

See METHODOLOGY.md for detailed explanation of the scoring approach.
See analytics_config.yaml for the empirically-derived parameters.

Summary:
- Quote score = engagement_z + intensity_z (both in z-score units)
- Intensity z-scores loaded from config (derived from data distribution)
- Alerts use standard statistical thresholds from config
"""

from datetime import date
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


# =============================================================================
# Enums
# =============================================================================

class AlertSeverity(str, Enum):
    """Alert levels based on z-score thresholds (configured in analytics_config.yaml)."""
    NONE = "none"
    NOTABLE = "notable"
    WARNING = "warning"
    ALERT = "alert"


class TrendDirection(str, Enum):
    """Direction of trend movement."""
    RISING = "rising"
    FALLING = "falling"
    STABLE = "stable"


# =============================================================================
# Sentiment Index Models
# =============================================================================

class DailySentimentScore(BaseModel):
    """Sentiment scores for a single day."""
    date: date

    # Raw counts per category
    fears_count: int
    frustrations_count: int
    optimism_count: int
    total_quotes: int

    # Z-score weighted sums (sum of engagement_z + intensity_z for each quote)
    fears_zscore_sum: float
    frustrations_zscore_sum: float
    optimism_zscore_sum: float

    # Dual sentiment scores for meaningful analysis
    negativity_score: float = Field(
        default=0.0,
        description="fears + frustrations z-score sum"
    )
    positivity_score: float = Field(
        default=0.0,
        description="optimism z-score sum"
    )

    # Composite score = (positive categories) - (negative categories)
    composite_score: float = Field(
        description="optimism - (fears + frustrations) in z-score units"
    )

    # Smoothed scores
    ema_score: float | None = Field(
        default=None,
        description="Exponential moving average for composite trend smoothing"
    )
    ema_negativity: float | None = Field(
        default=None,
        description="EMA for negativity trend"
    )
    ema_positivity: float | None = Field(
        default=None,
        description="EMA for positivity trend"
    )

    # Engagement context
    total_engagement: int
    avg_engagement: float


class SentimentTimeSeries(BaseModel):
    """Complete time series with trend analysis."""
    start_date: date
    end_date: date
    data_points: list[DailySentimentScore]

    # Statistical summary
    mean_score: float
    std_dev: float
    min_score: float
    max_score: float

    # Linear regression trend
    overall_trend: TrendDirection
    trend_slope: float = Field(description="Points per day")
    trend_r_squared: float = Field(description="R² of linear fit (0-1)")


# =============================================================================
# Category Momentum Models
# =============================================================================

class CategoryMomentum(BaseModel):
    """Momentum for one FFO category."""
    category: Literal["fears", "frustrations", "optimism"]

    current_count: int
    current_zscore_sum: float

    # Rate of change (%)
    roc_1d: float
    roc_3d: float
    roc_7d: float

    # Smoothed momentum
    ema_momentum: float

    # Classification
    trend: TrendDirection
    trend_strength: Literal["weak", "moderate", "strong"]


class MomentumReport(BaseModel):
    """Momentum across all categories."""
    report_date: date
    lookback_days: int = 7

    fears: CategoryMomentum
    frustrations: CategoryMomentum
    optimism: CategoryMomentum

    fastest_rising: str
    fastest_falling: str


# =============================================================================
# Velocity & Anomaly Detection
# =============================================================================

class VelocityMetric(BaseModel):
    """Velocity for a single metric."""
    metric_name: str
    current_value: float

    velocity: float
    velocity_zscore: float

    acceleration: float

    historical_mean: float
    historical_std: float

    alert_level: AlertSeverity


class TrendVelocityAlert(BaseModel):
    """Alert triggered by anomalous velocity."""
    alert_id: str
    triggered_at: date
    severity: AlertSeverity

    metric: str
    category: str | None = None

    current_value: float
    expected_value: float
    z_score: float
    percentile: float

    direction: TrendDirection
    description: str

    top_quotes: list[str] = Field(default=[])


class VelocityReport(BaseModel):
    """Complete velocity analysis."""
    report_date: date
    lookback_days: int = 7

    metrics: list[VelocityMetric]
    alerts: list[TrendVelocityAlert]

    total_alerts: int
    alert_count: int
    warning_count: int


# =============================================================================
# Complete Report
# =============================================================================

class AnalyticsReport(BaseModel):
    """Main output of the analytics pipeline."""
    schema_version: str = "analytics_v1"
    generated_at: date
    data_range_start: date
    data_range_end: date
    days_analyzed: int

    sentiment_timeseries: SentimentTimeSeries
    momentum: MomentumReport
    velocity: VelocityReport

    headline: str
    key_insights: list[str]
    sentiment_commentary: str = ""  # LLM-generated plain-language explanation of sentiment scores

    methodology: str = Field(
        default="See METHODOLOGY.md. Scores use z-score normalization with "
        "empirically-derived intensity weights from analytics_config.yaml. "
        "Alerts at |z| >= threshold (configurable, default 2.0 for p < 0.05)."
    )

    # Entity trends (optional)
    entity_trends: "EntityTrendsReport | None" = None


# =============================================================================
# Entity Trends Models
# =============================================================================

class EntityDayData(BaseModel):
    """Entity data for a single day."""
    date: date
    engagement: int
    mention_count: int
    categories: list[str]


class EntityTrend(BaseModel):
    """Trend data for a single entity across multiple days."""
    entity: str
    total_engagement: int
    total_mentions: int
    days_present: int
    daily_data: list[EntityDayData]
    dominant_category: str
    trend_direction: str = "stable"  # "rising", "falling", "stable"


class EntityTrendsReport(BaseModel):
    """Complete entity trends report."""
    generated_at: date
    days_analyzed: int
    top_entities: list[EntityTrend]

