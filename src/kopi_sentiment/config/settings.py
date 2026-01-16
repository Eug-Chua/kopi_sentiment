"""Application config using Pydantic settings"""

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings loaded from environment"""

    # reddit scraping
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
    claude_model: str = "claude-sonnet-4-20250514"     
    openai_model: str = "gpt-4o-mini"              
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()