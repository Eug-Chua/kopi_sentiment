from datetime import date, timedelta, datetime
import logging
import time

from kopi_sentiment.scraper.reddit import RedditScraper, RedditPost
from kopi_sentiment.config.settings import settings
from kopi_sentiment.analyzer.claude import ClaudeAnalyzer
from kopi_sentiment.analyzer.openai import OpenAIAnalyzer
from kopi_sentiment.storage.json_storage import JSONStorage
from kopi_sentiment.analyzer.models import (SubredditReport,
                                            AnalysisResult,
                                            AllQuotes,
                                            WeeklyReport,
                                            PostAnalysis,
                                            QuoteWithMetadata,
                                            WeeklyReportMetadata)

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
        logger.info(f"Analyzeing {len(posts)} posts from r/{subreddit}...")

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
        for quote_text in category_result.quotes:
            quote = QuoteWithMetadata(
                text=quote_text,
                post_id=post_analysis.id,
                post_title=post_analysis.title,
                subreddit=report.name,
                score=post_analysis.score,
                intensity=category_result.intensity)
            target_list.append(quote)

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

        # detect trending topics
        logger.info("Detecting tranding topics...")
        post_titles = [post.title for report in subreddit_reports for post in report.top_posts]

        trending_topics = self.analyzer.detect_trending_topics(post_titles=post_titles,
                                                               all_quotes=quotes_dict)
        
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
            trending_topics=trending_topics
        )
        
        saved_path = self.storage.save_weekly_report(report)
        logger.info(f"Weekly report saved to {saved_path}")

        return report

if __name__ == "__main__":
    print(date.today())