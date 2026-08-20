"""Browser-based Reddit fetch strategy (Playwright driving real Chrome).

Reddit's Aug 2026 login wall blocks plain HTTP clients (requests/curl) but
admits a real browser carrying a logged-in session. This strategy drives the
user's installed Chrome via Playwright against the same old.reddit.com JSON
endpoints as JsonRedditFetcher, reusing its URL builders and parsers so the
strategies cannot drift apart.

Design (mirrors reddit.py):
- BrowserRedditFetcher implements the RedditFetcher protocol - a new strategy
  added without modifying existing ones (OCP).
- ChromeSession owns browser lifecycle and navigation only (SRP); the fetcher
  receives it by injection and is testable with a fake (DIP).
- One process-wide ChromeSession is shared across per-subreddit scrapers so a
  pipeline run launches a single Chrome.

Requires a one-time manual login (persisted in the profile dir):
    python -m kopi_sentiment login
"""

import atexit
import json
import logging
from pathlib import Path

from kopi_sentiment.config.settings import settings
from kopi_sentiment.scraper.reddit import (
    Comment,
    RedditPost,
    listing_json_url,
    search_json_url,
    thread_json_url,
    _parse_listing_json,
    _parse_thread_comments_json,
    _parse_thread_selftext_json,
)

logger = logging.getLogger(__name__)

LOGIN_URL = "https://old.reddit.com/login"
SESSION_COOKIE = "reddit_session"


class BrowserSessionError(Exception):
    """The browser session could not produce the requested data (e.g. login wall)."""


class ChromeSession:
    """Owns a persistent Chrome context: launch, navigate, close (SRP).

    Uses the installed Chrome (channel="chrome") for a genuine browser
    fingerprint, with a persistent profile so the Reddit login survives
    across runs. Lazily launched on first navigation.
    """

    def __init__(self, profile_dir: str | None = None, headless: bool | None = None):
        self._profile_dir = Path(profile_dir or settings.browser_profile_dir).expanduser()
        self._headless = settings.browser_headless if headless is None else headless
        self._playwright = None
        self._context = None
        self._page = None

    def _ensure_started(self) -> None:
        if self._context is not None:
            return
        from playwright.sync_api import sync_playwright

        self._profile_dir.mkdir(parents=True, exist_ok=True)
        logger.info(
            f"Launching Chrome (headless={self._headless}, profile={self._profile_dir})"
        )
        self._playwright = sync_playwright().start()
        try:
            self._context = self._playwright.chromium.launch_persistent_context(
                str(self._profile_dir),
                channel="chrome",
                headless=self._headless,
                # Strip the two loudest automation tells Reddit's bot-detection
                # keys on: the navigator.webdriver flag and the enable-automation
                # switch. Makes the driven Chrome look like an ordinary one.
                args=["--disable-blink-features=AutomationControlled"],
                ignore_default_args=["--enable-automation"],
            )
        except Exception as e:
            self._playwright.stop()
            self._playwright = None
            if "existing browser session" in str(e):
                raise BrowserSessionError(
                    "The scraper profile is already in use by another Chrome - "
                    "likely a previous run that is still open or suspended. "
                    "Close it (pkill -f browser_profile) and retry."
                ) from e
            raise
        self._page = self._context.new_page()

    def get_json(self, url: str):
        """Navigate to a .json URL and return the parsed response body.

        Raises BrowserSessionError if Reddit serves the login wall or a
        non-JSON body, so callers fail loudly instead of parsing nothing.
        """
        self._ensure_started()
        response = self._page.goto(url, timeout=30_000)
        if response is None:
            raise BrowserSessionError(f"No response navigating to {url}")

        if "/login" in response.url:
            raise BrowserSessionError(
                "Reddit redirected to its login wall - the browser session is "
                "missing or expired. Run: python -m kopi_sentiment login"
            )

        body = response.text()
        try:
            return json.loads(body)
        except json.JSONDecodeError as e:
            raise BrowserSessionError(
                f"Expected JSON from {url} but got status {response.status} "
                f"with non-JSON body (starts with {body[:80]!r})"
            ) from e

    def open_page(self, url: str) -> None:
        """Navigate the session's page to a URL and leave it open (login flow)."""
        self._ensure_started()
        self._page.goto(url, timeout=60_000)

    def has_reddit_session(self) -> bool:
        """True if the profile currently holds a Reddit login cookie."""
        self._ensure_started()
        cookies = self._context.cookies("https://old.reddit.com")
        return any(c.get("name") == SESSION_COOKIE for c in cookies)

    def close(self) -> None:
        if self._context is not None:
            self._context.close()
            self._context = None
            self._page = None
        if self._playwright is not None:
            self._playwright.stop()
            self._playwright = None


_shared_session: ChromeSession | None = None


def get_shared_session() -> ChromeSession:
    """Process-wide ChromeSession so all subreddit scrapers share one Chrome."""
    global _shared_session
    if _shared_session is None:
        _shared_session = ChromeSession()
        atexit.register(_shared_session.close)
    return _shared_session


# ---- Browser Fetcher Strategy ----

class BrowserRedditFetcher:
    """Fetches Reddit data through a real Chrome session (RedditFetcher strategy)."""

    def __init__(self, session: ChromeSession | None = None):
        self._session = session or get_shared_session()

    def fetch_posts(self, subreddit: str, limit: int, sort: str, time_filter: str) -> list[RedditPost]:
        data = self._session.get_json(listing_json_url(subreddit, limit, sort, time_filter))
        return _parse_listing_json(data)

    def fetch_post_content(self, post: RedditPost) -> str:
        data = self._session.get_json(thread_json_url(post.url))
        return _parse_thread_selftext_json(data)

    def fetch_post_comments(self, post: RedditPost, limit: int) -> list[Comment]:
        data = self._session.get_json(thread_json_url(post.url, limit=limit))
        return _parse_thread_comments_json(data)

    def search_posts(self, subreddit: str, query: str, limit: int, sort: str, time_filter: str) -> list[RedditPost]:
        data = self._session.get_json(search_json_url(subreddit, query, limit, sort, time_filter))
        return _parse_listing_json(data)


# ---- One-time login flow ----

def run_login_flow() -> bool:
    """Open a headed Chrome on the persistent profile for a one-time manual login.

    The saved session is what the (headless) scraping runs reuse. Returns
    True if a Reddit session cookie is present afterwards.
    """
    session = ChromeSession(headless=False)
    try:
        session.open_page(LOGIN_URL)
        print("A Chrome window has opened on Reddit's login page.")
        print("Log in there (a throwaway account is fine), then return here.")
        input("Press Enter once you are logged in... ")

        if session.has_reddit_session():
            print("Login detected - session saved. Scraping runs will now reuse it.")
            return True
        print(f"No '{SESSION_COOKIE}' cookie found - the login may not have completed.")
        return False
    finally:
        session.close()
