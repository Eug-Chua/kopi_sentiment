"""Base interface for LLM analyzers"""

import json
import logging
from abc import ABC, abstractmethod
from kopi_sentiment.analyzer.models import (Intensity,
                                            FFGACategory,
                                            FFGAResult,
                                            AnalysisResult)
from kopi_sentiment.analyzer.prompts import (EXTRACT_SYSTEM_PROMPT,
                                             INTENSITY_SYSTEM_PROMPT,
                                             build_extract_prompt,
                                             build_intensity_prompt)

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

    def _extract_quotes(self, post: RedditPost) -> dict[str, list[str]]:
        """Step 1: Extract and categorize quotes from post."""
        user_prompt = build_extract_prompt(
            title=post.title,
            selftext=post.selftext,
            comments=post.comments,
            subreddit=post.subreddit,
        )

        response = self._call_llm(EXTRACT_SYSTEM_PROMPT, user_prompt)
        response = self._clean_json_response(response)

        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse extraction response: {e}")
            return {"fears": [], "frustrations": [], "goals": [], "aspirations": []}


    def _assess_intensity(self, title: str, quotes: dict[str, list[str]]) -> dict:
        """Step 2: Assess intensity for categorized quotes."""
        user_prompt = build_intensity_prompt(
            title=title,
            fears=quotes.get("fears", []),
            frustrations=quotes.get("frustrations", []),
            goals=quotes.get("goals", []),
            aspirations=quotes.get("aspirations", []),
        )

        response = self._call_llm(INTENSITY_SYSTEM_PROMPT, user_prompt)
        response = self._clean_json_response(response)

        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse intensity response: {e}")
            return {}

        
    def _clean_json_response(self, response: str) -> str:
        """Remove markdown code blocks from LLM response."""
        response = response.strip()
        
        # Remove ```json or ``` at start
        if response.startswith("```json"):
            response = response.removeprefix("```json")
        elif response.startswith("```"):
            response = response.removeprefix("```")
        
        # Remove ``` at end
        if response.endswith("```"):
            response = response.removesuffix("```")
        
        return response.strip()

    def _build_ffga_result(self,
                           category: FFGACategory,
                           key: str,
                           quotes: dict,
                           intensity_data: dict) -> FFGAResult:
        """Build a single FFGA result"""

        data = intensity_data.get(key, {})
        return FFGAResult(category=category,
                          intensity=data.get('intensity', 'moderate'),
                          summary=data.get('summary', 'No analysis available.'),
                          quotes=quotes.get(key, [])
        )

    def _build_analysis_result(self,
                               post: RedditPost,
                               quotes: dict,
                               intensity_data: dict) -> AnalysisResult:
        """Build the complete analysis result"""
        fears = self._build_ffga_result(FFGACategory.FEAR, "fears", quotes, intensity_data)
        frustrations = self._build_ffga_result(FFGACategory.FRUSTRATION, "frustrations", quotes, intensity_data)
        goals = self._build_ffga_result(FFGACategory.GOAL, "goals", quotes, intensity_data)
        aspirations = self._build_ffga_result(FFGACategory.ASPIRATION, "aspirations", quotes, intensity_data)

        return AnalysisResult(post_id=post.id,
                              post_title=post.title,
                              fears=fears,
                              frustrations=frustrations,
                              goals=goals,
                              aspirations=aspirations)

    def analyze(self, post: RedditPost) -> AnalysisResult:
        """Analyze a Reddit post and return FFGA analysis"""
        quotes = self._extract_quotes(post)
        intensity_data = self._assess_intensity(post.title, quotes)
        return self._build_analysis_result(post, quotes, intensity_data)

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

