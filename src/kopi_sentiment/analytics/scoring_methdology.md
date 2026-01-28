# Analytics Scoring Methodology

This document explains the statistical methodology behind the sentiment scoring system. All values are empirically derived from actual data, not arbitrarily chosen.

## Overview

The analytics module uses **z-score normalization** to create comparable, statistically meaningful sentiment scores. This approach:

1. Weights quotes by community engagement (upvotes)
2. Accounts for intensity levels (mild/moderate/strong)
3. Enables anomaly detection with clear statistical thresholds
4. Produces scores that are interpretable and defensible

---

## Quote Scoring Formula

Each quote contributes to the daily sentiment score using:

```
quote_score = engagement_z + intensity_z
```

Where both components are in z-score units, making them additive.

---

## Component 1: Engagement Z-Score

Measures how much the community validated this quote relative to typical engagement.

```
engagement_z = (comment_score - mean_score) / std_score
```

**Example** (using historical mean=28.7, std=45.2):
| Comment Score | Engagement Z | Interpretation |
|---------------|--------------|----------------|
| 100 upvotes | +1.58 | Well above average engagement |
| 30 upvotes | +0.03 | Typical engagement |
| 5 upvotes | -0.52 | Below average engagement |

**Bayesian Floor**: For quotes with 0 upvotes, we apply a floor of z = -2.0 to avoid extreme negative values dominating the score.

---

## Component 2: Intensity Z-Score

Maps the LLM-assigned intensity (mild/moderate/strong) to a z-score based on the **empirical distribution** in our data.

### Derivation (from 2,000 quotes, Jan 15-24, 2026)

We analyzed the distribution of intensity levels across all historical quotes:

| Intensity | Count | % of Total | Cumulative % | Midpoint Percentile |
|-----------|-------|------------|--------------|---------------------|
| mild | 202 | 10.1% | 10.1% | 5.1% |
| moderate | 839 | 41.9% | 52.0% | 31.1% |
| strong | 959 | 47.9% | 100% | 76.0% |

Converting midpoint percentiles to z-scores (inverse normal CDF):

```python
INTENSITY_Z_SCORES = {
    "mild": -1.64,     # 5.1th percentile
    "moderate": -0.49, # 31.1th percentile
    "strong": +0.71    # 76.0th percentile
}
```

### Validation: Engagement Correlates with Intensity

We verified that the community's upvoting behavior validates the LLM's intensity classification:

| Intensity | Mean Engagement | Observation |
|-----------|-----------------|-------------|
| mild | 20.8 upvotes | Lowest engagement |
| moderate | 23.8 upvotes | Middle engagement |
| strong | 39.1 upvotes | ~2x mild engagement |

This confirms that "strong" quotes genuinely resonate more with the community.

### Why Not Use Simple Weights (1, 2, 3)?

Arbitrary integer weights like `{mild: 1, moderate: 2, strong: 3}` have problems:

1. **Not grounded in data**: Why is strong 3x mild? Why not 2x or 5x?
2. **Not comparable**: These aren't in the same units as engagement scores
3. **Assumes equal spacing**: The gap mild→moderate equals moderate→strong (unlikely)

Our z-score approach solves all three:
1. Derived from actual distribution of 2,000 quotes
2. Same units as engagement z-scores (additive)
3. Reflects actual asymmetric distribution (10% / 42% / 48%)

---

## Combined Score Example

| Quote | Comment Score | Intensity | Engagement Z | Intensity Z | **Total** |
|-------|---------------|-----------|--------------|-------------|-----------|
| A | 100 upvotes | moderate | +1.58 | -0.49 | **+1.09** |
| B | 10 upvotes | strong | -0.41 | +0.71 | **+0.30** |
| C | 150 upvotes | mild | +2.68 | -1.64 | **+1.04** |

**Interpretation**:
- Quote A (high engagement, moderate intensity) scores highest
- Quote C (very high engagement, mild intensity) nearly matches Quote A
- Quote B (low engagement, strong intensity) scores lowest despite strong intensity

This reflects the principle: **community validation matters as much as expressed intensity**.

---

## Anomaly Detection Thresholds

For trend velocity alerts, we use standard z-score thresholds:

| Z-Score Range | Alert Level | Statistical Meaning | Probability |
|---------------|-------------|---------------------|-------------|
| \|z\| < 1.0 | None | Normal variation | 68% of days |
| 1.0 ≤ \|z\| < 1.5 | Notable | Somewhat unusual | 23% of days |
| 1.5 ≤ \|z\| < 2.0 | Warning | Unusual | 7% of days |
| \|z\| ≥ 2.0 | Alert | Statistically significant | <5% of days |

The \|z\| ≥ 2.0 threshold corresponds to p < 0.05, the standard threshold for statistical significance.

---

## Updating the Weights

The intensity z-scores should be recalculated periodically as more data accumulates:

```python
# Recalculation script: src/kopi_sentiment/analytics/calibrate.py
python -m kopi_sentiment.analytics.calibrate
```

Recommended: Recalibrate monthly or after collecting 10,000+ new quotes.

---

## References

1. **Z-score normalization**: Standard statistical technique for comparing values across different scales
2. **Inverse normal CDF**: Used to convert percentiles to z-scores (scipy.stats.norm.ppf)
3. **Wilson score interval**: Considered but not used (requires upvote/downvote ratio; Reddit only exposes net score)

---

## Changelog

| Date | Change | Reason |
|------|--------|--------|
| 2026-01-24 | Initial calibration | Based on 2,000 quotes from Jan 15-24, 2026 |