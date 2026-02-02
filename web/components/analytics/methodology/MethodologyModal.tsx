"use client";

import { useState, useCallback, useEffect } from "react";
import { createPortal } from "react-dom";
import { MethodologyConfig } from "./types";
import { MethodologyStep } from "./MethodologyStep";
import { usePopoverPosition } from "./usePopoverPosition";

interface MethodologyModalProps {
  config: MethodologyConfig;
  isOpen: boolean;
  onClose: () => void;
  anchorRef?: React.RefObject<HTMLButtonElement | null>;
}

/**
 * Reusable stepper popover for explaining methodology.
 *
 * SOLID principles:
 * - SRP: Only handles modal UI and step navigation (position delegated to hook)
 * - OCP: New methodologies added via config, not code changes
 * - DIP: Depends on MethodologyConfig abstraction
 */
export function MethodologyModal({ config, isOpen, onClose, anchorRef }: MethodologyModalProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [mounted, setMounted] = useState(false);
  const totalSteps = config.steps.length;

  // Delegate position calculation to specialized hook (SRP)
  const position = usePopoverPosition({ anchorRef, isOpen: isOpen && mounted });

  // Mount portal after hydration
  useEffect(() => {
    setMounted(true);
  }, []);

  const goNext = useCallback(() => {
    if (currentStep < totalSteps - 1) {
      setCurrentStep((s) => s + 1);
    }
  }, [currentStep, totalSteps]);

  const goPrev = useCallback(() => {
    if (currentStep > 0) {
      setCurrentStep((s) => s - 1);
    }
  }, [currentStep]);

  const handleClose = useCallback(() => {
    setCurrentStep(0);
    onClose();
  }, [onClose]);

  // Handle keyboard navigation
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "ArrowRight" || e.key === "Enter") {
        if (currentStep < totalSteps - 1) {
          goNext();
        } else {
          handleClose();
        }
      } else if (e.key === "ArrowLeft") {
        goPrev();
      } else if (e.key === "Escape") {
        handleClose();
      }
    },
    [currentStep, totalSteps, goNext, goPrev, handleClose]
  );

  if (!isOpen || !mounted) return null;

  const step = config.steps[currentStep];
  const isFirstStep = currentStep === 0;
  const isLastStep = currentStep === totalSteps - 1;

  const modalContent = (
    <div
      className="fixed inset-0 z-[9999] pointer-events-none"
      onKeyDown={handleKeyDown}
      tabIndex={0}
    >
      {/* Transparent click-away area */}
      <div
        className="absolute inset-0 pointer-events-auto"
        onClick={handleClose}
      />

      {/* Popover - positioned near anchor */}
      <div
        className="fixed w-[calc(100vw-1rem)] sm:w-96 max-h-[70vh] bg-[#0a0a0a] border border-white/[0.12] rounded-lg shadow-2xl shadow-black/50 overflow-hidden pointer-events-auto"
        style={{
          top: position.top,
          left: position.left,
        }}
      >
        {/* Header - compact */}
        <div className="px-3 sm:px-4 py-2.5 border-b border-white/[0.06]">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-medium text-white">{config.title}</h2>
              <p className="text-[10px] text-white/40 mt-0.5">{config.subtitle}</p>
            </div>
            <button
              onClick={handleClose}
              className="p-1 hover:bg-white/[0.05] rounded transition-colors"
              aria-label="Close"
            >
              <svg
                className="w-4 h-4 text-white/40"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
        </div>

        {/* Step indicator - compact */}
        <div className="px-3 sm:px-4 py-2 border-b border-white/[0.04] bg-white/[0.01]">
          <div className="flex items-center justify-between">
            <span className="text-[10px] text-white/50">
              Step {currentStep + 1}/{totalSteps}
            </span>
            <span className="text-[10px] font-medium text-white/70">{step.title}</span>
          </div>
          {/* Progress bar */}
          <div className="mt-1.5 h-0.5 bg-white/[0.05] rounded-full overflow-hidden">
            <div
              className="h-full bg-emerald-500/60 rounded-full transition-all duration-300"
              style={{ width: `${((currentStep + 1) / totalSteps) * 100}%` }}
            />
          </div>
        </div>

        {/* Content - compact padding */}
        <div className="px-3 sm:px-4 py-3 max-h-[55vh] overflow-y-auto">
          <MethodologyStep step={step} />
        </div>

        {/* Footer with navigation - compact */}
        <div className="px-3 sm:px-4 py-2.5 border-t border-white/[0.06] bg-white/[0.01]">
          <div className="flex items-center justify-between">
            <button
              onClick={goPrev}
              disabled={isFirstStep}
              className={`px-2.5 py-1 text-[10px] rounded transition-colors ${
                isFirstStep
                  ? "text-white/20 cursor-not-allowed"
                  : "text-white/60 hover:text-white bg-white/[0.05] hover:bg-white/[0.08]"
              }`}
            >
              Back
            </button>

            <div className="flex items-center gap-1">
              {config.steps.map((_, idx) => (
                <button
                  key={idx}
                  onClick={() => setCurrentStep(idx)}
                  className={`w-1.5 h-1.5 rounded-full transition-colors ${
                    idx === currentStep
                      ? "bg-emerald-500"
                      : idx < currentStep
                      ? "bg-emerald-500/40"
                      : "bg-white/20"
                  }`}
                  aria-label={`Go to step ${idx + 1}`}
                />
              ))}
            </div>

            <button
              onClick={isLastStep ? handleClose : goNext}
              className="px-2.5 py-1 text-[10px] font-medium rounded bg-emerald-600 hover:bg-emerald-500 text-white transition-colors"
            >
              {isLastStep ? "Done" : "Next"}
            </button>
          </div>
          <p className="text-[9px] text-white/30 text-center mt-2 hidden sm:block">
            Use arrow keys to navigate
          </p>
        </div>
      </div>
    </div>
  );

  // Render via portal to ensure it's above all other content
  return createPortal(modalContent, document.body);
}
