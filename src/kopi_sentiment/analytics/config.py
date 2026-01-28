"""Analytics configuration.

This module loads scoring parameters from a JSON config file.
Parameters are empirically derived - see METHODOLOGY.md for derivation details.

To recalibrate: run `python -m kopi_sentiment.analytics.calibrate`
"""

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


# =============================================================================
# Config Models
# =============================================================================

class IntensityConfig(BaseModel):
    """Z-score mappings for intensity levels."""
    mild: float = Field(description="Z-score for mild intensity")
    moderate: float = Field(description="Z-score for moderate intensity")
    strong: float = Field(description="Z-score for strong intensity")


class CalibrationMetadata(BaseModel):
    """Metadata about when/how the calibration was done."""
    calibrated_at: str = Field(description="Date of calibration")
    data_range_start: str = Field(description="Start of data used for calibration")
    data_range_end: str = Field(description="End of data used for calibration")
    total_quotes_analyzed: int = Field(description="Number of quotes in calibration dataset")
    distribution: dict[str, float] = Field(description="Observed distribution percentages")


class AlertThresholds(BaseModel):
    """Z-score thresholds for alert levels."""
    notable: float = Field(default=1.0, description="|z| threshold for 'notable'")
    warning: float = Field(default=1.5, description="|z| threshold for 'warning'")
    alert: float = Field(default=2.0, description="|z| threshold for 'alert' (p < 0.05)")
    significant_z: float = Field(default=2.0, description="Z-score for 'significant' label")


class EngagementConfig(BaseModel):
    """Engagement scoring parameters."""
    z_floor: float = Field(
        default=-2.0,
        description="Minimum z-score for 0-engagement quotes (Bayesian floor)"
    )


class EMAConfig(BaseModel):
    """Exponential moving average parameters."""
    span: int = Field(default=7, description="EMA span in days")
    min_periods: int = Field(default=3, description="Minimum data points before calculating EMA")


class TrendConfig(BaseModel):
    """Trend classification thresholds."""
    slope_stable_threshold: float = Field(default=0.5, description="Slope below this is 'stable'")
    roc_weak_threshold: float = Field(default=10, description="ROC% below this is 'weak' trend")
    roc_strong_threshold: float = Field(default=25, description="ROC% above this is 'strong' trend")


class MomentumConfig(BaseModel):
    """Momentum calculation parameters."""
    roc_1d_lookback: int = Field(default=2, description="Index offset for 1-day ROC")
    roc_3d_lookback: int = Field(default=4, description="Index offset for 3-day ROC")
    roc_7d_lookback: int = Field(default=8, description="Index offset for 7-day ROC")


class VelocityConfig(BaseModel):
    """Velocity calculation parameters."""
    lookback_days: int = Field(default=7, description="Lookback period for velocity report")


class PipelineConfig(BaseModel):
    """Pipeline requirements."""
    min_days_required: int = Field(default=3, description="Minimum days of data required")


class CommentaryConfig(BaseModel):
    """LLM commentary generation settings."""
    model: str = Field(default="claude-sonnet-4-20250514", description="Model for commentary")
    max_tokens: int = Field(default=500, description="Max tokens for commentary response")


class AnalyticsConfig(BaseModel):
    """Complete analytics configuration."""
    version: str = Field(description="Config schema version")

    intensity_z_scores: IntensityConfig
    calibration: CalibrationMetadata
    alert_thresholds: AlertThresholds = Field(default_factory=AlertThresholds)
    engagement: EngagementConfig = Field(default_factory=EngagementConfig)
    ema: EMAConfig = Field(default_factory=EMAConfig)
    trend: TrendConfig = Field(default_factory=TrendConfig)
    momentum: MomentumConfig = Field(default_factory=MomentumConfig)
    velocity: VelocityConfig = Field(default_factory=VelocityConfig)
    pipeline: PipelineConfig = Field(default_factory=PipelineConfig)
    commentary: CommentaryConfig = Field(default_factory=CommentaryConfig)


# =============================================================================
# Config Loading
# =============================================================================

CONFIG_PATH = Path(__file__).parent / "analytics_config.json"


def load_config(config_path: Path | None = None) -> AnalyticsConfig:
    """Load analytics configuration from JSON file.

    Args:
        config_path: Path to config file. Defaults to analytics_config.json
                     in the same directory as this module.

    Returns:
        AnalyticsConfig with all scoring parameters.

    Raises:
        FileNotFoundError: If config file doesn't exist.
        ValueError: If config file is invalid.
    """
    path = config_path or CONFIG_PATH

    if not path.exists():
        raise FileNotFoundError(
            f"Analytics config not found at {path}. "
            f"Run 'python -m kopi_sentiment.analytics.calibrate' to generate it."
        )

    with open(path) as f:
        raw_config: dict[str, Any] = json.load(f)

    return AnalyticsConfig(**raw_config)


def get_intensity_z(intensity: str, config: AnalyticsConfig | None = None) -> float:
    """Get z-score for an intensity level.

    Args:
        intensity: One of 'mild', 'moderate', 'strong'
        config: Optional config. Loads from file if not provided.

    Returns:
        Z-score for the intensity level.
    """
    if config is None:
        config = load_config()

    mapping = {
        "mild": config.intensity_z_scores.mild,
        "moderate": config.intensity_z_scores.moderate,
        "strong": config.intensity_z_scores.strong,
    }

    if intensity not in mapping:
        raise ValueError(f"Unknown intensity: {intensity}. Expected mild/moderate/strong.")

    return mapping[intensity]


def get_alert_severity(z_score: float, config: AnalyticsConfig | None = None) -> str:
    """Determine alert severity from z-score.

    Args:
        z_score: The z-score to evaluate.
        config: Optional config. Loads from file if not provided.

    Returns:
        Alert severity: 'none', 'notable', 'warning', or 'alert'
    """
    if config is None:
        config = load_config()

    abs_z = abs(z_score)
    thresholds = config.alert_thresholds

    if abs_z >= thresholds.alert:
        return "alert"
    elif abs_z >= thresholds.warning:
        return "warning"
    elif abs_z >= thresholds.notable:
        return "notable"
    else:
        return "none"
