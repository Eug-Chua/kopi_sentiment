"""Tests for the user-triggered Chrome capture receiver."""

import http.client
import json
import threading
from pathlib import Path

import pytest

from kopi_sentiment.capture import (
    CaptureHTTPServer,
    CaptureSession,
    CaptureValidationError,
    run_capture_server,
)
from kopi_sentiment.storage.json_storage import RawDataStorage


def capture_payload(subreddit: str, post_id: str = "abc123") -> dict:
    return {
        "subreddit": subreddit,
        "source_url": f"https://www.reddit.com/r/{subreddit}/top/?t=day",
        "warnings": ["Recent-comment feed returned HTTP 429"],
        "posts": [
            {
                "id": post_id,
                "subreddit": subreddit,
                "title": f"A post in {subreddit}",
                "url": f"https://www.reddit.com/r/{subreddit}/comments/{post_id}/a_post/",
                "score": "42",
                "num_comments": "3",
                "created_at": "2026-08-20T10:00:00Z",
                "selftext": "Post body",
                "comments": [
                    {"text": " First comment ", "score": "5"},
                    {"text": "First   comment", "score": 99},
                    {"text": "Second comment", "score": -2},
                ],
            }
        ],
    }


def test_capture_session_saves_raw_data_after_all_subreddits(tmp_path):
    storage = RawDataStorage(base_path=tmp_path, data_type="daily")
    session = CaptureSession(
        report_id="2026-08-20",
        data_type="daily",
        expected_subreddits=["singapore", "askSingapore"],
        posts_per_subreddit=10,
        comments_per_post=25,
        storage=storage,
    )

    first = session.add_capture(capture_payload("Singapore"))

    assert first["complete"] is False
    assert first["captured_subreddits"] == ["singapore"]
    assert not storage.raw_exists("2026-08-20")

    second = session.add_capture(capture_payload("askSingapore", "def456"))

    assert second["complete"] is True
    assert second["saved_path"] == str(tmp_path / "2026-08-20.json")
    raw = storage.load_raw_scrape("2026-08-20")
    assert raw["source_mode"] == "browser_capture"
    assert raw["collection_warnings"] == {
        "singapore": ["Recent-comment feed returned HTTP 429"],
        "askSingapore": ["Recent-comment feed returned HTTP 429"],
    }
    assert raw["subreddits"] == ["singapore", "askSingapore"]
    assert raw["total_posts"] == 2
    assert raw["total_comments"] == 4
    assert raw["posts"][0]["id"] == "t3_abc123"
    assert raw["posts"][0]["created_at"] == "2026-08-20T10:00:00+00:00"
    assert raw["posts"][0]["comments"] == [
        {"text": "First comment", "score": 5},
        {"text": "Second comment", "score": -2},
    ]


def test_capture_session_rejects_unexpected_or_non_reddit_data(tmp_path):
    session = CaptureSession(
        report_id="2026-08-20",
        data_type="daily",
        expected_subreddits=["singapore"],
        posts_per_subreddit=10,
        storage=RawDataStorage(base_path=tmp_path, data_type="daily"),
    )

    with pytest.raises(CaptureValidationError, match="Unexpected subreddit"):
        session.add_capture(capture_payload("notSingapore"))

    payload = capture_payload("singapore")
    payload["posts"][0]["url"] = "https://example.com/comments/abc123"
    with pytest.raises(CaptureValidationError, match="reddit.com"):
        session.add_capture(payload)


def test_capture_http_server_requires_extension_origin_and_shuts_down(tmp_path):
    session = CaptureSession(
        report_id="2026-08-20",
        data_type="daily",
        expected_subreddits=["singapore"],
        posts_per_subreddit=10,
        storage=RawDataStorage(base_path=tmp_path, data_type="daily"),
    )
    server = CaptureHTTPServer(("127.0.0.1", 0), session)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=2)
    body = json.dumps(capture_payload("singapore"))

    connection.request(
        "POST",
        "/capture",
        body=body,
        headers={"Content-Type": "application/json"},
    )
    forbidden = connection.getresponse()
    assert forbidden.status == 403
    forbidden.read()

    connection.request(
        "POST",
        "/capture",
        body=body,
        headers={
            "Content-Type": "application/json",
            "Origin": "chrome-extension://abcdefghijklmnop",
        },
    )
    accepted = connection.getresponse()
    response = json.loads(accepted.read())
    assert accepted.status == 200
    assert accepted.getheader("Access-Control-Allow-Origin") == "chrome-extension://abcdefghijklmnop"
    assert response["complete"] is True

    thread.join(timeout=2)
    server.server_close()
    connection.close()
    assert not thread.is_alive()
    assert (tmp_path / "2026-08-20.json").exists()


def test_capture_server_does_not_overwrite_raw_data_without_flag(tmp_path):
    storage = RawDataStorage(base_path=tmp_path, data_type="daily")
    (tmp_path / "2026-08-20.json").write_text("{}", encoding="utf-8")

    with pytest.raises(FileExistsError, match="--overwrite"):
        run_capture_server(
            report_id="2026-08-20",
            data_type="daily",
            expected_subreddits=["singapore"],
            posts_per_subreddit=10,
            port=0,
            storage=storage,
        )


def test_extension_manifest_has_minimal_permissions():
    manifest_path = Path(__file__).parents[1] / "chrome_extension" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["manifest_version"] == 3
    assert set(manifest["permissions"]) == {"activeTab", "scripting"}
    assert set(manifest["host_permissions"]) == {
        "http://127.0.0.1:8765/*",
        "https://*.reddit.com/*",
    }
    assert manifest["background"] == {"service_worker": "background.js"}
    assert "cookies" not in manifest["permissions"]
    assert "history" not in manifest["permissions"]
