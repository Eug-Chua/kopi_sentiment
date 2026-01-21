"""Daily sentiment analysis pipeline - runs daily at 5pm SGT."""

from datetime import date, timedelta, datetime
import logging
import time

from kopi_sentiment.scraper.reddit import RedditScraper, RedditPost
from kopi_sentiment.config.settings import settings
from kopi_sentiment.analyzer.base import create_analyzer
from kopi_sentiment.storage.json_storage import DailyJSONStorage
from kopi_sentiment.analyzer.models import (
    SubredditReport,
    AnalysisResult,
    AllQuotes,
    DailyReport,
    PostAnalysis,
    QuoteWithMetadata,
    DailyReportMetadata,
    DailyTrends,
    DailyInsights,
    CategoryTrend,
    TrendDirection,
)

logger = logging.getLogger(__name__)


class DailyPipeline:
    """Pipeline for daily sentiment analysis of the past 24 hours."""

    def __init__(self, subreddits, posts_per_subreddit, llm_provider, storage_path):
        """Initialize scraper config, analyzer, json storage."""
        self.subreddits = subreddits or settings.reddit_subreddit
        self.posts_per_subreddit = posts_per_subreddit
        self.storage = DailyJSONStorage(storage_path)

        self.analyzer = create_analyzer(llm_provider)

        logger.info(
            f"DailyPipeline initialized: {len(self.subreddits)} subreddits, "
            f"{self.posts_per_subreddit} posts each, using {llm_provider}"
        )

    def get_date_id(self, target_date: date | None = None) -> str:
        """Get date ID in ISO format (YYYY-MM-DD)."""
        target = target_date or date.today()
        return target.isoformat()

    def scrape_subreddit(self, subreddit: str) -> list[RedditPost]:
        """Scrape top subreddit posts from the last 24 hours."""
        scraper = RedditScraper(subreddit=subreddit)
        # Fetch top posts from the last day
        posts = scraper.fetch_posts_with_content(
            limit=self.posts_per_subreddit,
            delay=1.0,
            sort="top",
            time_filter="day",
        )

        logger.info(
            f"Scraped {len(posts)} posts from r/{subreddit} (top of day)"
        )

        return posts

    def analyze_subreddit(
        self, subreddit: str, posts: list[RedditPost]
    ) -> tuple[SubredditReport, list[AnalysisResult]]:
        """Analyze all posts from a subreddit using 2-step LLM chain."""
        logger.info(f"Analyzing {len(posts)} posts from r/{subreddit}...")

        analyses = []
        post_analyses = []
        total_comments = 0

        for post in posts:
            try:
                # Run 2-step LLM analysis
                analysis = self.analyzer.analyze(post)
                analyses.append(analysis)

                # Wrap with metadata for the report
                post_analysis = PostAnalysis(
                    id=post.id,
                    title=post.title,
                    url=post.url,
                    score=post.score,
                    num_comments=post.num_comments,
                    created_at=post.created_at,
                    subreddit=subreddit,
                    analysis=analysis,
                )
                post_analyses.append(post_analysis)
                total_comments += len(post.comments)
            except Exception as e:
                logger.error(f"Failed to analyze post {post.id}: {e}")
                continue

        report = SubredditReport(
            name=subreddit,
            posts_analyzed=len(post_analyses),
            comments_analyzed=total_comments,
            top_posts=post_analyses,
        )

        logger.info(
            f"Completed r/{subreddit}: {len(post_analyses)} posts, {total_comments} comments"
        )

        return report, analyses

    def aggregate_quotes(self, subreddit_reports: list[SubredditReport]) -> AllQuotes:
        """Extract quotes from all analyses into QuoteWithMetadata."""
        all_quotes = AllQuotes()
        for report in subreddit_reports:
            for post_analysis in report.top_posts:
                analysis = post_analysis.analysis

                self._add_quotes(
                    post_analysis, report, analysis.fears, all_quotes.fears
                )
                self._add_quotes(
                    post_analysis,
                    report,
                    analysis.frustrations,
                    all_quotes.frustrations,
                )
                self._add_quotes(
                    post_analysis, report, analysis.goals, all_quotes.goals
                )
                self._add_quotes(
                    post_analysis,
                    report,
                    analysis.aspirations,
                    all_quotes.aspirations,
                )

        logger.info(
            f"Aggregated quotes: {len(all_quotes.fears)} fears, "
            f"{len(all_quotes.frustrations)} frustrations, "
            f"{len(all_quotes.goals)} goals, "
            f"{len(all_quotes.aspirations)} aspirations"
        )

        return all_quotes

    def _add_quotes(self, post_analysis, report, category_result, target_list):
        """Helper function to add quotes with metadata."""
        for extracted_quote in category_result.quotes:
            quote = QuoteWithMetadata(
                text=extracted_quote.quote,
                post_id=post_analysis.id,
                post_title=post_analysis.title,
                subreddit=report.name,
                score=post_analysis.score,
                comment_score=extracted_quote.score,
                intensity=category_result.intensity,
            )
            target_list.append(quote)

    def _get_previous_date_id(self, current_date_id: str) -> str:
        """Get the previous day's date ID."""
        current_date = date.fromisoformat(current_date_id)
        previous_date = current_date - timedelta(days=1)
        return previous_date.isoformat()

    def _load_previous_day(self, date_id: str) -> DailyReport | None:
        """Try to load previous day's report."""
        prev_date_id = self._get_previous_date_id(date_id)
        try:
            return self.storage.load_daily_report(prev_date_id)
        except FileNotFoundError:
            logger.info(f"No previous day report found for {prev_date_id}")
            return None

    def _calculate_trends(
        self, current_quotes: AllQuotes, previous_report: DailyReport | None
    ) -> DailyTrends:
        """Calculate day-over-day trends."""
        if not previous_report:
            return DailyTrends(has_previous_day=False)

        def calc_category_trend(current_count: int, previous_count: int) -> CategoryTrend:
            if previous_count == 0:
                change_pct = 100.0 if current_count > 0 else 0.0
            else:
                change_pct = ((current_count - previous_count) / previous_count) * 100

            if change_pct > 10:
                direction = TrendDirection.UP
            elif change_pct < -10:
                direction = TrendDirection.DOWN
            else:
                direction = TrendDirection.STABLE

            return CategoryTrend(
                direction=direction,
                change_pct=round(change_pct, 1),
                intensity_shift="stable",
                previous_count=previous_count,
                current_count=current_count,
            )

        prev_quotes = previous_report.all_quotes
        return DailyTrends(
            has_previous_day=True,
            previous_date=previous_report.report_date,
            fears=calc_category_trend(len(current_quotes.fears), len(prev_quotes.fears)),
            frustrations=calc_category_trend(
                len(current_quotes.frustrations), len(prev_quotes.frustrations)
            ),
            goals=calc_category_trend(len(current_quotes.goals), len(prev_quotes.goals)),
            aspirations=calc_category_trend(
                len(current_quotes.aspirations), len(prev_quotes.aspirations)
            ),
        )

    def _build_trend_summary(self, trends: DailyTrends) -> str:
        """Build a text summary of trends for prompts."""
        if not trends.has_previous_day:
            return "No previous day data available for comparison."

        parts = []
        for name, trend in [
            ("Fears", trends.fears),
            ("Frustrations", trends.frustrations),
            ("Goals", trends.goals),
            ("Aspirations", trends.aspirations),
        ]:
            if trend:
                parts.append(
                    f"- {name}: {trend.direction.value} {trend.change_pct:+.1f}% "
                    f"({trend.previous_count} → {trend.current_count})"
                )
        return "\n".join(parts)

    def _get_high_engagement_quotes(
        self, all_quotes: AllQuotes, min_score: int = 10
    ) -> list[str]:
        """Get quotes with high engagement scores."""
        all_quote_list = (
            list(all_quotes.fears)
            + list(all_quotes.frustrations)
            + list(all_quotes.goals)
            + list(all_quotes.aspirations)
        )
        high_engagement = [q for q in all_quote_list if q.score >= min_score]
        high_engagement.sort(key=lambda q: q.score, reverse=True)
        return [f"[+{q.score}] {q.text}" for q in high_engagement[:10]]

    def _count_intensity(
        self, all_analyses: list[AnalysisResult]
    ) -> dict[str, dict[str, int]]:
        """Count quotes by intensity for each category."""
        counts = {
            "fears": {"mild": 0, "moderate": 0, "strong": 0},
            "frustrations": {"mild": 0, "moderate": 0, "strong": 0},
            "goals": {"mild": 0, "moderate": 0, "strong": 0},
            "aspirations": {"mild": 0, "moderate": 0, "strong": 0},
        }
        for analysis in all_analyses:
            for key, result in [
                ("fears", analysis.fears),
                ("frustrations", analysis.frustrations),
                ("goals", analysis.goals),
                ("aspirations", analysis.aspirations),
            ]:
                intensity = (
                    result.intensity.value
                    if hasattr(result.intensity, "value")
                    else result.intensity
                )
                if intensity in counts[key]:
                    counts[key][intensity] += len(result.quotes)
        return counts

    def run(self, date_id: str | None = None) -> DailyReport:
        """Execute the full daily pipeline."""
        date_id = date_id or self.get_date_id()
        report_date = date.fromisoformat(date_id)

        logger.info(f"Starting daily pipeline for {date_id}")

        # Scrape and analyze each subreddit
        subreddit_reports = []
        all_analyses = []
        total_posts = 0
        total_comments = 0

        for i, subreddit in enumerate(self.subreddits):
            posts = self.scrape_subreddit(subreddit)

            if not posts:
                logger.warning(f"No posts found for r/{subreddit} in last 24h")
                continue

            report, analyses = self.analyze_subreddit(subreddit, posts)

            subreddit_reports.append(report)
            all_analyses.extend(analyses)
            total_posts += report.posts_analyzed
            total_comments += report.comments_analyzed

            # Wait between subreddits (except after the last one)
            if i < len(self.subreddits) - 1:
                logger.info("Waiting 30 seconds before next subreddit...")
                time.sleep(30)

        # Aggregate all quotes
        all_quotes = self.aggregate_quotes(subreddit_reports)

        # Convert AllQuotes to dict format for LLM prompts
        quotes_dict = {
            "fears": [q.text for q in all_quotes.fears],
            "frustrations": [q.text for q in all_quotes.frustrations],
            "goals": [q.text for q in all_quotes.goals],
            "aspirations": [q.text for q in all_quotes.aspirations],
        }

        # Generate daily summary
        logger.info("Generating daily summary...")
        overall_sentiment = self.analyzer.generate_weekly_summary(
            week_id=date_id,
            analyses=all_analyses,
            all_quotes=quotes_dict,
            is_daily=True,  # Use daily framing for the prompt
        )

        # Detect thematic clusters (what people are discussing)
        logger.info("Detecting thematic clusters...")
        # Include scores with titles so LLM can weight by popularity
        post_titles_with_scores = [
            f"[+{post.score}] {post.title}"
            for report in subreddit_reports
            for post in report.top_posts
        ]

        thematic_clusters = self.analyzer.detect_thematic_clusters(
            post_titles=post_titles_with_scores, all_quotes=quotes_dict
        )

        # Load previous day and calculate trends
        logger.info("Calculating day-over-day trends...")
        previous_report = self._load_previous_day(date_id)
        trends = self._calculate_trends(all_quotes, previous_report)
        trend_summary = self._build_trend_summary(trends)

        # Get high engagement quotes
        high_engagement_quotes = self._get_high_engagement_quotes(all_quotes)
        thematic_cluster_names = [t.topic for t in thematic_clusters]

        # Generate daily insights
        logger.info("Generating daily insights...")
        weekly_insights = self.analyzer.generate_weekly_insights(
            week_id=date_id,
            overall_sentiment=overall_sentiment,
            trend_summary=trend_summary,
            high_engagement_quotes=high_engagement_quotes,
            trending_topics=thematic_cluster_names,  # Pass cluster names for insights
        )

        # Convert to DailyInsights
        insights = DailyInsights(
            headline=weekly_insights.headline,
            key_takeaways=weekly_insights.key_takeaways,
            opportunities=weekly_insights.opportunities,
            risks=weekly_insights.risks,
        )

        # Cluster themes
        logger.info("Clustering themes...")
        theme_clusters = self.analyzer.cluster_themes(all_quotes=quotes_dict)

        # Detect signals
        logger.info("Detecting signals...")
        intensity_counts = self._count_intensity(all_analyses)
        previous_day_comparison = trend_summary if trends.has_previous_day else ""
        signals = self.analyzer.detect_signals(
            intensity_counts=intensity_counts,
            previous_week_comparison=previous_day_comparison,
            high_engagement_quotes=high_engagement_quotes,
            trending_topics=thematic_cluster_names,  # Pass cluster names for signals
        )

        # Build final report
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

        # Also save to web/public/data/daily for frontend
        web_storage = DailyJSONStorage("web/public/data/daily")
        web_path = web_storage.save_daily_report(report)
        logger.info(f"Daily report also saved to {web_path}")

        # Cleanup old reports (keep 7 days) in both locations
        self.storage.cleanup_old_reports(keep_days=30)
        web_storage.cleanup_old_reports(keep_days=30)

        return report


if __name__ == "__main__":
    print(date.today())