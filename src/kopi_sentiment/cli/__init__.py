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
    return 0


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