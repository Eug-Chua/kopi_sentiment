"""Application config using Pydantic settings"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment"""

    # Reddit scraping
    reddit_base_url: str = "https://old.reddit.com"
    reddit_subreddit: list[str] = ['singapore', 'askSingapore', 'SingaporeRaw', 'singaporefi']
    reddit_user_agent: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    reddit_client_id: str = ""
    reddit_client_secret: str = ""

    # LLM settings
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    llm_provider: str = "hybrid"
    llm_max_tokens: int = 2048

    # Model configuration
    # Extraction model: used for quote extraction and intensity assessment (high volume)
    extraction_model: str = "claude-haiku-4-5-20251001"
    # Synthesis model: used for summaries, insights, signals (requires more reasoning)
    synthesis_model: str = "claude-sonnet-4-20250514"
    # Fallback model (OpenAI)
    openai_model: str = "gpt-4o-mini"

    # Legacy alias for backwards compatibility
    @property
    def claude_model(self) -> str:
        return self.synthesis_model

    # Scraper settings
    scraper_delay: float = 1.0
    posts_per_fetch: int = 25
    comments_per_post: int = 25

    # Pipeline settings - Weekly
    subreddit_delay_weekly: int = 60
    high_engagement_min_score_weekly: int = 20
    high_engagement_limit_weekly: int = 15

    # Pipeline settings - Daily
    subreddit_delay_daily: int = 30
    high_engagement_min_score_daily: int = 10
    high_engagement_limit_daily: int = 10
    report_retention_days: int = 30

    # Trend calculation
    trend_threshold_pct: float = 10.0

    # Parallel processing
    analysis_max_workers: int = 10  # Number of parallel LLM calls for post analysis

    # Storage paths
    data_path_weekly: str = "data/weekly"
    data_path_daily: str = "data/daily"
    web_data_path_weekly: str = "web/public/data/weekly"
    web_data_path_daily: str = "web/public/data/daily"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
