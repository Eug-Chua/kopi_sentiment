"""Velocity calculator with anomaly detection.

Calculates first and second derivatives of sentiment metrics
and detects anomalies using z-score thresholds.
"""

import uuid
from datetime import date
from math import erf, sqrt
from statistics import mean, stdev

from .config import AnalyticsConfig, get_alert_severity
from .models import (
    AlertSeverity,
    SentimentTimeSeries,
    TrendDirection,
    TrendVelocityAlert,
    VelocityMetric,
    VelocityReport,
)


class VelocityCalculator:
    """Calculates velocity metrics and detects anomalies."""

    METRIC_CONFIGS = [
        ("composite_score", None),
        ("fears_zscore_sum", "fears"),
        ("frustrations_zscore_sum", "frustrations"),
        ("optimism_zscore_sum", "optimism"),
    ]

    def __init__(self, config: AnalyticsConfig):
        self.config = config

    def calculate(self, timeseries: SentimentTimeSeries) -> VelocityReport:
        """Calculate velocity metrics and detect anomalies.

        Args:
            timeseries: Sentiment time series with data points.

        Returns:
            VelocityReport with metrics and alerts.
        """
        data = timeseries.data_points
        report_date = data[-1].date

        metrics = []
        alerts = []

        for attr, category in self.METRIC_CONFIGS:
            values = [getattr(dp, attr) for dp in data]
            metric, alert = self._calculate_metric(
                attr, values, category, report_date
            )
            metrics.append(metric)
            if alert:
                alerts.append(alert)

        alerts = self._sort_alerts(alerts)
        alert_count = sum(1 for a in alerts if a.severity == AlertSeverity.ALERT)
        warning_count = sum(1 for a in alerts if a.severity == AlertSeverity.WARNING)

        return VelocityReport(
            report_date=report_date,
            lookback_days=min(self.config.velocity.lookback_days, len(data)),
            metrics=metrics,
            alerts=alerts,
            total_alerts=len(alerts),
            alert_count=alert_count,
            warning_count=warning_count,
        )

    def _calculate_metric(
        self,
        metric_name: str,
        values: list[float],
        category: str | None,
        report_date: date,
    ) -> tuple[VelocityMetric, TrendVelocityAlert | None]:
        """Calculate velocity for a single metric."""
        if len(values) < 2:
            return self._empty_metric(metric_name, values), None

        velocities = [values[i] - values[i - 1] for i in range(1, len(values))]
        current_velocity = velocities[-1]

        hist_velocities = velocities[:-1] if len(velocities) > 1 else velocities
        hist_mean = mean(hist_velocities)
        hist_std = stdev(hist_velocities) if len(hist_velocities) > 1 else 1

        velocity_zscore = (
            (current_velocity - hist_mean) / hist_std if hist_std > 0 else 0
        )
        acceleration = velocities[-1] - velocities[-2] if len(velocities) >= 2 else 0
        alert_level = AlertSeverity(get_alert_severity(velocity_zscore, self.config))

        metric = VelocityMetric(
            metric_name=metric_name,
            current_value=values[-1],
            velocity=current_velocity,
            velocity_zscore=velocity_zscore,
            acceleration=acceleration,
            historical_mean=hist_mean,
            historical_std=hist_std,
            alert_level=alert_level,
        )

        alert = None
        if alert_level in (AlertSeverity.WARNING, AlertSeverity.ALERT):
            alert = self._create_alert(
                metric_name, category, current_velocity, hist_mean,
                velocity_zscore, report_date
            )

        return metric, alert

    def _empty_metric(
        self, metric_name: str, values: list[float]
    ) -> VelocityMetric:
        """Create empty metric when insufficient data."""
        return VelocityMetric(
            metric_name=metric_name,
            current_value=values[-1] if values else 0,
            velocity=0,
            velocity_zscore=0,
            acceleration=0,
            historical_mean=0,
            historical_std=0,
            alert_level=AlertSeverity.NONE,
        )

    def _create_alert(
        self,
        metric_name: str,
        category: str | None,
        current_velocity: float,
        expected: float,
        z_score: float,
        report_date: date,
    ) -> TrendVelocityAlert:
        """Create a velocity alert."""
        direction = TrendDirection.RISING if z_score > 0 else TrendDirection.FALLING
        percentile = self._z_to_percentile(z_score)
        severity = AlertSeverity(get_alert_severity(z_score, self.config))

        return TrendVelocityAlert(
            alert_id=str(uuid.uuid4())[:8],
            triggered_at=report_date,
            severity=severity,
            metric=metric_name,
            category=category,
            current_value=current_velocity,
            expected_value=expected,
            z_score=z_score,
            percentile=percentile,
            direction=direction,
            description=self._alert_description(
                metric_name, z_score, direction, category
            ),
        )

    def _alert_description(
        self,
        metric: str,
        z_score: float,
        direction: TrendDirection,
        category: str | None,
    ) -> str:
        """Generate human-readable alert description."""
        significant_z = self.config.alert_thresholds.significant_z
        magnitude = "significantly" if abs(z_score) >= significant_z else "notably"
        dir_word = "increased" if direction == TrendDirection.RISING else "decreased"

        if category:
            return f"{category.title()} has {magnitude} {dir_word} (z={z_score:.2f})"
        return f"Overall sentiment has {magnitude} {dir_word} (z={z_score:.2f})"

    def _z_to_percentile(self, z: float) -> float:
        """Convert z-score to percentile using normal CDF approximation."""
        return 50 * (1 + erf(z / sqrt(2)))

    def _sort_alerts(
        self, alerts: list[TrendVelocityAlert]
    ) -> list[TrendVelocityAlert]:
        """Sort alerts by severity (most severe first)."""
        severity_order = {
            AlertSeverity.ALERT: 0,
            AlertSeverity.WARNING: 1,
            AlertSeverity.NOTABLE: 2,
            AlertSeverity.NONE: 3,
        }
        return sorted(alerts, key=lambda a: severity_order[a.severity])
