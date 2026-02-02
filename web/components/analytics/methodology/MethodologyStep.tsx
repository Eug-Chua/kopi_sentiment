"use client";

import { MethodologyStep as StepType } from "./types";

interface MethodologyStepProps {
  step: StepType;
}

/**
 * Renders a single methodology step with formula and example.
 *
 * SRP: Only responsible for displaying step content.
 */
export function MethodologyStep({ step }: MethodologyStepProps) {
  return (
    <div className="space-y-2">
      {/* Description */}
      <p className="text-[10px] sm:text-[11px] text-white/70 leading-relaxed">{step.description}</p>

      {/* Formula */}
      {step.formula && (
        <div className="bg-white/[0.03] border border-white/[0.08] rounded p-2">
          <p className="text-[8px] uppercase tracking-wider text-white/40 mb-1">
            Formula
          </p>
          <code className="text-emerald-400 font-mono text-[10px] sm:text-[11px] break-all">{step.formula}</code>
        </div>
      )}

      {/* Formula breakdown */}
      {step.formulaBreakdown && step.formulaBreakdown.length > 0 && (
        <div className="space-y-1">
          <p className="text-[8px] uppercase tracking-wider text-white/40">
            Where
          </p>
          <div className="space-y-0.5">
            {step.formulaBreakdown.map((item, idx) => (
              <div key={idx} className="flex items-start gap-1.5 text-[9px] sm:text-[10px]">
                <code className="text-amber-400 font-mono shrink-0">
                  {item.variable}
                </code>
                <span className="text-white/50">=</span>
                <span className="text-white/60">{item.explanation}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Example calculation */}
      {step.example && (
        <div className="bg-emerald-500/[0.05] border border-emerald-500/20 rounded p-2">
          <p className="text-[8px] uppercase tracking-wider text-emerald-400/70 mb-1.5">
            Example
          </p>
          <p className="text-[9px] sm:text-[10px] text-white/60 mb-1.5">{step.example.description}</p>
          <div className="space-y-0.5 mb-1.5">
            {step.example.values.map((val, idx) => (
              <div key={idx} className="flex items-center gap-1.5 text-[9px] sm:text-[10px]">
                <span className="text-white/50">{val.label}:</span>
                <span className="text-white/80 font-mono">{val.value}</span>
              </div>
            ))}
          </div>
          <div className="pt-1.5 border-t border-emerald-500/20">
            <span className="text-[9px] sm:text-[10px] text-white/50">Result: </span>
            <code className="text-emerald-400 font-mono text-[9px] sm:text-[10px]">
              {step.example.result}
            </code>
          </div>
        </div>
      )}

      {/* Plain English summary */}
      {step.plainEnglish && (
        <div className="flex items-start gap-1.5 text-[9px] sm:text-[10px] bg-white/[0.02] rounded p-2">
          <span className="text-amber-400 shrink-0">TL;DR:</span>
          <span className="text-white/60 italic">{step.plainEnglish}</span>
        </div>
      )}
    </div>
  );
}
