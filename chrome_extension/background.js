const RECEIVER = "http://127.0.0.1:8765";
const THREAD_RENDER_DELAY_MS = 2500;
const BETWEEN_THREADS_DELAY_MS = 5000;
const THREAD_LOAD_TIMEOUT_MS = 30000;

let captureInProgress = false;

function sleep(milliseconds) {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

async function publishProgress(current, total, message) {
  const badge = total ? `${current}/${total}` : "";
  await chrome.action.setBadgeBackgroundColor({color: "#8b4513"});
  await chrome.action.setBadgeText({text: badge});
  try {
    await chrome.runtime.sendMessage({
      type: "capture-progress",
      current,
      total,
      message,
    });
  } catch {
    // The popup may be closed; the action badge still shows progress.
  }
}

function waitForTabComplete(tabId) {
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      chrome.tabs.onUpdated.removeListener(listener);
      reject(new Error("Timed out waiting for the Reddit thread to load"));
    }, THREAD_LOAD_TIMEOUT_MS);

    function listener(updatedTabId, changeInfo) {
      if (updatedTabId !== tabId || changeInfo.status !== "complete") return;
      clearTimeout(timeout);
      chrome.tabs.onUpdated.removeListener(listener);
      resolve();
    }

    chrome.tabs.onUpdated.addListener(listener);
    chrome.tabs.get(tabId).then((tab) => {
      if (tab.status === "complete") {
        clearTimeout(timeout);
        chrome.tabs.onUpdated.removeListener(listener);
        resolve();
      }
    }).catch((error) => {
      clearTimeout(timeout);
      chrome.tabs.onUpdated.removeListener(listener);
      reject(error);
    });
  });
}

function redditThreadUrl(value) {
  const url = new URL(value);
  url.searchParams.set("sort", "top");
  url.hash = "";
  return url.href;
}

async function extractRedditListing(maxPosts) {
  function parseCompactNumber(value) {
    if (value === null || value === undefined) return 0;
    const normalized = String(value).trim().toLowerCase().replaceAll(",", "");
    const match = normalized.match(/-?\d+(?:\.\d+)?/);
    if (!match) return 0;
    let result = Number(match[0]);
    if (normalized.includes("k")) result *= 1_000;
    if (normalized.includes("m")) result *= 1_000_000;
    return Math.round(result);
  }

  function firstAttribute(element, names) {
    for (const name of names) {
      const value = element.getAttribute?.(name);
      if (value) return value;
    }
    return "";
  }

  function firstText(element, selectors) {
    for (const selector of selectors) {
      const node = element.querySelector?.(selector);
      const value = node?.innerText?.trim() || node?.textContent?.trim();
      if (value) return value;
    }
    return "";
  }

  function absoluteRedditPermalink(value) {
    if (!value) return "";
    try {
      const url = new URL(value, location.origin);
      const host = url.hostname.toLowerCase();
      const isReddit = host === "reddit.com" || host.endsWith(".reddit.com");
      if (!isReddit || !url.pathname.includes("/comments/")) return "";
      url.hash = "";
      return url.href;
    } catch {
      return "";
    }
  }

  function postPermalink(element) {
    const candidates = [
      firstAttribute(element, ["permalink", "data-permalink"]),
      element.querySelector?.('a[data-click-id="comments"]')?.href,
      element.querySelector?.("a.comments")?.href,
      element.querySelector?.('a[href*="/comments/"]')?.href,
    ];
    return candidates.map(absoluteRedditPermalink).find(Boolean) || "";
  }

  function normalizePostId(value, url) {
    let id = String(value || "").replace(/^t3_/, "").trim();
    if (!id && url) {
      id = new URL(url).pathname.match(/\/comments\/([^/]+)/)?.[1] || "";
    }
    return id ? `t3_${id}` : "";
  }

  function isoTimestamp(element) {
    const value = firstAttribute(element, [
      "created-timestamp",
      "data-timestamp",
      "datetime",
    ]) || element.querySelector?.("time")?.getAttribute("datetime");
    if (!value) return new Date().toISOString();
    const parsed = new Date(value);
    return Number.isNaN(parsed.getTime()) ? new Date().toISOString() : parsed.toISOString();
  }

  function parsePost(element, fallbackSubreddit) {
    const url = postPermalink(element);
    const id = normalizePostId(
      firstAttribute(element, ["id", "post-id", "data-fullname"]),
      url,
    );
    const title = firstAttribute(element, ["post-title", "data-title"]) || firstText(element, [
      '[slot="title"]',
      "a.title",
      "h1",
      "h2",
      "h3",
    ]);
    const rawSubreddit = firstAttribute(element, [
      "subreddit-prefixed-name",
      "subreddit-name",
      "data-subreddit",
    ]).replace(/^r\//i, "");
    const scoreValue = firstAttribute(element, ["score", "data-score"]) || firstText(element, [
      '[data-testid="post-vote-count"]',
      ".score",
    ]);
    const commentsValue = firstAttribute(element, [
      "comment-count",
      "data-comments-count",
    ]) || firstText(element, [
      'a[data-click-id="comments"]',
      "a.comments",
    ]);
    const selftext = firstText(element, [
      '[slot="text-body"]',
      '[data-post-click-location="text-body"]',
      ".expando .md",
      ".usertext-body .md",
    ]);

    if (!id || !title || !url) return null;
    return {
      id,
      subreddit: rawSubreddit || fallbackSubreddit,
      title,
      url,
      score: parseCompactNumber(scoreValue),
      num_comments: Math.max(0, parseCompactNumber(commentsValue)),
      created_at: isoTimestamp(element),
      selftext,
      comments: [],
    };
  }

  const hostname = location.hostname.toLowerCase();
  const isReddit = hostname === "reddit.com" || hostname.endsWith(".reddit.com");
  if (!isReddit) throw new Error("The active tab is not a Reddit page.");

  const listingMatch = location.pathname.match(
    /^\/r\/([^/]+)(?:\/(?:top|hot|new|rising))?\/?$/i,
  );
  if (!listingMatch) {
    throw new Error("Open a subreddit listing page, not an individual thread.");
  }
  const subreddit = decodeURIComponent(listingMatch[1]);
  const warnings = [];
  if (!/\/top\/?$/i.test(location.pathname)) {
    warnings.push("This is not the subreddit top listing; ranking may differ.");
  }

  let elements = Array.from(document.querySelectorAll("shreddit-post"));
  if (!elements.length) {
    elements = Array.from(document.querySelectorAll('div.thing[data-type="link"]'));
  }
  if (!elements.length) elements = Array.from(document.querySelectorAll("article"));

  const posts = [];
  const seenIds = new Set();
  for (const element of elements) {
    const post = parsePost(element, subreddit);
    if (!post || seenIds.has(post.id)) continue;
    if (post.subreddit.toLowerCase() !== subreddit.toLowerCase()) continue;
    seenIds.add(post.id);
    posts.push(post);
    if (posts.length >= maxPosts) break;
  }

  if (!posts.length) {
    throw new Error(
      "No Reddit posts were found. Wait for the listing to load, scroll once, and retry.",
    );
  }
  if (posts.length < maxPosts) {
    warnings.push(`Only ${posts.length}/${maxPosts} posts were rendered on this page.`);
  }

  return {
    subreddit,
    source_url: location.href,
    captured_at: new Date().toISOString(),
    posts,
    warnings,
  };
}

async function extractRedditThread(maxComments) {
  function parseCompactNumber(value) {
    if (value === null || value === undefined) return 0;
    const normalized = String(value).trim().toLowerCase().replaceAll(",", "");
    const match = normalized.match(/-?\d+(?:\.\d+)?/);
    if (!match) return 0;
    let result = Number(match[0]);
    if (normalized.includes("k")) result *= 1_000;
    if (normalized.includes("m")) result *= 1_000_000;
    return Math.round(result);
  }

  function firstAttribute(element, names) {
    for (const name of names) {
      const value = element?.getAttribute?.(name);
      if (value) return value;
    }
    return "";
  }

  function firstText(element, selectors) {
    for (const selector of selectors) {
      const node = element?.querySelector?.(selector);
      const value = node?.innerText?.trim() || node?.textContent?.trim();
      if (value) return value;
    }
    return "";
  }

  function normalizePostId(value) {
    let id = String(value || "").replace(/^t3_/, "").trim();
    if (!id) id = location.pathname.match(/\/comments\/([^/]+)/)?.[1] || "";
    return id ? `t3_${id}` : "";
  }

  const pageText = document.body?.innerText?.toLowerCase() || "";
  if (pageText.includes("blocked by network security") || pageText.includes("you've been blocked")) {
    throw new Error("Reddit returned its network-security block page");
  }
  if (/\/login\/?$/i.test(location.pathname)) {
    throw new Error("Reddit redirected the thread to its login page");
  }

  const commentArea = document.querySelector("shreddit-comment, .commentarea");
  if (commentArea) {
    commentArea.scrollIntoView({block: "start"});
    await new Promise((resolve) => setTimeout(resolve, 1500));
  }

  const postElement = document.querySelector("shreddit-post, div.thing[data-type='link']");
  const post = {
    id: normalizePostId(firstAttribute(postElement, ["id", "post-id", "data-fullname"])),
    score: parseCompactNumber(firstAttribute(postElement, ["score", "data-score"]) || firstText(postElement, [
      '[data-testid="post-vote-count"]',
      ".score",
    ])),
    num_comments: Math.max(0, parseCompactNumber(
      firstAttribute(postElement, ["comment-count", "data-comments-count"]),
    )),
    selftext: firstText(postElement, [
      '[slot="text-body"]',
      '[data-post-click-location="text-body"]',
      ".expando .md",
      ".usertext-body .md",
    ]),
  };

  let elements = Array.from(document.querySelectorAll("shreddit-comment"));
  if (!elements.length) {
    elements = Array.from(document.querySelectorAll("div.thing[data-type='comment']"));
  }
  if (!elements.length) {
    elements = Array.from(document.querySelectorAll('[data-testid="comment"]'));
  }

  const comments = [];
  const seen = new Set();
  for (const element of elements) {
    const text = firstText(element, [
      '[slot="comment"]',
      '[slot="comment-content"]',
      'div[id$="-comment-rtjson-content"]',
      ".usertext-body .md",
      ".md",
    ]).replace(/\s+/g, " ").trim();
    const dedupeKey = text.toLowerCase();
    if (!text || text === "[deleted]" || text === "[removed]" || seen.has(dedupeKey)) {
      continue;
    }
    seen.add(dedupeKey);
    const scoreValue = firstAttribute(element, ["score", "data-score"]) || firstText(element, [
      '[data-testid="comment-vote-count"]',
      "faceplate-number",
      ".score.unvoted",
      ".score",
    ]);
    comments.push({text, score: parseCompactNumber(scoreValue)});
    if (comments.length >= maxComments) break;
  }

  return {post, comments};
}

async function captureSubreddit({tabId, maxPosts, maxComments, includeComments}) {
  const listingResult = await chrome.scripting.executeScript({
    target: {tabId},
    func: extractRedditListing,
    args: [maxPosts],
  });
  const payload = listingResult[0]?.result;
  if (!payload) throw new Error("The Reddit listing returned no capture data");

  if (includeComments) {
    let consecutiveFailures = 0;
    for (let index = 0; index < payload.posts.length; index += 1) {
      const post = payload.posts[index];
      if (post.num_comments <= 0) continue;

      await publishProgress(
        index + 1,
        payload.posts.length,
        `Reading comments ${index + 1}/${payload.posts.length}: ${post.title}`,
      );

      let threadTab = null;
      try {
        threadTab = await chrome.tabs.create({url: redditThreadUrl(post.url), active: false});
        await waitForTabComplete(threadTab.id);
        await sleep(THREAD_RENDER_DELAY_MS);

        const threadResult = await chrome.scripting.executeScript({
          target: {tabId: threadTab.id},
          func: extractRedditThread,
          args: [maxComments],
        });
        const thread = threadResult[0]?.result;
        if (!thread) throw new Error("Thread returned no capture data");
        if (thread.post.id && thread.post.id !== post.id) {
          throw new Error(`Thread ID mismatch: expected ${post.id}, got ${thread.post.id}`);
        }

        if (thread.post.selftext) post.selftext = thread.post.selftext;
        if (thread.post.score || !post.score) post.score = thread.post.score;
        if (thread.post.num_comments) post.num_comments = thread.post.num_comments;
        post.comments = thread.comments;
        if (!thread.comments.length && post.num_comments > 0) {
          payload.warnings.push(`${post.id}: no rendered comments were found.`);
        }
        consecutiveFailures = 0;
      } catch (error) {
        consecutiveFailures += 1;
        payload.warnings.push(`${post.id}: ${error.message || String(error)}`);
        if (consecutiveFailures >= 2) {
          payload.warnings.push("Stopped thread capture after two consecutive failures.");
          break;
        }
      } finally {
        if (threadTab?.id) {
          try {
            await chrome.tabs.remove(threadTab.id);
          } catch {
            // The tab may already have closed.
          }
        }
      }

      if (index < payload.posts.length - 1) await sleep(BETWEEN_THREADS_DELAY_MS);
    }
  }

  await publishProgress(0, 0, `Saving r/${payload.subreddit}…`);
  const response = await fetch(`${RECEIVER}/capture`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(payload),
  });
  const status = await response.json();
  if (!response.ok) throw new Error(status.error || `Receiver returned HTTP ${response.status}`);
  return {status, payload};
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.type !== "start-capture") return false;
  if (captureInProgress) {
    sendResponse({ok: false, error: "A capture is already in progress"});
    return false;
  }

  captureInProgress = true;
  captureSubreddit(message)
    .then((result) => sendResponse({ok: true, ...result}))
    .catch((error) => sendResponse({ok: false, error: error.message || String(error)}))
    .finally(async () => {
      captureInProgress = false;
      await chrome.action.setBadgeText({text: ""});
    });
  return true;
});
