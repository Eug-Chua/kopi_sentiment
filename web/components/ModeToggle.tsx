"use client";

import { ReportMode } from "@/types";

interface ModeToggleProps {
  mode: ReportMode;
  onModeChange: (mode: ReportMode) => void;
}

export function ModeToggle({ mode, onModeChange }: ModeToggleProps) {
  return (
    <div className="inline-flex rounded-full bg-zinc-800/50 p-1 border border-zinc-700">
      <button
        onClick={() => onModeChange("daily")}
        className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all ${
          mode === "daily"
            ? "bg-zinc-700 text-white"
            : "text-zinc-400 hover:text-zinc-200"
        }`}
      >
        Daily
      </button>
      <button
        onClick={() => onModeChange("weekly")}
        className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all ${
          mode === "weekly"
            ? "bg-zinc-700 text-white"
            : "text-zinc-400 hover:text-zinc-200"
        }`}
      >
        Weekly
      </button>
    </div>
  );
}