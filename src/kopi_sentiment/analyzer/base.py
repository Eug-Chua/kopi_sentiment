"""Base interface for LLM analyzers"""

import json
import logging
from abc import ABC, abstractmethod
from kopi_sentiment.analyzer.models import (Sentiment,
                                            FFGACategory,
                                            FFGAResult,
                                            AnalysisResult)
from kopi_sentiment.analyzer.prompts import (EXTRACT_SYSTEM_PROMPT,
                                             SENTIMENT_SYSTEM_PROMPT,
                                             build_extract_prompt,
                                             build_sentiment_prompt)

from kopi_sentiment.scraper.reddit import RedditPost

logger = logging.getLogger(__name__)

class BaseAnalyzer:
    """Abstract base class for sentiment analyzers"""

    @abstractmethod
    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Make a call to the LLM provider
        
        Each provider (Claude, OpenAI) implements this differently.
        """
        pass

    @abstractmethod
    def _extract_quote(self, post: RedditPost) -> dict[str, list[str]]:
        """Step 1: extract and categorize quotes from post"""

        user_prompt = build_extract_prompt(title=post.title,
                                           selftext=post.selftext,
                                           comments=post.comments,
                                           subreddit=post.subreddit)

        response = self._call_llm(EXTRACT_SYSTEM_PROMPT, user_prompt)

        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse extraction response: {e}")
            return {'fears': [], 'frustrations': [], 'goals':[], 'aspirations': []}
    
    def _assess_sentiment(self, title: str, quotes: dict[str, list[str]]) -> dict:
        """Step 2: assess sentiment for categorized quotes"""
        
        user_prompt = build_sentiment_prompt(title=title,
                                             fears=quotes.get('fears', []),
                                             frustrations=quotes.get('frustrations', []),
                                             goals=quotes.get('goals', []),
                                             aspirations=quotes.get('aspirations', []))
        
        response = self._call_llm(SENTIMENT_SYSTEM_PROMPT, user_prompt)

        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse sentiment response: {e}")
            return {}

    def _calculate_overall_sentiment(self, sentiments: list[Sentiment]) -> Sentiment:
        """Calculate the overall sentiment from category sentiments"""
        counts = {}

        for s in sentiments:
            counts[s] = counts.get(s, 0) + 1
        
        if not counts:
            return Sentiment.MIXED
        
        # return most frequent, with negative bias for ties
        priority = [Sentiment.STRONG_NEGATIVE,
                    Sentiment.NEGATIVE,
                    Sentiment.MIXED,
                    Sentiment.POSITIVE,
                    Sentiment.STRONG_POSITIVE]
        
        max_count = max(counts.values())
        for sentiment in priority:
            if counts.get(sentiment, 0) == max_count:
                return sentiment
            
        return Sentiment.MIXED

    def _build_ffga_result(self,
                           category: FFGACategory,
                           key:str,
                           quotes: dict,
                           sentiment_data: dict) -> FFGAResult:
        """Build a single FFGA result"""

        data = sentiment_data.get(key, {})
        return FFGAResult(category=category,
                          sentiment=data.get('sentiment', 'mixed'),
                          summary=data.get('summary','No analysis available.'),
                          quotes=quotes.get(key, [])
        )
    
    def _build_analysis_result(self,
                               post: RedditPost,
                               quotes: dict,
                               sentiment_data: dict) -> AnalysisResult:
        """Build the complete analysis result"""
        fears = self._build_ffga_result(FFGACategory.FEAR, "fears", quotes, sentiment_data)
        frustrations = self._build_ffga_result(FFGACategory.FRUSTRATION, "frustrations", quotes, sentiment_data)
        goals = self._build_ffga_result(FFGACategory.GOAL, "goals", quotes, sentiment_data)
        aspirations = self._build_ffga_result(FFGACategory.ASPIRATION, "aspirations", quotes, sentiment_data)

        overall = self._calculate_overall_sentiment([fears.sentiment,
                                                     frustrations.sentiment,
                                                     goals.sentiment,
                                                     aspirations.sentiment])
        return AnalysisResult(post_id=post.id,
                              post_title=post.title,
                              fears=fears,
                              frustrations=frustrations,
                              goals=goals,
                              aspirations=aspirations,
                              overall_sentiment=overall)


    def analyze(self, post:RedditPost) -> AnalysisResult:
        """Analyze a Reddit post and return FFGA sentiment analysis"""
        quotes = self._extract_quote(post)
        sentiment_data = self._assess_sentiment(post.title, quotes)
        return self._build_analysis_result(post, quotes, sentiment_data)

    def analyze_batch(self, posts: list[RedditPost]) -> list[AnalysisResult]:
        """Analyze multiple Reddit posts"""
        results = []
        for post in posts:
            try:
                result = self.analyze(post)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to analyze post {post.id}: {e}")
        
        return results

