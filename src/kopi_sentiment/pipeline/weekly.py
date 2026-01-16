from datetime import date, timedelta, datetime
import logging
import time

from kopi_sentiment.scraper.reddit import RedditScraper, RedditPost
from kopi_sentiment.config.settings import settings
from kopi_sentiment.analyzer.claude import ClaudeAnalyzer
from kopi_sentiment.analyzer.openai import OpenAIAnalyzer
from kopi_sentiment.analyzer.hybrid import HybridAnalyzer
from kopi_sentiment.storage.json_storage import JSONStorage
from kopi_sentiment.analyzer.models import (SubredditReport,
                                            AnalysisResult,
                                            AllQuotes,
                                            WeeklyReport,
                                            PostAnalysis,
                                            QuoteWithMetadata,
                                            WeeklyReportMetadata,
                                            WeeklyTrends,
                                            CategoryTrend,
                                            TrendDirection)

logger = logging.getLogger(__name__)

class WeeklyPipeline:

    def __init__(self, subreddits, posts_per_subreddit, llm_provider, storage_path):
        """Initalize scraper config, analyzer, jsonstorage"""
        self.subreddits = subreddits or settings.reddit_subreddit
        self.posts_per_subreddit = posts_per_subreddit
        self.storage = JSONStorage(storage_path)

        provider = llm_provider or settings.llm_provider
        if provider == 'claude':
            self.analyzer = ClaudeAnalyzer()
        elif provider == 'hybrid':
            self.analyzer = HybridAnalyzer()
        else:
            self.analyzer = OpenAIAnalyzer()

        logger.info(f"WeeklyPipeline initialized: {len(self.subreddits)} subreddits, "
                    f"{self.posts_per_subreddit} posts each, using {provider}")            

    def get_week(self, target_date=None) -> str:
        """Get week of defined target date"""
        target = target_date or date.today()
        return target.strftime("%G-W%V")

    def get_week_bounds(self, week_id) -> tuple[date, date]:
        """Parse week id into year and week number"""
        year, week = week_id.split("-W")
        year = int(year)
        week = int(week)

        # jan 4 is always in ISO week 1
        jan_4 = date(year, 1, 4)
        week_1_monday = jan_4 - timedelta(days=jan_4.weekday())

        week_start = week_1_monday + timedelta(weeks=week - 1)
        week_end = week_start + timedelta(days=6)

        logger.info(f"Week Range: {week_start} to {week_end}")

        return week_start, week_end
    
    def scrape_subreddit(self, subreddit) -> list[RedditPost]:
        """Scrape subreddit posts"""
        scraper = RedditScraper(subreddit=subreddit)
        posts = scraper.fetch_posts_with_content(
            limit=self.posts_per_subreddit,
            delay=1.0)  # rate limiting
        
        logger.info(f"Scraped {len(posts)} posts from r/{subreddit}")

        return posts
    
    def analyze_subreddit(self, subreddit, posts) -> tuple[SubredditReport, list[AnalysisResult]]:
        """Analyze all posts from a subreddit using 2-step LLM chain"""
        logger.info(f"Analyzing {len(posts)} posts from r/{subreddit}...")

        analyses = []
        post_analyses = []
        total_comments = 0

        for post in posts:
            try:
                # run 2-step LLM analysis
                analysis = self.analyzer.analyze(post)
                analyses.append(analysis)

                # wrap with metadata for the report
                post_analysis = PostAnalysis(
                    id=post.id,
                    title=post.title,
                    url=post.url,
                    score=post.score,
                    num_comments=post.num_comments,
                    created_at=post.created_at,
                    subreddit=subreddit,
                    analysis=analysis
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
            top_posts=post_analyses
        )

        logger.info(f"Completed r/{subreddit}: {len(post_analyses)} posts, {total_comments} comments")

        return report, analyses

    def aggregate_quotes(self, subreddit_reports) -> AllQuotes:
        """Extract quotes from all analyses into QuoteWithMetadata"""
        all_quotes = AllQuotes()
        for report in subreddit_reports:
            for post_analysis in report.top_posts:
                analysis = post_analysis.analysis

                self._add_quotes(post_analysis, report, analysis.fears, all_quotes.fears)
                self._add_quotes(post_analysis, report, analysis.frustrations, all_quotes.frustrations)
                self._add_quotes(post_analysis, report, analysis.goals, all_quotes.goals)
                self._add_quotes(post_analysis, report, analysis.aspirations, all_quotes.aspirations)

        logger.info(
            f"Aggregated quotes: {len(all_quotes.fears)} fears, "
            f"{len(all_quotes.frustrations)} frustrations, "
            f"{len(all_quotes.goals)} goals, "
            f"{len(all_quotes.aspirations)} aspirations"
        )
        
        return all_quotes

    def _add_quotes(self, post_analysis, report, category_result, target_list):
        """Helper function to add quotes with metadata"""
        for extracted_quote in category_result.quotes:
            quote = QuoteWithMetadata(
                text=extracted_quote.quote,
                post_id=post_analysis.id,
                post_title=post_analysis.title,
                subreddit=report.name,
                score=post_analysis.score,
                comment_score=extracted_quote.score,
                intensity=category_result.intensity)
            target_list.append(quote)

    def _get_previous_week_id(self, current_week_id: str) -> str:
        """Get the previous week's ID"""
        year, week = current_week_id.split("-W")
        year, week = int(year), int(week)
        if week == 1:
            year -= 1
            week = 52
        else:
            week -= 1
        return f"{year}-W{week:02d}"

    def _load_previous_week(self, week_id: str) -> WeeklyReport | None:
        """Try to load previous week's report"""
        prev_week_id = self._get_previous_week_id(week_id)
        try:
            return self.storage.load_weekly_report(prev_week_id)
        except FileNotFoundError:
            logger.info(f"No previous week report found for {prev_week_id}")
            return None

    def _calculate_trends(self, current_quotes: AllQuotes, previous_report: WeeklyReport | None) -> WeeklyTrends:
        """Calculate week-over-week trends"""
        if not previous_report:
            return WeeklyTrends(has_previous_week=False)

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
        return WeeklyTrends(
            has_previous_week=True,
            previous_week_id=previous_report.week_id,
            fears=calc_category_trend(len(current_quotes.fears), len(prev_quotes.fears)),
            frustrations=calc_category_trend(len(current_quotes.frustrations), len(prev_quotes.frustrations)),
            goals=calc_category_trend(len(current_quotes.goals), len(prev_quotes.goals)),
            aspirations=calc_category_trend(len(current_quotes.aspirations), len(prev_quotes.aspirations)),
        )

    def _build_trend_summary(self, trends: WeeklyTrends) -> str:
        """Build a text summary of trends for prompts"""
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

    def _get_high_engagement_quotes(self, all_quotes: AllQuotes, min_score: int = 20) -> list[str]:
        """Get quotes with high engagement scores"""
        all_quote_list = (
            list(all_quotes.fears) +
            list(all_quotes.frustrations) +
            list(all_quotes.goals) +
            list(all_quotes.aspirations)
        )
        high_engagement = [q for q in all_quote_list if q.score >= min_score]
        high_engagement.sort(key=lambda q: q.score, reverse=True)
        return [f"[+{q.score}] {q.text}" for q in high_engagement[:15]]

    def _count_intensity(self, all_analyses: list[AnalysisResult]) -> dict[str, dict[str, int]]:
        """Count quotes by intensity for each category"""
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
                intensity = result.intensity.value if hasattr(result.intensity, 'value') else result.intensity
                if intensity in counts[key]:
                    counts[key][intensity] += len(result.quotes)
        return counts

    def run(self, week_id) -> WeeklyReport:
        """Executes the full weekly pipeline"""
        week_id = week_id or self.get_week()
        week_start, week_end = self.get_week_bounds(week_id)

        logger.info(f"Starting weekly pipeline for {week_id}")

        # scrape and analyze each subreddit
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

            # Wait 2 minutes between subreddits (except after the last one)
            if i < len(self.subreddits) - 1:
                logger.info("Waiting 1 minute before next subreddit...")
                time.sleep(60)

        # aggregate all quotes
        all_quotes = self.aggregate_quotes(subreddit_reports)

        # convert AllQuotes to dict format for LLM prompts
        quotes_dict = {
            'fears': [q.text for q in all_quotes.fears],
            'frustrations': [q.text for q in all_quotes.frustrations],
            'goals': [q.text for q in all_quotes.goals],
            'aspirations': [q.text for q in all_quotes.aspirations]
        }

        # generate weekly summary
        logger.info("Generating weekly summary...")
        overall_sentiment = self.analyzer.generate_weekly_summary(
            week_id=week_id,
            analyses=all_analyses,
            all_quotes=quotes_dict
        )

        # detect thematic clusters (what people are discussing)
        logger.info("Detecting thematic clusters...")
        # Include scores with titles so LLM can weight by popularity
        post_titles_with_scores = [
            f"[+{post.score}] {post.title}"
            for report in subreddit_reports
            for post in report.top_posts
        ]

        thematic_clusters = self.analyzer.detect_thematic_clusters(
            post_titles=post_titles_with_scores,
            all_quotes=quotes_dict
        )

        # load previous week and calculate trends
        logger.info("Calculating week-over-week trends...")
        previous_report = self._load_previous_week(week_id)
        trends = self._calculate_trends(all_quotes, previous_report)
        trend_summary = self._build_trend_summary(trends)

        # get high engagement quotes
        high_engagement_quotes = self._get_high_engagement_quotes(all_quotes)
        thematic_cluster_names = [t.topic for t in thematic_clusters]

        # generate weekly insights
        logger.info("Generating weekly insights...")
        insights = self.analyzer.generate_weekly_insights(
            week_id=week_id,
            overall_sentiment=overall_sentiment,
            trend_summary=trend_summary,
            high_engagement_quotes=high_engagement_quotes,
            trending_topics=thematic_cluster_names,  # Pass cluster names for insights
        )

        # cluster themes
        logger.info("Clustering themes...")
        theme_clusters = self.analyzer.cluster_themes(all_quotes=quotes_dict)

        # detect signals
        logger.info("Detecting signals...")
        intensity_counts = self._count_intensity(all_analyses)
        previous_week_comparison = trend_summary if trends.has_previous_week else ""
        signals = self.analyzer.detect_signals(
            intensity_counts=intensity_counts,
            previous_week_comparison=previous_week_comparison,
            high_engagement_quotes=high_engagement_quotes,
            trending_topics=thematic_cluster_names,  # Pass cluster names for signals
        )

        # build final report
        report = WeeklyReport(
            week_id=week_id,
            week_start=week_start,
            week_end=week_end,
            generated_at=datetime.now(),
            metadata=WeeklyReportMetadata(
                total_posts_analyzed=total_posts,
                total_comments_analyzed=total_comments,
                subreddits=self.subreddits
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

        # Also save to web/public/data/weekly for frontend
        web_storage = JSONStorage("web/public/data/weekly")
        web_path = web_storage.save_weekly_report(report)
        logger.info(f"Weekly report also saved to {web_path}")

        return report

if __name__ == "__main__":
    print(date.today())