"""Hybrid analyzer using OpenAI for extraction and Claude for synthesis."""

import logging
from anthropic import Anthropic
from openai import OpenAI

from kopi_sentiment.analyzer.base import BaseAnalyzer
from kopi_sentiment.analyzer.openai import OpenAIAnalyzer
from kopi_sentiment.config.settings import settings
from kopi_sentiment.analyzer.models import OverallSentiment, Signal
from kopi_sentiment.analyzer.prompts import (
    WEEKLY_SUMMARY_SYSTEM_PROMPT,
    SIGNAL_DETECTION_SYSTEM_PROMPT,
)

logger = logging.getLogger(__name__)


class HybridAnalyzer(OpenAIAnalyzer):
    """Hybrid analyzer: OpenAI for extraction, Claude for synthesis.

    Uses gpt-4o-mini for the heavy lifting (quote extraction, intensity assessment)
    and Claude for the final synthesis steps (weekly summary, signal detection).
    """

    def __init__(
        self,
        openai_model: str | None = None,
        claude_model: str = "claude-sonnet-4-20250514",
    ):
        # Initialize OpenAI for extraction (parent class)
        super().__init__(model=openai_model)

        # Initialize Claude for synthesis
        self.claude_client = Anthropic(api_key=settings.anthropic_api_key)
        self.claude_model = claude_model

        logger.info(f"HybridAnalyzer initialized: OpenAI ({self.model}) + Claude ({self.claude_model})")

    def _call_claude(self, system_prompt: str, user_prompt: str) -> str:
        """Make a call to Claude API for synthesis tasks."""
        response = self.claude_client.messages.create(
            model=self.claude_model,
            max_tokens=settings.llm_max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return response.content[0].text

    def generate_weekly_summary(self, *args, **kwargs) -> OverallSentiment:
        """Override to use Claude for weekly summary generation."""
        # Store original _call_llm
        original_call_llm = self._call_llm

        # Temporarily replace with Claude
        self._call_llm = self._call_claude

        try:
            result = super().generate_weekly_summary(*args, **kwargs)
            logger.info("Weekly summary generated using Claude")
            return result
        finally:
            # Restore original
            self._call_llm = original_call_llm

    def detect_signals(self, *args, **kwargs) -> list[Signal]:
        """Override to use Claude for signal detection."""
        # Store original _call_llm
        original_call_llm = self._call_llm

        # Temporarily replace with Claude
        self._call_llm = self._call_claude

        try:
            result = super().detect_signals(*args, **kwargs)
            logger.info("Signal detection completed using Claude")
            return result
        finally:
            # Restore original
            self._call_llm = original_call_llm