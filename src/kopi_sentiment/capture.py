"""Receive user-triggered Reddit captures from the local Chrome extension.

The receiver deliberately binds to loopback and accepts browser requests only
from Chrome extension origins. It never receives cookies or credentials; the
extension sends only public post/comment fields extracted from the active tab.
"""

from __future__ import annotations

import json
import logging
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from kopi_sentiment.config.settings import settings
from kopi_sentiment.scraper.reddit import Comment, RedditPost
from kopi_sentiment.storage.json_storage import RawDataStorage

logger = logging.getLogger(__name__)

MAX_REQUEST_BYTES = 5 * 1024 * 1024


class CaptureValidationError(ValueError):
    """The extension sent a malformed or unexpected capture."""


def _canonical_subreddit(value: Any, expected: dict[str, str]) -> str:
    if not isinstance(value, str):
        raise CaptureValidationError("subreddit must be a string")
    normalized = value.strip().removeprefix("r/")
    canonical = expected.get(normalized.casefold())
    if canonical is None:
        allowed = ", ".join(expected.values())
        raise CaptureValidationError(
            f"Unexpected subreddit r/{normalized}; expected one of: {allowed}"
        )
    return canonical


def _reddit_permalink(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CaptureValidationError("post URL is required")
    parsed = urlparse(value.strip())
    host = (parsed.hostname or "").casefold()
    if host != "reddit.com" and not host.endswith(".reddit.com"):
        raise CaptureValidationError("post URL must point to reddit.com")
    if "/comments/" not in parsed.path:
        raise CaptureValidationError("post URL must be a Reddit comment-thread permalink")
    return value.strip()


def _post_id(value: Any, url: str) -> str:
    raw = str(value or "").strip()
    if raw.startswith("t3_"):
        raw = raw[3:]
    if not raw:
        parts = urlparse(url).path.split("/comments/", 1)
        if len(parts) == 2:
            raw = parts[1].split("/", 1)[0]
    if not raw or not raw.replace("_", "").isalnum():
        raise CaptureValidationError("post ID is missing or invalid")
    return f"t3_{raw}"


def _integer(value: Any, *, default: int = 0, non_negative: bool = False) -> int:
    if value in (None, ""):
        return default
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise CaptureValidationError(f"Expected an integer, got {value!r}") from exc
    return max(0, result) if non_negative else result


def _captured_post(
    data: Any,
    subreddit: str,
    comments_per_post: int,
) -> RedditPost:
    if not isinstance(data, dict):
        raise CaptureValidationError("each post must be a JSON object")

    title = str(data.get("title") or "").strip()
    if not title:
        raise CaptureValidationError("post title is required")

    url = _reddit_permalink(data.get("url"))
    post_id = _post_id(data.get("id"), url)

    created_at = data.get("created_at") or datetime.now(timezone.utc).isoformat()
    try:
        created = datetime.fromisoformat(str(created_at).replace("Z", "+00:00"))
    except ValueError as exc:
        raise CaptureValidationError(f"Invalid post timestamp: {created_at!r}") from exc

    comments: list[Comment] = []
    seen_comments: set[str] = set()
    raw_comments = data.get("comments") or []
    if not isinstance(raw_comments, list):
        raise CaptureValidationError("post comments must be a list")
    for raw_comment in raw_comments:
        if not isinstance(raw_comment, dict):
            continue
        text = str(raw_comment.get("text") or "").strip()
        dedupe_key = " ".join(text.split()).casefold()
        if not text or dedupe_key in seen_comments:
            continue
        seen_comments.add(dedupe_key)
        comments.append(
            Comment(text=text, score=_integer(raw_comment.get("score")))
        )
        if len(comments) >= comments_per_post:
            break

    return RedditPost(
        id=post_id,
        subreddit=subreddit,
        title=title,
        url=url,
        score=_integer(data.get("score")),
        num_comments=_integer(data.get("num_comments"), non_negative=True),
        created_at=created,
        selftext=str(data.get("selftext") or "").strip(),
        comments=comments,
    )


class CaptureSession:
    """Collect one browser capture per configured subreddit and save raw data."""

    def __init__(
        self,
        report_id: str,
        data_type: str,
        expected_subreddits: list[str],
        posts_per_subreddit: int,
        storage: RawDataStorage,
        comments_per_post: int | None = None,
    ):
        if data_type not in {"daily", "weekly"}:
            raise ValueError("data_type must be 'daily' or 'weekly'")
        if not expected_subreddits:
            raise ValueError("at least one subreddit is required")
        if posts_per_subreddit < 1:
            raise ValueError("posts_per_subreddit must be positive")

        self.report_id = report_id
        self.data_type = data_type
        self.expected_subreddits = list(expected_subreddits)
        self.posts_per_subreddit = posts_per_subreddit
        self.comments_per_post = comments_per_post or settings.comments_per_post
        self.storage = storage
        self.saved_path: Path | None = None
        self._expected = {name.casefold(): name for name in expected_subreddits}
        self._captures: dict[str, list[RedditPost]] = {}
        self._warnings: dict[str, list[str]] = {}
        self._lock = threading.Lock()

    def status(self) -> dict[str, Any]:
        with self._lock:
            return self._status_unlocked()

    def _status_unlocked(self) -> dict[str, Any]:
        captured = [
            subreddit
            for subreddit in self.expected_subreddits
            if subreddit in self._captures
        ]
        remaining = [
            subreddit
            for subreddit in self.expected_subreddits
            if subreddit not in self._captures
        ]
        return {
            "report_id": self.report_id,
            "data_type": self.data_type,
            "posts_per_subreddit": self.posts_per_subreddit,
            "comments_per_post": self.comments_per_post,
            "expected_subreddits": self.expected_subreddits,
            "captured_subreddits": captured,
            "remaining_subreddits": remaining,
            "captured_posts": {
                subreddit: len(posts) for subreddit, posts in self._captures.items()
            },
            "warnings": dict(self._warnings),
            "complete": not remaining,
            "saved_path": str(self.saved_path) if self.saved_path else None,
        }

    def add_capture(self, payload: Any) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise CaptureValidationError("capture payload must be a JSON object")

        subreddit = _canonical_subreddit(payload.get("subreddit"), self._expected)
        raw_posts = payload.get("posts")
        if not isinstance(raw_posts, list) or not raw_posts:
            raise CaptureValidationError("capture must contain at least one post")

        posts: list[RedditPost] = []
        seen_ids: set[str] = set()
        for raw_post in raw_posts:
            post = _captured_post(raw_post, subreddit, self.comments_per_post)
            if post.id in seen_ids:
                continue
            seen_ids.add(post.id)
            posts.append(post)
            if len(posts) >= self.posts_per_subreddit:
                break

        if not posts:
            raise CaptureValidationError("capture did not contain any valid posts")

        raw_warnings = payload.get("warnings") or []
        warnings = [str(item) for item in raw_warnings if str(item).strip()]

        with self._lock:
            self._captures[subreddit] = posts
            self._warnings[subreddit] = warnings
            status = self._status_unlocked()
            if status["complete"] and self.saved_path is None:
                all_posts = [
                    post
                    for expected in self.expected_subreddits
                    for post in self._captures[expected]
                ]
                self.saved_path = self.storage.save_raw_scrape(
                    report_id=self.report_id,
                    posts=all_posts,
                    subreddits=self.expected_subreddits,
                    source_mode="browser_capture",
                    collection_warnings={
                        subreddit: warnings
                        for subreddit, warnings in self._warnings.items()
                        if warnings
                    },
                )
                status = self._status_unlocked()
            return status


class CaptureHTTPServer(ThreadingHTTPServer):
    """HTTP server carrying the capture-session state."""

    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address: tuple[str, int], session: CaptureSession):
        super().__init__(address, CaptureRequestHandler)
        self.capture_session = session


class CaptureRequestHandler(BaseHTTPRequestHandler):
    """Small JSON-only loopback API used by the unpacked Chrome extension."""

    server: CaptureHTTPServer

    def log_message(self, format: str, *args: Any) -> None:
        logger.debug("Capture receiver: " + format, *args)

    def _extension_origin(self) -> str | None:
        origin = self.headers.get("Origin", "")
        if origin.startswith("chrome-extension://"):
            return origin
        return None

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        origin = self._extension_origin()
        if origin:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.end_headers()
        self.wfile.write(encoded)

    def do_OPTIONS(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        origin = self._extension_origin()
        if not origin:
            self._send_json(403, {"error": "Only Chrome extension origins are allowed"})
            return
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "600")
        self.send_header("Vary", "Origin")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        if self.path != "/status":
            self._send_json(404, {"error": "Not found"})
            return
        if self.headers.get("Origin") and not self._extension_origin():
            self._send_json(403, {"error": "Only Chrome extension origins are allowed"})
            return
        self._send_json(200, self.server.capture_session.status())

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        if self.path != "/capture":
            self._send_json(404, {"error": "Not found"})
            return
        if not self._extension_origin():
            self._send_json(403, {"error": "Only Chrome extension origins are allowed"})
            return
        if "application/json" not in self.headers.get("Content-Type", ""):
            self._send_json(415, {"error": "Content-Type must be application/json"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_json(400, {"error": "Invalid Content-Length"})
            return
        if length < 1 or length > MAX_REQUEST_BYTES:
            self._send_json(413, {"error": "Capture payload is empty or too large"})
            return

        try:
            payload = json.loads(self.rfile.read(length))
            status = self.server.capture_session.add_capture(payload)
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Request body is not valid JSON"})
            return
        except CaptureValidationError as exc:
            self._send_json(400, {"error": str(exc)})
            return

        self._send_json(200, status)
        if status["complete"]:
            threading.Thread(target=self.server.shutdown, daemon=True).start()


def run_capture_server(
    *,
    report_id: str,
    data_type: str,
    expected_subreddits: list[str],
    posts_per_subreddit: int,
    port: int = 8765,
    overwrite: bool = False,
    storage: RawDataStorage | None = None,
) -> Path | None:
    """Run the loopback receiver until every configured subreddit is captured."""
    storage = storage or RawDataStorage(data_type=data_type)
    if storage.raw_exists(report_id) and not overwrite:
        raise FileExistsError(
            f"Raw data already exists for {report_id}; use --overwrite to replace it"
        )

    session = CaptureSession(
        report_id=report_id,
        data_type=data_type,
        expected_subreddits=expected_subreddits,
        posts_per_subreddit=posts_per_subreddit,
        storage=storage,
    )
    server = CaptureHTTPServer(("127.0.0.1", port), session)

    logger.info(
        "Browser capture receiver listening at http://127.0.0.1:%s (%s)",
        server.server_port,
        ", ".join(f"r/{name}" for name in expected_subreddits),
    )
    logger.info("Open each subreddit listing in Chrome and click the Kopi Capture extension")
    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        logger.info("Capture cancelled; partial data was not saved")
    finally:
        server.server_close()

    return session.saved_path
