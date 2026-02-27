"""JSON file storage for weekly and daily sentiment reports."""

import json
import logging
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from kopi_sentiment.config.settings import settings
from kopi_sentiment.analyzer.models import WeeklyReport, DailyReport
from kopi_sentiment.scraper.reddit import RedditPost, Comment

logger = logging.getLogger(__name__)


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime objects."""

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, date):
            return obj.isoformat()
        return super().default(obj)


class JSONStorage:
    """Manages JSON file storage for weekly reports."""

    def __init__(self, base_path: Path | str | None = None):
        """Initialize storage with a base path.

        Args:
            base_path: Directory for storing JSON files. Defaults to 'data/weekly'.
        """
        if base_path is None:
            base_path = Path(settings.data_path_weekly)
        elif isinstance(base_path, str):
            base_path = Path(base_path)

        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"JSONStorage initialized at {self.base_path.absolute()}")

    def save_weekly_report(self, report: WeeklyReport) -> Path:
        """Save a weekly report to JSON.

        Args:
            report: WeeklyReport to save

        Returns:
            Path to the saved file
        """
        file_path = self.base_path / f"{report.week_id}.json"

        # Convert to dict with proper serialization
        data = report.model_dump(mode="json")

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, cls=DateTimeEncoder)

        logger.info(f"Saved weekly report to {file_path}")
        return file_path

    def load_weekly_report(self, week_id: str) -> WeeklyReport:
        """Load a weekly report from JSON.

        Args:
            week_id: Week identifier (e.g., '2025-W02')

        Returns:
            WeeklyReport object

        Raises:
            FileNotFoundError: If the report doesn't exist
        """
        file_path = self.base_path / f"{week_id}.json"

        if not file_path.exists():
            raise FileNotFoundError(f"No report found for week {week_id}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return WeeklyReport.model_validate(data)

    def list_all_weeks(self) -> list[str]:
        """List all available week IDs, sorted newest first.

        Returns:
            List of week IDs (e.g., ['2025-W03', '2025-W02', '2025-W01'])
        """
        weeks = sorted(
            [f.stem for f in self.base_path.glob("*.json")],
            reverse=True,
        )
        return weeks

    def get_latest_week(self) -> str | None:
        """Get the most recent week ID.

        Returns:
            Latest week ID or None if no reports exist
        """
        weeks = self.list_all_weeks()
        return weeks[0] if weeks else None

    def report_exists(self, week_id: str) -> bool:
        """Check if a report exists for the given week.

        Args:
            week_id: Week identifier (e.g., '2025-W02')

        Returns:
            True if report exists
        """
        file_path = self.base_path / f"{week_id}.json"
        return file_path.exists()

    def delete_report(self, week_id: str) -> bool:
        """Delete a weekly report.

        Args:
            week_id: Week identifier to delete

        Returns:
            True if deleted, False if not found
        """
        file_path = self.base_path / f"{week_id}.json"

        if file_path.exists():
            file_path.unlink()
            logger.info(f"Deleted report for {week_id}")
            return True

        return False


class DailyJSONStorage:
    """Manages JSON file storage for daily reports."""

    def __init__(self, base_path: Path | str | None = None):
        """Initialize storage with a base path.

        Args:
            base_path: Directory for storing JSON files. Defaults to 'data/daily'.
        """
        if base_path is None:
            base_path = Path(settings.data_path_daily)
        elif isinstance(base_path, str):
            base_path = Path(base_path)

        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"DailyJSONStorage initialized at {self.base_path.absolute()}")

    def save_daily_report(self, report: DailyReport) -> Path:
        """Save a daily report to JSON.

        Args:
            report: DailyReport to save

        Returns:
            Path to the saved file
        """
        file_path = self.base_path / f"{report.date_id}.json"

        # Convert to dict with proper serialization
        data = report.model_dump(mode="json")

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, cls=DateTimeEncoder)

        logger.info(f"Saved daily report to {file_path}")
        return file_path

    def load_daily_report(self, date_id: str) -> DailyReport:
        """Load a daily report from JSON.

        Args:
            date_id: Date identifier (e.g., '2025-01-15')

        Returns:
            DailyReport object

        Raises:
            FileNotFoundError: If the report doesn't exist
        """
        file_path = self.base_path / f"{date_id}.json"

        if not file_path.exists():
            raise FileNotFoundError(f"No report found for date {date_id}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return DailyReport.model_validate(data)

    def list_all_dates(self) -> list[str]:
        """List all available date IDs, sorted newest first.

        Returns:
            List of date IDs (e.g., ['2025-01-15', '2025-01-14', '2025-01-13'])
        """
        dates = sorted(
            [f.stem for f in self.base_path.glob("*.json")],
            reverse=True,
        )
        return dates

    def get_latest_date(self) -> str | None:
        """Get the most recent date ID.

        Returns:
            Latest date ID or None if no reports exist
        """
        dates = self.list_all_dates()
        return dates[0] if dates else None

    def report_exists(self, date_id: str) -> bool:
        """Check if a report exists for the given date.

        Args:
            date_id: Date identifier (e.g., '2025-01-15')

        Returns:
            True if report exists
        """
        file_path = self.base_path / f"{date_id}.json"
        return file_path.exists()

    def delete_report(self, date_id: str) -> bool:
        """Delete a daily report.

        Args:
            date_id: Date identifier to delete

        Returns:
            True if deleted, False if not found
        """
        file_path = self.base_path / f"{date_id}.json"

        if file_path.exists():
            file_path.unlink()
            logger.info(f"Deleted daily report for {date_id}")
            return True

        return False

    def cleanup_old_reports(self, keep_days: int = 7) -> int:
        """Delete daily reports older than keep_days.

        Args:
            keep_days: Number of days of reports to keep (default 7)

        Returns:
            Number of reports deleted
        """
        cutoff_date = date.today() - timedelta(days=keep_days)
        deleted_count = 0

        for date_id in self.list_all_dates():
            try:
                report_date = date.fromisoformat(date_id)
                if report_date < cutoff_date:
                    if self.delete_report(date_id):
                        deleted_count += 1
            except ValueError:
                logger.warning(f"Invalid date format in filename: {date_id}")
                continue

        logger.info(f"Cleaned up {deleted_count} old daily reports (keeping {keep_days} days)")
        return deleted_count


class RawDataStorage:
    """Manages JSON file storage for raw scraped Reddit data.

    Stores the full scraped posts and comments before LLM analysis,
    enabling future re-analysis without re-scraping.
    """

    def __init__(self, base_path: Path | str | None = None, data_type: str = "daily"):
        """Initialize storage with a base path.

        Args:
            base_path: Directory for storing JSON files. Defaults to 'data/raw/{data_type}'.
            data_type: Either 'daily' or 'weekly' to organize raw data.
        """
        if base_path is None:
            # Use appropriate data path based on data type
            if data_type == "weekly":
                base_path = Path(settings.data_path_weekly).parent / "raw" / data_type
            else:
                base_path = Path(settings.data_path_daily).parent / "raw" / data_type
        elif isinstance(base_path, str):
            base_path = Path(base_path)

        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"RawDataStorage initialized at {self.base_path.absolute()}")

    def save_raw_scrape(
        self,
        report_id: str,
        posts: list[RedditPost],
        subreddits: list[str],
    ) -> Path:
        """Save raw scraped data to JSON.

        Args:
            report_id: Date ID (YYYY-MM-DD) or week ID (YYYY-Www)
            posts: List of RedditPost objects with all comments
            subreddits: List of subreddit names that were scraped

        Returns:
            Path to the saved file
        """
        file_path = self.base_path / f"{report_id}.json"

        # Build the raw data structure
        data: dict[str, Any] = {
            "schema_version": "raw_scrape_v1",
            "report_id": report_id,
            "scraped_at": datetime.now().isoformat(),
            "subreddits": subreddits,
            "total_posts": len(posts),
            "total_comments": sum(len(p.comments) for p in posts),
            "posts": [
                {
                    "id": post.id,
                    "subreddit": post.subreddit,
                    "title": post.title,
                    "url": post.url,
                    "score": post.score,
                    "num_comments": post.num_comments,
                    "created_at": post.created_at.isoformat() if isinstance(post.created_at, datetime) else post.created_at,
                    "selftext": post.selftext,
                    "comments": [
                        {
                            "text": comment.text,
                            "score": comment.score,
                        }
                        for comment in post.comments
                    ],
                }
                for post in posts
            ],
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(
            f"Saved raw scrape to {file_path} "
            f"({len(posts)} posts, {data['total_comments']} comments)"
        )
        return file_path

    def load_raw_scrape(self, report_id: str) -> dict[str, Any]:
        """Load raw scraped data from JSON.

        Args:
            report_id: Date ID or week ID

        Returns:
            Dict with raw scrape data

        Raises:
            FileNotFoundError: If the raw data doesn't exist
        """
        file_path = self.base_path / f"{report_id}.json"

        if not file_path.exists():
            raise FileNotFoundError(f"No raw data found for {report_id}")

        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_raw_as_posts(self, report_id: str) -> dict[str, list[RedditPost]]:
        """Load raw data and reconstruct RedditPost objects grouped by subreddit.

        Counterpart to save_raw_scrape(): deserializes saved raw data back into
        domain objects for pipeline re-processing without re-scraping.

        Args:
            report_id: Date ID (YYYY-MM-DD) or week ID (YYYY-Www)

        Returns:
            Dict mapping subreddit name to list of RedditPost objects.

        Raises:
            FileNotFoundError: If the raw data doesn't exist.
        """
        data = self.load_raw_scrape(report_id)
        posts_by_subreddit: dict[str, list[RedditPost]] = {}

        for post_data in data.get("posts", []):
            subreddit = post_data.get("subreddit", "")
            comments = [
                Comment(text=c["text"], score=c["score"])
                for c in post_data.get("comments", [])
            ]
            post = RedditPost(
                id=post_data["id"],
                title=post_data["title"],
                url=post_data["url"],
                score=post_data["score"],
                num_comments=post_data["num_comments"],
                created_at=post_data["created_at"],
                subreddit=subreddit,
                selftext=post_data.get("selftext", ""),
                comments=comments,
            )
            if subreddit not in posts_by_subreddit:
                posts_by_subreddit[subreddit] = []
            posts_by_subreddit[subreddit].append(post)

        return posts_by_subreddit

    def raw_exists(self, report_id: str) -> bool:
        """Check if raw data exists for the given report ID."""
        file_path = self.base_path / f"{report_id}.json"
        return file_path.exists()

    def list_all_raw(self) -> list[str]:
        """List all available raw data IDs, sorted newest first."""
        ids = sorted(
            [f.stem for f in self.base_path.glob("*.json")],
            reverse=True,
        )
        return ids

    def delete_raw(self, report_id: str) -> bool:
        """Delete raw data for a report."""
        file_path = self.base_path / f"{report_id}.json"

        if file_path.exists():
            file_path.unlink()
            logger.info(f"Deleted raw data for {report_id}")
            return True

        return False

    def cleanup_old_raw(self, keep_days: int = 30) -> int:
        """Delete raw data older than keep_days.

        Args:
            keep_days: Number of days of raw data to keep (default 30)

        Returns:
            Number of files deleted
        """
        cutoff_date = date.today() - timedelta(days=keep_days)
        deleted_count = 0

        for report_id in self.list_all_raw():
            try:
                # Handle both date format (YYYY-MM-DD) and week format (YYYY-Www)
                if "-W" in report_id:
                    # Week format: use Monday of that week
                    year, week = report_id.split("-W")
                    report_date = date.fromisocalendar(int(year), int(week), 1)
                else:
                    report_date = date.fromisoformat(report_id)

                if report_date < cutoff_date:
                    if self.delete_raw(report_id):
                        deleted_count += 1
            except ValueError:
                logger.warning(f"Invalid format in raw filename: {report_id}")
                continue

        logger.info(f"Cleaned up {deleted_count} old raw data files (keeping {keep_days} days)")
        return deleted_count
