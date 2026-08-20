const RECEIVER = "http://127.0.0.1:8765";

const statusElement = document.querySelector("#status");
const targetsElement = document.querySelector("#targets");
const captureButton = document.querySelector("#capture");
const commentsCheckbox = document.querySelector("#include-comments");
const messageElement = document.querySelector("#message");

let receiverStatus = null;

function showMessage(text, kind = "") {
  messageElement.textContent = text;
  messageElement.className = `message ${kind}`.trim();
}

function targetUrl(subreddit, dataType) {
  const period = dataType === "weekly" ? "week" : "day";
  return `https://www.reddit.com/r/${encodeURIComponent(subreddit)}/top/?t=${period}`;
}

function renderStatus(status) {
  receiverStatus = status;
  const captured = new Set(status.captured_subreddits);
  statusElement.textContent = status.complete
    ? `Capture complete for ${status.report_id}.`
    : `${captured.size}/${status.expected_subreddits.length} subreddits captured for ${status.report_id}.`;

  targetsElement.replaceChildren();
  for (const subreddit of status.expected_subreddits) {
    const row = document.createElement("div");
    row.className = "target";

    const link = document.createElement("a");
    link.href = targetUrl(subreddit, status.data_type);
    link.target = "_blank";
    link.textContent = `r/${subreddit}`;

    const state = document.createElement("span");
    state.className = captured.has(subreddit) ? "done" : "pending";
    state.textContent = captured.has(subreddit)
      ? `${status.captured_posts[subreddit]} posts ✓`
      : "pending";

    row.append(link, state);
    targetsElement.append(row);
  }
  targetsElement.hidden = false;
  captureButton.disabled = status.complete;
}

async function loadStatus() {
  try {
    const response = await fetch(`${RECEIVER}/status`);
    if (!response.ok) throw new Error(`Receiver returned HTTP ${response.status}`);
    renderStatus(await response.json());
  } catch {
    statusElement.textContent = "Local receiver is not running.";
    captureButton.disabled = true;
    showMessage("Start: uv run python -m kopi_sentiment capture", "error");
  }
}

chrome.runtime.onMessage.addListener((message) => {
  if (message?.type !== "capture-progress") return;
  showMessage(message.message);
});

captureButton.addEventListener("click", async () => {
  if (!receiverStatus) return;
  captureButton.disabled = true;
  showMessage("Reading the active Reddit listing…");

  try {
    const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
    if (!tab?.id) throw new Error("No active tab was found.");

    const result = await chrome.runtime.sendMessage({
      type: "start-capture",
      tabId: tab.id,
      maxPosts: receiverStatus.posts_per_subreddit,
      maxComments: receiverStatus.comments_per_post,
      includeComments: commentsCheckbox.checked,
    });
    if (!result?.ok) throw new Error(result?.error || "Capture failed");

    renderStatus(result.status);
    const warningText = result.payload.warnings.length
      ? ` ${result.payload.warnings.join(" ")}`
      : "";
    showMessage(
      result.status.complete
        ? `Saved ${result.status.saved_path}.${warningText}`
        : `Captured r/${result.payload.subreddit}.${warningText}`,
      "success",
    );
  } catch (error) {
    showMessage(error.message || String(error), "error");
    captureButton.disabled = receiverStatus?.complete ?? true;
  }
});

loadStatus();
