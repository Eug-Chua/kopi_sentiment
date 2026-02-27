"""Daily sentiment analysis pipeline."""

from datetime import date, timedelta, datetime
import logging
import time

from kopi_sentiment.config.settings import settings
from kopi_sentiment.pipeline.base import BasePipeline
from kopi_sentiment.scraper.reddit import RedditScraper, RedditPost
from kopi_sentiment.storage.json_storage import DailyJSONStorage, RawDataStorage
from kopi_sentiment.analyzer.models import (
    DailyReport,
    DailyReportMetadata,
    DailyTrends,
    DailyInsights,
)

logger = logging.getLogger(__name__)


class DailyPipeline(BasePipeline):
    """Pipeline for daily sentiment analysis of the past 24 hours."""

    def __init__(self, subreddits, posts_per_subreddit, llm_provider, storage_path):
        super().__init__(subreddits, posts_per_subreddit, llm_provider)
        self.storage = DailyJSONStorage(storage_path)
        self.raw_storage = RawDataStorage(data_type="daily")
        logger.info(
            f"DailyPipeline initialized: {len(self.subreddits)} subreddits, "
            f"{self.posts_per_subreddit} posts each"
        )

    def get_report_id(self, target_date: date | None = None) -> str:
        """Get date ID in ISO format (YYYY-MM-DD)."""
        target = target_date or date.today()
        return target.isoformat()

    def scrape_subreddit(self, subreddit: str) -> list[RedditPost]:
        """Scrape top posts from the last 24 hours."""
        scraper = RedditScraper(subreddit=subreddit)
        posts = scraper.fetch_posts_with_content(
            limit=self.posts_per_subreddit,
            delay=settings.scraper_delay,
            sort="top",
            time_filter="day",
        )
        logger.info(f"Scraped {len(posts)} posts from r/{subreddit} (top of day)")
        return posts

    def _get_previous_date_id(self, current_date_id: str) -> str:
        """Get the previous day's date ID."""
        current_date = date.fromisoformat(current_date_id)
        previous_date = current_date - timedelta(days=1)
        return previous_date.isoformat()

    def _load_previous_report(self, date_id: str) -> DailyReport | None:
        """Try to load previous day's report."""
        prev_id = self._get_previous_date_id(date_id)
        try:
            return self.storage.load_daily_report(prev_id)
        except FileNotFoundError:
            logger.info(f"No previous day report found for {prev_id}")
            return None

    def _calculate_trends(self, current_quotes, previous_report) -> DailyTrends:
        """Calculate day-over-day trends."""
        if not previous_report:
            return DailyTrends(has_previous_day=False)

        prev_quotes = previous_report.all_quotes
        return DailyTrends(
            has_previous_day=True,
            previous_date=previous_report.report_date,
            fears=self._calc_category_trend(len(current_quotes.fears), len(prev_quotes.fears)),
            frustrations=self._calc_category_trend(len(current_quotes.frustrations), len(prev_quotes.frustrations)),
            optimism=self._calc_category_trend(len(current_quotes.optimism), len(prev_quotes.optimism)),
        )

    def _build_trend_summary(self, trends: DailyTrends) -> str:
        """Build a text summary of trends for prompts."""
        if not trends.has_previous_day:
            return "No previous day data available for comparison."

        parts = []
        for name, trend in [
            ("Fears", trends.fears),
            ("Frustrations", trends.frustrations),
            ("Optimism", trends.optimism),
        ]:
            if trend:
                parts.append(f"- {name}: {trend.direction.value} {trend.change_pct:+.1f}% ({trend.previous_count} → {trend.current_count})")
        return "\n".join(parts)

    def run(self, date_id: str | None = None, from_raw: bool = False) -> DailyReport:
        """Execute the full daily pipeline.

        Args:
            date_id: Date to analyze (YYYY-MM-DD), defaults to today.
            from_raw: If True, skip scraping and load from saved raw data.
        """
        date_id = date_id or self.get_report_id()
        report_date = date.fromisoformat(date_id)

        logger.info(f"Starting daily pipeline for {date_id}")

        if from_raw:
            # Load from previously saved raw data (enables scrape/analyze separation)
            logger.info(f"Loading from raw data for {date_id}...")
            posts_by_subreddit = self.raw_storage.load_raw_as_posts(date_id)
            all_scraped_posts = [
                post for posts in posts_by_subreddit.values() for post in posts
            ]
            logger.info(
                f"Loaded {len(all_scraped_posts)} posts from raw data "
                f"across {len(posts_by_subreddit)} subreddits"
            )
        else:
            # Phase 1: Scrape all subreddits first
            logger.info("Phase 1: Scraping all subreddits...")
            all_scraped_posts = []
            posts_by_subreddit = {}

            for i, subreddit in enumerate(self.subreddits):
                posts = self.scrape_subreddit(subreddit)

                if not posts:
                    logger.warning(f"No posts found for r/{subreddit} in last 24h")
                    posts_by_subreddit[subreddit] = []
                    continue

                posts_by_subreddit[subreddit] = posts
                all_scraped_posts.extend(posts)

                if i < len(self.subreddits) - 1:
                    logger.info("Waiting 30 seconds before next subreddit...")
                    time.sleep(settings.subreddit_delay_daily)

            # Phase 2: Save raw scraped data before LLM analysis
            if all_scraped_posts:
                logger.info("Phase 2: Saving raw scraped data...")
                self.raw_storage.save_raw_scrape(
                    report_id=date_id,
                    posts=all_scraped_posts,
                    subreddits=self.subreddits,
                )

        # Phase 3: Analyze each subreddit
        logger.info("Phase 3: Analyzing scraped data...")
        subreddit_reports = []
        all_analyses = []
        total_posts = 0
        total_comments = 0

        for subreddit in self.subreddits:
            posts = posts_by_subreddit.get(subreddit, [])

            if not posts:
                continue

            report, analyses = self.analyze_subreddit(subreddit, posts)

            subreddit_reports.append(report)
            all_analyses.extend(analyses)
            total_posts += report.posts_analyzed
            total_comments += report.comments_analyzed

        # Aggregate quotes
        all_quotes = self.aggregate_quotes(subreddit_reports)
        quotes_dict = self.quotes_to_dict(all_quotes)

        # Generate summary
        logger.info("Generating daily summary...")
        overall_sentiment = self.analyzer.generate_weekly_summary(
            week_id=date_id,
            analyses=all_analyses,
            all_quotes=quotes_dict,
            is_daily=True,
        )

        # Detect thematic clusters and enrich with URLs
        logger.info("Detecting thematic clusters...")
        post_titles = self.get_post_titles_with_scores(subreddit_reports)
        thematic_clusters = self.analyzer.detect_thematic_clusters(
            post_titles=post_titles,
            all_quotes=quotes_dict,
        )
        title_to_url = self.build_title_to_url_map(subreddit_reports)
        thematic_clusters = self.enrich_thematic_clusters_with_urls(thematic_clusters, title_to_url)

        # Calculate trends
        logger.info("Calculating day-over-day trends...")
        previous_report = self._load_previous_report(date_id)
        trends = self._calculate_trends(all_quotes, previous_report)
        trend_summary = self._build_trend_summary(trends)

        # Generate insights
        logger.info("Generating daily insights...")
        high_engagement_quotes = self._get_high_engagement_quotes(all_quotes,
                                                                  min_score=settings.high_engagement_min_score_daily,
                                                                  limit=settings.high_engagement_limit_daily)
        thematic_cluster_names = [t.topic for t in thematic_clusters]
        weekly_insights = self.analyzer.generate_weekly_insights(
            week_id=date_id,
            overall_sentiment=overall_sentiment,
            trend_summary=trend_summary,
            high_engagement_quotes=high_engagement_quotes,
            trending_topics=thematic_cluster_names,
        )

        # Convert to DailyInsights
        insights = DailyInsights(
            headline=weekly_insights.headline,
            key_takeaways=weekly_insights.key_takeaways,
            opportunities=weekly_insights.opportunities,
            risks=weekly_insights.risks,
        )

        # Cluster themes and detect signals
        logger.info("Clustering themes...")
        theme_clusters = self.analyzer.cluster_themes(all_quotes=quotes_dict)

        logger.info("Detecting signals...")
        intensity_counts = self._count_intensity(all_analyses)
        signals = self.analyzer.detect_signals(
            intensity_counts=intensity_counts,
            previous_week_comparison=trend_summary if trends.has_previous_day else "",
            high_engagement_quotes=high_engagement_quotes,
            trending_topics=thematic_cluster_names,
        )

        # Build and save report
        report = DailyReport(
            date_id=date_id,
            report_date=report_date,
            generated_at=datetime.now(),
            metadata=DailyReportMetadata(
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

        saved_path = self.storage.save_daily_report(report)
        logger.info(f"Daily report saved to {saved_path}")

        web_storage = DailyJSONStorage(settings.web_data_path_daily)
        web_path = web_storage.save_daily_report(report)
        logger.info(f"Daily report also saved to {web_path}")

        # Cleanup old reports and raw data
        self.storage.cleanup_old_reports(keep_days=settings.report_retention_days)
        web_storage.cleanup_old_reports(keep_days=settings.report_retention_days)
        self.raw_storage.cleanup_old_raw(keep_days=settings.report_retention_days)

        return report
