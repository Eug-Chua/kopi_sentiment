"""Data models for sentiment analyis output"""

from enum import Enum
from pydantic import BaseModel

class Sentiment(str, Enum):
    """Range and intensity of sentiment"""
    STRONG_POSITIVE = "strong_positive"
    POSITIVE = "positive"
    MIXED = "mixed"
    NEGATIVE = "negative"
    STRONG_NEGATIVE = "strong_negative"

class FFGACategory(str, Enum):
    """FFGA framework categories"""
    FEAR = "fear"
    FRUSTRATION = "frustration"
    GOAL = "goal"
    ASPIRATION = "aspiration"

class FFGAResult(BaseModel):
    """Result for a single FFGA category"""
    category: FFGACategory
    sentiment: Sentiment
    summary: str
    quotes: list[str] = []

class AnalysisResult(BaseModel):
    """Complete FFGA analysis for a post"""
    post_id: str
    post_title: str
    fears: FFGAResult
    frustrations: FFGAResult
    goals: FFGAResult
    aspirations: FFGAResult
    overall_sentiment: Sentiment