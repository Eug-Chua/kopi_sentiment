"""OpenAI implementation of the sentiment analyzer."""

from openai import OpenAI
from kopi_sentiment.analyzer.base import BaseAnalyzer
from kopi_sentiment.config.settings import settings

class OpenAIAnalyzer(BaseAnalyzer):
    """Sentiment analyzer using OpenAI API."""

    def __init__(self, model: str | None = None):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = model or settings.openai_model

    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=settings.llm_max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content
