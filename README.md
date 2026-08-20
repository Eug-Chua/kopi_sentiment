# Kopi Sentiment
**Understanding the heartbeat of Singapore, one thread at a time.**

## Why This Matters

Singapore's fortunes are tied to global forces beyond its control. As Singapore's leaders have noted:
- *The rules-based international order is being tested and multilateral cooperation is fraying.*
- *We are living in turbulent times... the global order changes before our very eyes.*

As a small nation navigating a shifting world order, what was normal is no longer normal. The rules Singapore rode to transform from third world to first are being rewritten. 

This affects Singaporeans' daily lives in profound ways.

**Kopi Sentiment** listens to what people are actually saying—and what they truly mean.


## What It Does

This tool mines Singapore subreddit discussions where people speak candidly about what's going on in Singapore, using the **FFO Framework** to surface authentic voices:

- **Fears** - What worries or concerns do they have?
- **Frustrations** - What obstacles or annoyances do they face?
- **Optimism** - What are they hopeful or positive about?

The FFO framework captures both **negative** (fears, frustrations) and **positive** (optimism) dimensions of how Singaporeans experience this moment in history.

**Output**: A simple traffic light sentiment score (Green / Amber / Red) for each FFO dimension, backed by actual quotes from real conversations.

## The Goal

To hear what is being said, and understand what is truly meant.

Not to prescribe solutions, but to listen deeply to the Singaporean psyche in an age of economic uncertainty and geopolitical tension.

## Quick Start

```bash
# Install dependencies
pip install -e .

# Run daily analysis
python -m kopi_sentiment daily

# Run weekly analysis
python -m kopi_sentiment weekly

# Generate analytics report
python -c "
from kopi_sentiment.analytics.calculator import AnalyticsCalculator
calculator = AnalyticsCalculator()
report = calculator.generate_report()
print(report.headline)
"
```

## Browser Capture (No Reddit API)

If Reddit is accessible in ordinary Chrome but blocks automated login/API
requests, use the included user-triggered browser capture extension. It reads
only the active Reddit listing and sends extracted public post data to a
loopback receiver; it does not read or export browser cookies.

Install it once:

1. Open `chrome://extensions` and enable **Developer mode**.
2. Click **Load unpacked**.
3. Select the repository's `chrome_extension` directory.
4. Pin **Kopi Sentiment Capture** to the Chrome toolbar.

For a daily run:

```bash
uv run python -m kopi_sentiment capture
```

Open each subreddit link shown in the extension, wait for its top listing to
load, and click **Capture this subreddit**. With comment capture enabled, the
extension opens each selected thread in an inactive tab, captures up to 25
rendered top comments, waits five seconds between threads, and closes each tab.
Keep Chrome open until the toolbar badge finishes counting.

Once all configured subreddits are captured, analyze the saved raw data:

```bash
uv run python -m kopi_sentiment daily --date YYYY-MM-DD --from-raw
```

Any incomplete thread captures are recorded under `collection_warnings` in the
raw file. Use `capture --overwrite` when replacing an earlier capture for the
same date.

## Analytics Module

The analytics module provides data science capabilities for trend analysis:

### Features

| Feature | Description |
|---------|-------------|
| **Sentiment Index** | Composite score tracking overall sentiment over time with EMA smoothing |
| **Category Momentum** | Rate of change analysis for each FFO category (1d, 3d, 7d) |
| **Velocity Alerts** | Z-score based anomaly detection (alerts at \|z\| >= 2.0) |
| **Forecasting** | Linear regression with train/test split and confidence intervals |

### Methodology

All scoring uses **z-score normalization** for statistical rigor:

```
quote_score = engagement_z + intensity_z
```

Where:
- `engagement_z` = normalized comment upvote score
- `intensity_z` = empirically-derived from data distribution (see [METHODOLOGY.md](src/kopi_sentiment/analytics/METHODOLOGY.md))

**Why z-scores?**
- Self-normalizing: adapts to changing engagement patterns
- Statistically interpretable: z=2.0 means "top 2.5%"
- Additive: engagement and intensity in same units

### Configuration

All parameters are configurable in `analytics_config.json`:
- Intensity z-scores (derived from 2,000 quotes)
- Alert thresholds (default: 2.0 for statistical significance)
- EMA span (default: 7 days)
- Forecast train/test ratio (default: 70/30)

### Tests

```bash
# Run analytics tests
pytest tests/test_analytics.py -v
```


## References

- [PM Lawrence Wong on the global order](https://www.youtube.com/watch?v=40AjeJwoJJ0&t)
- [Minister Ng Eng Hen on turbulent times](https://www.mindef.gov.sg/news-and-events/latest-releases/04mar25_speech3/)
