"""Weekly sentiment analysis pipeline."""

from datetime import date, timedelta, datetime
import logging
import time

from kopi_sentiment.pipeline.base import BasePipeline
from kopi_sentiment.scraper.reddit import RedditScraper, RedditPost
from kopi_sentiment.storage.json_storage import JSONStorage
from kopi_sentiment.analyzer.models import (
    WeeklyReport,
    WeeklyReportMetadata,
    WeeklyTrends,
)

logger = logging.getLogger(__name__)


class WeeklyPipeline(BasePipeline):
    """Pipeline for weekly sentiment analysis."""

    def __init__(self, subreddits, posts_per_subreddit, llm_provider, storage_path):
        super().__init__(subreddits, posts_per_subreddit, llm_provider)
        self.storage = JSONStorage(storage_path)
        logger.info(
            f"WeeklyPipeline initialized: {len(self.subreddits)} subreddits, "
            f"{self.posts_per_subreddit} posts each"
        )

    def get_report_id(self, target_date=None) -> str:
        """Get week ID in ISO format (YYYY-Www)."""
        target = target_date or date.today()
        return target.strftime("%G-W%V")

    def get_week_bounds(self, week_id: str) -> tuple[date, date]:
        """Parse week ID into start and end dates."""
        year, week = week_id.split("-W")
        year, week = int(year), int(week)

        jan_4 = date(year, 1, 4)
        week_1_monday = jan_4 - timedelta(days=jan_4.weekday())

        week_start = week_1_monday + timedelta(weeks=week - 1)
        week_end = week_start + timedelta(days=6)

        logger.info(f"Week Range: {week_start} to {week_end}")
        return week_start, week_end

    def scrape_subreddit(self, subreddit: str) -> list[RedditPost]:
        """Scrape top posts from the last week."""
        scraper = RedditScraper(subreddit=subreddit)
        posts = scraper.fetch_posts_with_content(
            limit=self.posts_per_subreddit,
            delay=1.0,
            sort="top",
            time_filter="week",
        )
        logger.info(f"Scraped {len(posts)} posts from r/{subreddit} (top of week)")
        return posts

    def _get_previous_week_id(self, current_week_id: str) -> str:
        """Get the previous week's ID."""
        year, week = current_week_id.split("-W")
        year, week = int(year), int(week)
        if week == 1:
            year -= 1
            week = 52
        else:
            week -= 1
        return f"{year}-W{week:02d}"

    def _load_previous_report(self, week_id: str) -> WeeklyReport | None:
        """Try to load previous week's report."""
        prev_id = self._get_previous_week_id(week_id)
        try:
            return self.storage.load_weekly_report(prev_id)
        except FileNotFoundError:
            logger.info(f"No previous week report found for {prev_id}")
            return None

    def _calculate_trends(self, current_quotes, previous_report) -> WeeklyTrends:
        """Calculate week-over-week trends."""
        if not previous_report:
            return WeeklyTrends(has_previous_week=False)

        prev_quotes = previous_report.all_quotes
        return WeeklyTrends(
            has_previous_week=True,
            previous_week_id=previous_report.week_id,
            fears=self._calc_category_trend(len(current_quotes.fears), len(prev_quotes.fears)),
            frustrations=self._calc_category_trend(len(current_quotes.frustrations), len(prev_quotes.frustrations)),
            goals=self._calc_category_trend(len(current_quotes.goals), len(prev_quotes.goals)),
            aspirations=self._calc_category_trend(len(current_quotes.aspirations), len(prev_quotes.aspirations)),
        )

    def _build_trend_summary(self, trends: WeeklyTrends) -> str:
        """Build a text summary of trends for prompts."""
        if not trends.has_previous_week:
            return "No previous week data available for comparison."

        parts = []
        for name, trend in [
            ("Fears", trends.fears),
            ("Frustrations", trends.frustrations),
            ("Goals", trends.goals),
            ("Aspirations", trends.aspirations),
        ]:
            if trend:
                parts.append(f"- {name}: {trend.direction.value} {trend.change_pct:+.1f}% ({trend.previous_count} → {trend.current_count})")
        return "\n".join(parts)

    def run(self, week_id: str | None = None) -> WeeklyReport:
        """Execute the full weekly pipeline."""
        week_id = week_id or self.get_report_id()
        week_start, week_end = self.get_week_bounds(week_id)

        logger.info(f"Starting weekly pipeline for {week_id}")

        # Scrape and analyze each subreddit
        subreddit_reports = []
        all_analyses = []
        total_posts = 0
        total_comments = 0

        for i, subreddit in enumerate(self.subreddits):
            posts = self.scrape_subreddit(subreddit)
            report, analyses = self.analyze_subreddit(subreddit, posts)

            subreddit_reports.append(report)
            all_analyses.extend(analyses)
            total_posts += report.posts_analyzed
            total_comments += report.comments_analyzed

            if i < len(self.subreddits) - 1:
                logger.info("Waiting 1 minute before next subreddit...")
                time.sleep(60)

        # Aggregate quotes
        all_quotes = self.aggregate_quotes(subreddit_reports)
        quotes_dict = self.quotes_to_dict(all_quotes)

        # Generate summary
        logger.info("Generating weekly summary...")
        overall_sentiment = self.analyzer.generate_weekly_summary(
            week_id=week_id,
            analyses=all_analyses,
            all_quotes=quotes_dict,
        )

        # Detect thematic clusters
        logger.info("Detecting thematic clusters...")
        post_titles = self.get_post_titles_with_scores(subreddit_reports)
        thematic_clusters = self.analyzer.detect_thematic_clusters(
            post_titles=post_titles,
            all_quotes=quotes_dict,
        )

        # Calculate trends
        logger.info("Calculating week-over-week trends...")
        previous_report = self._load_previous_report(week_id)
        trends = self._calculate_trends(all_quotes, previous_report)
        trend_summary = self._build_trend_summary(trends)

        # Generate insights
        logger.info("Generating weekly insights...")
        high_engagement_quotes = self._get_high_engagement_quotes(all_quotes, min_score=20, limit=15)
        thematic_cluster_names = [t.topic for t in thematic_clusters]
        insights = self.analyzer.generate_weekly_insights(
            week_id=week_id,
            overall_sentiment=overall_sentiment,
            trend_summary=trend_summary,
            high_engagement_quotes=high_engagement_quotes,
            trending_topics=thematic_cluster_names,
        )

        # Cluster themes and detect signals
        logger.info("Clustering themes...")
        theme_clusters = self.analyzer.cluster_themes(all_quotes=quotes_dict)

        logger.info("Detecting signals...")
        intensity_counts = self._count_intensity(all_analyses)
        signals = self.analyzer.detect_signals(
            intensity_counts=intensity_counts,
            previous_week_comparison=trend_summary if trends.has_previous_week else "",
            high_engagement_quotes=high_engagement_quotes,
            trending_topics=thematic_cluster_names,
        )

        # Build and save report
        report = WeeklyReport(
            week_id=week_id,
            week_start=week_start,
            week_end=week_end,
            generated_at=datetime.now(),
            metadata=WeeklyReportMetadata(
                total_posts_analyzed=total_posts,
                total_comments_analyzed=total_comments,
                subreddits=self.subreddits,
            ),
            overall_sentiment=overall_sentiment,
            subreddits=subreddit_reports,
            all_quotes=all_quotes,
            thematic_clusters=thematic_clusters,
            insights=insights,
            trends=trends,
            theme_clusters=theme_clusters,
            signals=signals,
        )

        saved_path = self.storage.save_weekly_report(report)
        logger.info(f"Weekly report saved to {saved_path}")

        web_storage = JSONStorage("web/public/data/weekly")
        web_path = web_storage.save_weekly_report(report)
        logger.info(f"Weekly report also saved to {web_path}")

        return report
