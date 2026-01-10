"""Data models for sentiment analyis output"""

from enum import Enum
from pydantic import BaseModel

class Intensity(str, Enum):
    """How strongly the FFGA emotion is expressed"""
    MILD = "mild"          # Slight, passing mention
    MODERATE = "moderate"  # Clear expression
    STRONG = "strong"      # Intense, emphatic expression

class FFGACategory(str, Enum):
    """FFGA framework categories"""
    FEAR = "fear"
    FRUSTRATION = "frustration"
    GOAL = "goal"
    ASPIRATION = "aspiration"

class FFGAResult(BaseModel):
    """Result for a single FFGA category"""
    category: FFGACategory
    intensity: Intensity
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