"""Calibration script for analytics intensity z-scores.

This script analyzes the distribution of intensity labels (mild/moderate/strong)
across all daily reports and computes appropriate z-scores for each level.

Usage:
    python -m kopi_sentiment.analytics.calibrate
    python -m kopi_sentiment.analytics.calibrate --data-dir data/daily
    python -m kopi_sentiment.analytics.calibrate --dry-run

The calibration updates ONLY the empirically-derived values:
- intensity_z_scores (mild, moderate, strong)
- calibration metadata (date, data range, distribution)

All other config values (thresholds, EMA params, etc.) are left unchanged.
"""

import argparse
import json
import logging
from datetime import date
from pathlib import Path
from scipy import stats

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent / "analytics_config.json"


def load_daily_reports(data_dir: Path) -> list[dict]:
    """Load all daily JSON reports."""
    reports = []
    for file_path in sorted(data_dir.glob("*.json")):
        with open(file_path) as f:
            reports.append(json.load(f))
    return reports


def count_intensity_distribution(reports: list[dict]) -> dict[str, int]:
    """Count intensity labels across all quotes."""
    counts = {"mild": 0, "moderate": 0, "strong": 0}

    for report in reports:
        for category in ["fears", "frustrations", "optimism"]:
            for quote in report.get("all_quotes", {}).get(category, []):
                intensity = quote.get("intensity", "moderate").lower()
                if intensity in counts:
                    counts[intensity] += 1

    return counts


def compute_z_scores(counts: dict[str, int]) -> dict[str, float]:
    """Convert intensity distribution to z-scores.

    We model intensity as an ordinal variable and assign z-scores based on
    the cumulative percentile position of each level.

    - mild: z-score at the midpoint of the mild percentile range
    - moderate: z-score at the midpoint of the moderate percentile range
    - strong: z-score at the midpoint of the strong percentile range
    """
    total = sum(counts.values())
    if total == 0:
        raise ValueError("No quotes found in data")

    # Calculate percentages
    pct_mild = counts["mild"] / total
    pct_moderate = counts["moderate"] / total
    pct_strong = counts["strong"] / total

    # Cumulative percentiles (midpoints)
    # mild: 0 to pct_mild, midpoint = pct_mild / 2
    # moderate: pct_mild to pct_mild + pct_moderate, midpoint = pct_mild + pct_moderate/2
    # strong: pct_mild + pct_moderate to 1, midpoint = pct_mild + pct_moderate + pct_strong/2

    mid_mild = pct_mild / 2
    mid_moderate = pct_mild + pct_moderate / 2
    mid_strong = pct_mild + pct_moderate + pct_strong / 2

    # Convert percentiles to z-scores using inverse normal CDF
    z_mild = stats.norm.ppf(mid_mild) if mid_mild > 0 else -2.5
    z_moderate = stats.norm.ppf(mid_moderate) if 0 < mid_moderate < 1 else 0
    z_strong = stats.norm.ppf(mid_strong) if mid_strong < 1 else 2.5

    return {
        "mild": round(z_mild, 2),
        "moderate": round(z_moderate, 2),
        "strong": round(z_strong, 2),
    }


def update_config(
    config_path: Path,
    z_scores: dict[str, float],
    counts: dict[str, int],
    data_range: tuple[str, str],
) -> dict:
    """Update config file with new calibration values."""
    with open(config_path) as f:
        config = json.load(f)

    total = sum(counts.values())

    # Update intensity z-scores
    config["intensity_z_scores"]["mild"] = z_scores["mild"]
    config["intensity_z_scores"]["moderate"] = z_scores["moderate"]
    config["intensity_z_scores"]["strong"] = z_scores["strong"]

    # Update calibration metadata
    config["calibration"]["calibrated_at"] = date.today().isoformat()
    config["calibration"]["data_range_start"] = data_range[0]
    config["calibration"]["data_range_end"] = data_range[1]
    config["calibration"]["total_quotes_analyzed"] = total
    config["calibration"]["distribution"] = {
        "mild": round(counts["mild"] / total * 100, 1),
        "moderate": round(counts["moderate"] / total * 100, 1),
        "strong": round(counts["strong"] / total * 100, 1),
    }

    return config


def main():
    parser = argparse.ArgumentParser(
        description="Calibrate analytics intensity z-scores from data distribution"
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data/daily"),
        help="Directory containing daily JSON reports (default: data/daily)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=CONFIG_PATH,
        help="Path to analytics config file",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print results without updating config file",
    )
    args = parser.parse_args()

    # Load data
    logger.info(f"Loading daily reports from {args.data_dir}...")
    reports = load_daily_reports(args.data_dir)

    if not reports:
        logger.error(f"No reports found in {args.data_dir}")
        return 1

    logger.info(f"Loaded {len(reports)} daily reports")

    # Get date range
    dates = [r.get("date_id", "") for r in reports if r.get("date_id")]
    data_range = (min(dates), max(dates)) if dates else ("unknown", "unknown")
    logger.info(f"Data range: {data_range[0]} to {data_range[1]}")

    # Count distribution
    counts = count_intensity_distribution(reports)
    total = sum(counts.values())
    logger.info(f"\nIntensity distribution ({total:,} total quotes):")
    for level, count in counts.items():
        pct = count / total * 100 if total > 0 else 0
        logger.info(f"  {level:10s}: {count:5d} ({pct:5.1f}%)")

    # Compute z-scores
    z_scores = compute_z_scores(counts)
    logger.info(f"\nComputed z-scores:")
    for level, z in z_scores.items():
        logger.info(f"  {level:10s}: {z:+.2f}")

    if args.dry_run:
        logger.info("\n[DRY RUN] Config file not updated")
        return 0

    # Update config
    updated_config = update_config(args.config, z_scores, counts, data_range)

    with open(args.config, "w") as f:
        json.dump(updated_config, f, indent=2)

    logger.info(f"\nConfig updated: {args.config}")
    return 0


if __name__ == "__main__":
    exit(main())
