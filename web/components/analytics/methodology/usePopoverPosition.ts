import { useState, useEffect, RefObject } from "react";

interface PopoverPosition {
  top: number;
  left: number;
}

interface UsePopoverPositionOptions {
  anchorRef: RefObject<HTMLElement | null> | undefined;
  isOpen: boolean;
  popoverWidth?: number;
  popoverHeight?: number;
  padding?: number;
}

/**
 * Hook to calculate popover position relative to an anchor element.
 * Positions above anchor by default, falls back to below if insufficient space.
 *
 * SRP: Only responsible for position calculation.
 */
export function usePopoverPosition({
  anchorRef,
  isOpen,
  popoverWidth = 384,
  popoverHeight = 400,
  padding = 8,
}: UsePopoverPositionOptions): PopoverPosition {
  const [position, setPosition] = useState<PopoverPosition>({ top: 0, left: 0 });

  useEffect(() => {
    if (!isOpen || !anchorRef?.current) return;

    const calculatePosition = (): PopoverPosition => {
      const anchor = anchorRef.current;
      if (!anchor) return { top: 0, left: 0 };

      const rect = anchor.getBoundingClientRect();

      // Center horizontally relative to anchor
      let left = rect.left + rect.width / 2 - popoverWidth / 2;
      // Position above anchor
      let top = rect.top - popoverHeight - padding;

      // Keep within horizontal viewport bounds
      left = Math.max(padding, left);
      left = Math.min(window.innerWidth - popoverWidth - padding, left);

      // If insufficient space above, show below
      if (top < padding) {
        top = rect.bottom + padding;
      }

      return { top, left };
    };

    const updatePosition = () => setPosition(calculatePosition());

    updatePosition();
    window.addEventListener("resize", updatePosition);
    window.addEventListener("scroll", updatePosition, true);

    return () => {
      window.removeEventListener("resize", updatePosition);
      window.removeEventListener("scroll", updatePosition, true);
    };
  }, [isOpen, anchorRef, popoverWidth, popoverHeight, padding]);

  return position;
}
