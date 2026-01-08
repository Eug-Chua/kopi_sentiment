"""Claude implmentaiton of the sentiment analyzer"""

from anthropic import Anthropic

from kopi_sentiment.analyzer.base import BaseAnalyzer
from kopi_sentiment.config.settings import settings


class ClaudeAnalyzer(BaseAnalyzer):
    """Sentiment analyzer using Claude API."""

    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.model = model

    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Make a call to Claude API."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=settings.llm_max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return response.content[0].text