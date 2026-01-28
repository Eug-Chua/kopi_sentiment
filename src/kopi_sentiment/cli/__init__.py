"""CLI for Kopi Sentiment analysis pipelines."""

import argparse
import logging
import sys
from datetime import date

from kopi_sentiment.config.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def run_daily(args):
    """Run the daily sentiment analysis pipeline."""
    from kopi_sentiment.pipeline.daily import DailyPipeline

    date_id = args.date or date.today().isoformat()

    logger.info(f"Starting daily pipeline for {date_id}")

    pipeline = DailyPipeline(
        subreddits=settings.reddit_subreddit,
        posts_per_subreddit=args.posts or 10,
        llm_provider=args.provider or settings.llm_provider,
        storage_path=args.output or settings.data_path_daily,
    )

    report = pipeline.run(date_id)
    logger.info(f"Daily analysis complete. Report saved for {report.date_id}")

    # Auto-regenerate analytics unless --no-analytics flag is set
    if not args.no_analytics:
        logger.info("Regenerating analytics report...")
        _regenerate_analytics(args.output or settings.data_path_daily)

    return 0


def _regenerate_analytics(daily_data_dir: str | None = None):
    """Helper to regenerate analytics after daily pipeline."""
    import json
    from pathlib import Path

    from kopi_sentiment.analytics.calculator import AnalyticsCalculator

    input_dir = daily_data_dir or "web/public/data/daily"
    output_file = "web/public/data/analytics.json"

    try:
        calculator = AnalyticsCalculator()
        report = calculator.generate_report(input_dir)

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(report.model_dump(mode="json"), f, indent=2, default=str)

        logger.info(
            f"Analytics updated: {report.data_range_start} to {report.data_range_end} "
            f"({report.days_analyzed} days)"
        )
    except Exception as e:
        logger.warning(f"Could not regenerate analytics: {e}")


def run_weekly(args):
    """Run the weekly sentiment analysis pipeline."""
    from kopi_sentiment.pipeline.weekly import WeeklyPipeline

    week_id = args.week

    logger.info(f"Starting weekly pipeline for {week_id or 'current week'}")

    pipeline = WeeklyPipeline(
        subreddits=settings.reddit_subreddit,
        posts_per_subreddit=args.posts or 25,
        llm_provider=args.provider or settings.llm_provider,
        storage_path=args.output or settings.data_path_weekly,
    )

    report = pipeline.run(week_id)
    logger.info(f"Weekly analysis complete. Report saved for {report.week_id}")
    return 0


def run_analytics(args):
    """Generate analytics report from daily data."""
    import json
    from datetime import datetime, timedelta
    from pathlib import Path

    from kopi_sentiment.analytics.calculator import AnalyticsCalculator

    input_dir = args.input or "web/public/data/daily"

    # Determine output file based on --weekly flag
    if args.weekly:
        output_file = args.output or "web/public/data/analytics_weekly.json"
    else:
        output_file = args.output or "web/public/data/analytics.json"

    # Calculate date range for weekly analytics
    start_date = None
    end_date = None

    if args.weekly:
        if args.week:
            # Parse week ID (e.g., "2026-W04") using ISO week format
            year, week_num = args.week.split("-W")
            # Use ISO week format: %G=ISO year, %V=ISO week number, %u=weekday (1=Monday)
            week_start = datetime.strptime(f"{year}-W{week_num}-1", "%G-W%V-%u").date()
            start_date = week_start
            end_date = week_start + timedelta(days=6)
        else:
            # Default to last complete week
            today = date.today()
            # Go back to last Sunday
            days_since_sunday = (today.weekday() + 1) % 7
            last_sunday = today - timedelta(days=days_since_sunday)
            end_date = last_sunday
            start_date = last_sunday - timedelta(days=6)

        logger.info(f"Generating weekly analytics from {input_dir}")
        logger.info(f"Date range: {start_date} to {end_date}")
    else:
        logger.info(f"Generating analytics from {input_dir}")

    calculator = AnalyticsCalculator()
    report = calculator.generate_report(input_dir, start_date=start_date, end_date=end_date)

    # Save report
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(report.model_dump(mode="json"), f, indent=2, default=str)

    logger.info(
        f"Analytics report saved to {output_file} "
        f"(range: {report.data_range_start} to {report.data_range_end}, "
        f"{report.days_analyzed} days)"
    )
    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Kopi Sentiment - Reddit sentiment analysis for Singapore",
        prog="kopi_sentiment",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Daily command
    daily_parser = subparsers.add_parser("daily", help="Run daily analysis (last 24 hours)")
    daily_parser.add_argument(
        "--date",
        type=str,
        help="Date to analyze (YYYY-MM-DD), defaults to today",
    )
    daily_parser.add_argument(
        "--posts",
        type=int,
        default=10,
        help="Number of posts per subreddit (default: 10)",
    )
    daily_parser.add_argument(
        "--provider",
        type=str,
        choices=["openai", "claude", "hybrid"],
        help="LLM provider to use (hybrid = OpenAI extraction + Claude synthesis)",
    )
    daily_parser.add_argument(
        "--output",
        type=str,
        help="Output directory for reports",
    )
    daily_parser.add_argument(
        "--no-analytics",
        action="store_true",
        help="Skip automatic analytics regeneration",
    )
    daily_parser.set_defaults(func=run_daily)

    # Weekly command
    weekly_parser = subparsers.add_parser("weekly", help="Run weekly analysis")
    weekly_parser.add_argument(
        "--week",
        type=str,
        help="Week ID to analyze (e.g., 2025-W03), defaults to current week",
    )
    weekly_parser.add_argument(
        "--posts",
        type=int,
        default=25,
        help="Number of posts per subreddit (default: 25)",
    )
    weekly_parser.add_argument(
        "--provider",
        type=str,
        choices=["openai", "claude", "hybrid"],
        help="LLM provider to use (hybrid = OpenAI extraction + Claude synthesis)",
    )
    weekly_parser.add_argument(
        "--output",
        type=str,
        help="Output directory for reports",
    )
    weekly_parser.set_defaults(func=run_weekly)

    # Analytics command
    analytics_parser = subparsers.add_parser(
        "analytics", help="Generate trend analytics from daily reports"
    )
    analytics_parser.add_argument(
        "--input",
        type=str,
        help="Input directory with daily JSON reports (default: web/public/data/daily)",
    )
    analytics_parser.add_argument(
        "--output",
        type=str,
        help="Output file path (default: web/public/data/analytics.json)",
    )
    analytics_parser.add_argument(
        "--weekly",
        action="store_true",
        help="Generate weekly analytics (7-day window) instead of rolling daily",
    )
    analytics_parser.add_argument(
        "--week",
        type=str,
        help="Week ID to analyze (e.g., 2026-W04). Only used with --weekly flag.",
    )
    analytics_parser.set_defaults(func=run_analytics)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        return args.func(args)
    except Exception as e:
        logger.error(f"Error running {args.command}: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())