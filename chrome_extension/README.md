# Kopi Sentiment Chrome Capture

This unpacked Manifest V3 extension extracts public post data from the Reddit
listing that is open in the active tab. When comment capture is enabled, it
opens each selected thread in an inactive tab, captures up to 25 rendered top
comments, and closes the tab. It sends the extracted JSON only to the Kopi
Sentiment receiver on `127.0.0.1:8765`; it never reads or exports cookies.

## Install once

1. Open `chrome://extensions` in Chrome.
2. Enable **Developer mode**.
3. Click **Load unpacked**.
4. Select this `chrome_extension` directory.
5. Pin **Kopi Sentiment Capture** to the toolbar.

After updating the extension files, click its **Reload** button on
`chrome://extensions` before capturing again.

## Capture a daily run

Start the receiver from the project root:

```bash
uv run python -m kopi_sentiment capture
```

Click each subreddit link shown by the extension, wait for the listing to load,
then click **Capture this subreddit**. Keep Chrome open while the toolbar badge
counts through the thread pages. Threads are processed sequentially with a
five-second pause; the inactive tabs close automatically.

After all configured subreddits have been captured, the receiver writes
`data/raw/daily/YYYY-MM-DD.json` and exits. Collection failures, if any, are
stored in the raw file's `collection_warnings` field.

Run the analysis using the command printed by the receiver.

To replace an earlier capture for the same day, start the receiver with
`--overwrite`. The previous file is not replaced until all subreddit captures
finish successfully.
