"""Entity trend calculator for tracking topics over time.

Aggregates entities from daily thematic clusters to show
which topics are trending across multiple days.
"""

import json
from collections import defaultdict
from datetime import date
from pathlib import Path

from .models import EntityDayData, EntityTrend, EntityTrendsReport


class EntityTrendCalculator:
    """Calculates entity trends from daily reports."""

    def generate_report(
        self,
        data_dir: str | Path = "data/daily",
        top_n: int = 10,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> EntityTrendsReport:
        """Generate entity trends report from daily data.

        Args:
            data_dir: Directory containing daily JSON reports.
            top_n: Number of top entities to include.
            start_date: Optional start date to filter reports (inclusive).
            end_date: Optional end date to filter reports (inclusive).

        Returns:
            EntityTrendsReport with aggregated trends.
        """
        data_path = Path(data_dir)
        daily_data = self._load_daily_reports(data_path, start_date, end_date)

        if len(daily_data) < 1:
            return EntityTrendsReport(
                generated_at=date.today(),
                days_analyzed=0,
                top_entities=[],
            )

        # Aggregate entities across days
        entity_map = self._aggregate_entities(daily_data)

        # Calculate trends
        entity_trends = self._calculate_trends(entity_map, top_n)

        return EntityTrendsReport(
            generated_at=date.today(),
            days_analyzed=len(daily_data),
            top_entities=entity_trends,
        )

    def _load_daily_reports(
        self,
        data_dir: Path,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[dict]:
        """Load daily reports, optionally filtered by date range."""
        reports = []

        for file_path in sorted(data_dir.glob("*.json")):
            # Extract date from filename (e.g., "2026-01-15.json")
            file_date_str = file_path.stem
            try:
                file_date = date.fromisoformat(file_date_str)
            except ValueError:
                # Skip files that don't have date-formatted names
                continue

            # Apply date filters
            if start_date and file_date < start_date:
                continue
            if end_date and file_date > end_date:
                continue

            with open(file_path) as f:
                data = json.load(f)
                reports.append(data)

        return reports

    def _aggregate_entities(
        self,
        daily_data: list[dict],
    ) -> dict[str, list[EntityDayData]]:
        """Aggregate entity mentions across all days."""
        entity_map: dict[str, list[EntityDayData]] = defaultdict(list)

        for day in daily_data:
            day_date = date.fromisoformat(day["date_id"])
            clusters = day.get("thematic_clusters", [])

            # Track entities seen this day (to avoid double counting)
            day_entities: dict[str, dict] = {}

            for cluster in clusters:
                entities = cluster.get("entities", [])
                engagement = cluster.get("engagement_score", 0)
                category = cluster.get("dominant_emotion", "")

                for entity in entities:
                    # Normalize entity name
                    entity_normalized = entity.strip().upper()

                    if entity_normalized not in day_entities:
                        day_entities[entity_normalized] = {
                            "engagement": 0,
                            "mention_count": 0,
                            "categories": [],
                        }

                    day_entities[entity_normalized]["engagement"] += engagement
                    day_entities[entity_normalized]["mention_count"] += 1
                    if category and category not in day_entities[entity_normalized]["categories"]:
                        day_entities[entity_normalized]["categories"].append(category)

            # Add day data to entity map
            for entity_name, data in day_entities.items():
                entity_map[entity_name].append(EntityDayData(
                    date=day_date,
                    engagement=data["engagement"],
                    mention_count=data["mention_count"],
                    categories=data["categories"],
                ))

        return dict(entity_map)

    def _calculate_trends(
        self,
        entity_map: dict[str, list[EntityDayData]],
        top_n: int,
    ) -> list[EntityTrend]:
        """Calculate trends for top entities."""
        entity_stats = []

        for entity_name, daily_data in entity_map.items():
            total_engagement = sum(d.engagement for d in daily_data)
            total_mentions = sum(d.mention_count for d in daily_data)
            days_present = len(daily_data)

            # Find dominant category
            category_counts: dict[str, int] = defaultdict(int)
            for d in daily_data:
                for cat in d.categories:
                    category_counts[cat] += 1
            dominant_category = max(category_counts, key=category_counts.get) if category_counts else "unknown"

            # Calculate trend direction (compare first half vs second half)
            trend_direction = "stable"
            if len(daily_data) >= 4:
                mid = len(daily_data) // 2
                first_half_eng = sum(d.engagement for d in daily_data[:mid])
                second_half_eng = sum(d.engagement for d in daily_data[mid:])

                if second_half_eng > first_half_eng * 1.2:
                    trend_direction = "rising"
                elif second_half_eng < first_half_eng * 0.8:
                    trend_direction = "falling"

            entity_stats.append(EntityTrend(
                entity=entity_name,
                total_engagement=total_engagement,
                total_mentions=total_mentions,
                days_present=days_present,
                daily_data=sorted(daily_data, key=lambda x: x.date),
                dominant_category=dominant_category,
                trend_direction=trend_direction,
            ))

        # Sort by total engagement and return top N
        entity_stats.sort(key=lambda x: x.total_engagement, reverse=True)
        return entity_stats[:top_n]