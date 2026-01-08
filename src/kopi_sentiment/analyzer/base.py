"""Base interface for LLM analyzers"""

from abc import ABC, abstractmethod
from kopi_sentiment.analyzer.models import AnalysisResult
from kopi_sentiment.scraper.reddit import RedditPost

class BaseAnalyzer:
    """Abstract base class for sentiment analyzers"""

    @abstractmethod
    def analyze(self, post:RedditPost) -> AnalysisResult:
        """Analyze a Reddit post and return FFGA sentiment analysis

        Args:
            post: Reddit post with comments to analyze
        
        Returns:
            AnalysisResult with FFGA breakdown and sentiment scores
        """
        pass

    @abstractmethod
    def analyze_batch(self, posts: list[RedditPost]) -> list[AnalysisResult]:
        """Analyze multiple Reddit posts

        Args:
            posts: list of Reddit posts to analyze

        Returns:
            List of AnalysisResult for each post
        """
        pass
