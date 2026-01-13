"""JSON file storage for weekly sentiment reports."""

import json
import logging
from datetime import date, datetime
from pathlib import Path

from kopi_sentiment.analyzer.models import WeeklyReport

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
            base_path = Path("data/weekly")
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
