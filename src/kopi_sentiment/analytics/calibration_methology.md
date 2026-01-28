# Analytics Calibration

This document explains the calibration process for the analytics scoring system.

## What Gets Calibrated

Only **empirically-derived values** are calibrated from data:

| Config Field | Calibrated? | Source |
|--------------|-------------|--------|
| `intensity_z_scores` | ✅ Yes | Data distribution |
| `calibration` metadata | ✅ Yes | Auto-updated |
| `alert_thresholds` | ❌ No | Statistical convention |
| `ema`, `forecast`, `trend` | ❌ No | Hyperparameters |
| `momentum`, `velocity` | ❌ No | Design choices |
| `pipeline`, `commentary` | ❌ No | App settings |

## Intensity Z-Scores

### What They Are

The LLM labels each quote with an intensity level: **mild**, **moderate**, or **strong**.

To combine intensity with engagement (upvotes) into a single score, we convert intensity to z-score units:

```
quote_score = engagement_z + intensity_z
```

### How They're Calculated

1. Count the distribution of intensity labels across all quotes
2. Treat intensity as ordinal (mild < moderate < strong)
3. Assign z-scores based on cumulative percentile midpoints

**Example** (from Jan 15-24, 2026 data):

| Intensity | Count | Percentage | Cumulative Midpoint | Z-Score |
|-----------|-------|------------|---------------------|---------|
| mild | 202 | 10.1% | 5.05% | -1.64 |
| moderate | 838 | 41.9% | 31.0% | -0.49 |
| strong | 960 | 48.0% | 76.0% | +0.71 |

This means:
- A **mild** quote is penalized (z = -1.64)
- A **moderate** quote is slightly below average (z = -0.49)
- A **strong** quote gets a boost (z = +0.71)

## Running Calibration

```bash
# Calibrate from default data directory
python -m kopi_sentiment.analytics.calibrate

# Calibrate from specific directory
python -m kopi_sentiment.analytics.calibrate --data-dir data/daily

# Preview without updating config
python -m kopi_sentiment.analytics.calibrate --dry-run
```

## When to Recalibrate

Recalibrate when:
- You have significantly more data (2x or more)
- The LLM prompt for intensity labeling changes
- You notice the distribution has shifted substantially

**Don't recalibrate** just because you added a few days of data. The z-scores are fairly stable once you have ~1000+ quotes.

## What NOT to Change

These values are **not data-derived** and should be tuned manually:

### Alert Thresholds
```json
"alert_thresholds": {
  "notable": 1.0,   // |z| >= 1.0 → "notable" (~32% of data)
  "warning": 1.5,   // |z| >= 1.5 → "warning" (~13% of data)
  "alert": 2.0      // |z| >= 2.0 → "alert" (~5% of data, p < 0.05)
}
```
These are standard statistical thresholds. Adjust only if you want more/fewer alerts.

### EMA Parameters
```json
"ema": {
  "span": 7,        // 7-day smoothing window
  "min_periods": 3  // Need 3 days before EMA starts
}
```
Standard time series smoothing. Change if you want faster/slower response to trends.

### Forecast Parameters
```json
"forecast": {
  "train_ratio": 0.7,           // 70% train, 30% test
  "forecast_horizon_days": 3,   // Predict 3 days ahead
  "z_critical": 1.96            // 95% confidence interval (DON'T CHANGE)
}
```
The `z_critical` value is a mathematical constant for 95% CI.

### Trend Thresholds
```json
"trend": {
  "slope_stable_threshold": 0.5,  // < 0.5 points/day = "stable"
  "roc_weak_threshold": 10,       // < 10% change = "weak"
  "roc_strong_threshold": 25      // > 25% change = "strong"
}
```
Business decisions about what counts as "significant movement."

## Config File Location

```
src/kopi_sentiment/analytics/analytics_config.json
```

The calibration script only modifies `intensity_z_scores` and `calibration` sections. All other values are preserved.
