"""Reddit scaper using webscraping (fallback when API not available)"""

import time
from datetime import datetime
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup

class RedditPost(BaseModel):
    """Represents a Reddit post"""
    id: str
    title: str
    url: str
    score: int
    num_comments: int
    created_at: datetime
    selftext: str = ""