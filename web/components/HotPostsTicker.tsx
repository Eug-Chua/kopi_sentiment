"use client";

import { PostAnalysis } from "@/types";

interface HotPostsTickerProps {
  posts: PostAnalysis[];
}

export function HotPostsTicker({ posts }: HotPostsTickerProps) {
  if (!posts || posts.length === 0) {
    return null;
  }

  // Filter out "START HERE" posts, take top 5 by score and duplicate for seamless loop
  const topPosts = [...posts]
    .filter((p) => !p.title.toLowerCase().includes("start here"))
    .sort((a, b) => b.score - a.score)
    .slice(0, 5);
  const tickerContent = [...topPosts, ...topPosts];

  return (
    <div className="bg-black/40 backdrop-blur-sm rounded-xl border border-white/[0.08] overflow-hidden">
      <div className="flex items-center">
        <div className="flex-1 overflow-hidden">
          <div className="ticker-wrapper">
            <div className="ticker-content">
              {tickerContent.map((post, i) => (
                <a
                  key={`${post.id}-${i}`}
                  href={post.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="ticker-item group"
                >
                  <span className="text-white/40">r/{post.subreddit}</span>
                  <span className="text-white/80 group-hover:text-[#FF4500] transition-colors">{post.title}</span>
                  <span className="text-white/30 text-xs">↑{post.score}</span>
                  <span className="text-white/30 text-xs">💬{post.num_comments}</span>
                  <span className="text-white/20 mx-4">|</span>
                </a>
              ))}
            </div>
          </div>
        </div>
      </div>
      <style jsx>{`
  .ticker-wrapper {
    display: flex;
    width: 100%;
    overflow-x: auto;
    scrollbar-width: none;
    -ms-overflow-style: none;
  }
  .ticker-wrapper::-webkit-scrollbar {
    display: none;
  }
  .ticker-content {
    display: flex;
    animation: ticker 80s linear infinite;
    white-space: nowrap;
    padding: 8px 0;
  }
  .ticker-item {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    text-decoration: none;
  }
  @keyframes ticker {
    0% {
      transform: translateX(0);
    }
    100% {
      transform: translateX(-50%);
    }
  }
  .ticker-wrapper:hover .ticker-content {
    animation-play-state: paused;
  }
`}</style>
    </div>
  );
}