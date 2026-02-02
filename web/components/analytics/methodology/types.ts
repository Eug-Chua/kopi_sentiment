/**
 * Types for methodology explanation modals.
 *
 * Following SOLID principles:
 * - ISP: Small, focused interface for step data
 * - DIP: Components depend on this abstraction, not concrete implementations
 */

export interface FormulaExample {
  label: string;
  value: string | number;
}

export interface MethodologyStep {
  /** Step title shown in header */
  title: string;
  /** Brief description of what this step does */
  description: string;
  /** Optional formula displayed in monospace */
  formula?: string;
  /** Optional breakdown of formula components */
  formulaBreakdown?: {
    variable: string;
    explanation: string;
  }[];
  /** Optional example calculation with real values */
  example?: {
    description: string;
    values: FormulaExample[];
    result: string;
  };
  /** Optional plain-English summary */
  plainEnglish?: string;
}

export interface MethodologyConfig {
  /** Unique identifier for this methodology */
  id: string;
  /** Display title for the modal */
  title: string;
  /** Brief subtitle explaining what metric this explains */
  subtitle: string;
  /** The steps in the methodology */
  steps: MethodologyStep[];
}
