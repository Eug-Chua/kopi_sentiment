"""Hybrid analyzer using different models for extraction vs synthesis.

Follows the Dependency Inversion Principle:
- Models are configured via settings, not hardcoded
- Extraction and synthesis can use different providers/models
"""

import logging

from kopi_sentiment.analyzer.claude import ClaudeAnalyzer
from kopi_sentiment.config.settings import settings
from kopi_sentiment.analyzer.models import OverallSentiment, Signal, ThematicCluster

logger = logging.getLogger(__name__)


class HybridAnalyzer(ClaudeAnalyzer):
    """Hybrid analyzer: fast model for extraction, powerful model for synthesis.

    Default configuration (from settings):
    - Extraction: claude-haiku-4-5 (fast, cost-effective for high-volume quote extraction)
    - Synthesis: claude-sonnet-4 (better reasoning for summaries, insights, signals)

    Models can be overridden via constructor or environment variables.
    """

    def __init__(
        self,
        extraction_model: str | None = None,
        synthesis_model: str | None = None,
    ):
        """Initialize the hybrid analyzer.

        Args:
            extraction_model: Model for quote extraction/intensity (defaults to settings.extraction_model)
            synthesis_model: Model for summaries/insights (defaults to settings.synthesis_model)
        """
        # Use settings as defaults (Dependency Inversion)
        self._extraction_model = extraction_model or settings.extraction_model
        self._synthesis_model = synthesis_model or settings.synthesis_model

        # Initialize parent with extraction model
        super().__init__(model=self._extraction_model)

        logger.info(
            f"HybridAnalyzer initialized: "
            f"extraction={self._extraction_model}, synthesis={self._synthesis_model}"
        )

    def _call_synthesis_model(self, system_prompt: str, user_prompt: str) -> str:
        """Make a call using the synthesis model."""
        response = self.client.messages.create(
            model=self._synthesis_model,
            max_tokens=settings.llm_max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return response.content[0].text

    def _with_synthesis_model(self, method_name: str):
        """Decorator pattern: temporarily swap to synthesis model for a method call."""
        def wrapper(*args, **kwargs):
            original_call_llm = self._call_llm
            self._call_llm = self._call_synthesis_model
            try:
                method = getattr(super(HybridAnalyzer, self), method_name)
                result = method(*args, **kwargs)
                logger.info(f"{method_name} completed using synthesis model")
                return result
            finally:
                self._call_llm = original_call_llm
        return wrapper

    def generate_weekly_summary(self, *args, **kwargs) -> OverallSentiment:
        """Use synthesis model for weekly summary generation."""
        return self._with_synthesis_model("generate_weekly_summary")(*args, **kwargs)

    def detect_signals(self, *args, **kwargs) -> list[Signal]:
        """Use synthesis model for signal detection."""
        return self._with_synthesis_model("detect_signals")(*args, **kwargs)

    def detect_thematic_clusters(self, *args, **kwargs) -> list[ThematicCluster]:
        """Use synthesis model for thematic cluster detection."""
        return self._with_synthesis_model("detect_thematic_clusters")(*args, **kwargs)

    def generate_weekly_insights(self, *args, **kwargs):
        """Use synthesis model for weekly insights generation."""
        return self._with_synthesis_model("generate_weekly_insights")(*args, **kwargs)

    def cluster_themes(self, *args, **kwargs):
        """Use synthesis model for theme clustering."""
        return self._with_synthesis_model("cluster_themes")(*args, **kwargs)