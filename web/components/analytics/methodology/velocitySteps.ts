import { MethodologyConfig } from "./types";

/**
 * Velocity z-score methodology explanation.
 *
 * OCP: Add new steps here without modifying modal component.
 */
export const velocityMethodology: MethodologyConfig = {
  id: "velocity-zscore",
  title: "How Velocity Z-Score Works",
  subtitle: "Understanding the rate of change in sentiment",
  steps: [
    {
      title: "Global Baseline",
      description:
        "First, we establish a baseline by looking at all quotes across all days and categories. This tells us what 'typical' engagement looks like.",
      formula: "global_mean = sum(all_upvotes) / count(all_quotes)",
      formulaBreakdown: [
        { variable: "global_mean", explanation: "Average upvotes per quote (32.31)" },
        { variable: "global_std", explanation: "Standard deviation of upvotes (72.60)" },
      ],
      example: {
        description: "From 3,327 historical quotes:",
        values: [
          { label: "Total upvotes", value: "107,535" },
          { label: "Total quotes", value: "3,327" },
        ],
        result: "mean = 32.31, std = 72.60",
      },
      plainEnglish:
        "We look at all past comments to understand what a 'normal' amount of upvotes looks like.",
    },
    {
      title: "Quote Scoring",
      description:
        "Each quote gets a score based on how its engagement compares to the baseline, plus a bonus for emotional intensity.",
      formula: "quote_score = engagement_z + intensity_z",
      formulaBreakdown: [
        {
          variable: "engagement_z",
          explanation: "(upvotes - global_mean) / global_std",
        },
        {
          variable: "intensity_z",
          explanation: "mild: -1.64, moderate: -0.49, strong: +0.71",
        },
      ],
      example: {
        description: 'Quote: "fuck me can we deport this guy" (641 upvotes, strong)',
        values: [
          { label: "engagement_z", value: "(641 - 32.31) / 72.60 = 8.38" },
          { label: "intensity_z", value: "0.71 (strong)" },
        ],
        result: "quote_score = 8.38 + 0.71 = 9.09",
      },
      plainEnglish:
        "Viral comments with strong emotions score higher. A comment with 641 upvotes is way above average, so it gets a high score.",
    },
    {
      title: "Daily Sum",
      description:
        "We add up all the quote scores for each emotion category to get a daily total. This represents the overall 'weight' of that emotion for the day.",
      formula: "zscore_sum = sum(all quote_scores for category)",
      example: {
        description: "Frustrations on Feb 2, 2026 (164 quotes):",
        values: [
          { label: "Quote 1", value: "9.09" },
          { label: "Quote 2", value: "4.77" },
          { label: "Quote 3", value: "1.24" },
          { label: "... + 161 more", value: "..." },
        ],
        result: "frustrations_zscore_sum = 75.07",
      },
      plainEnglish:
        "We combine all frustration scores into one number that represents 'how much frustration happened today, weighted by importance'.",
    },
    {
      title: "Velocity Calculation",
      description:
        "Velocity is simply how much the daily sum changed from yesterday. Positive means increasing, negative means decreasing.",
      formula: "velocity = today_zscore_sum - yesterday_zscore_sum",
      example: {
        description: "Frustrations change from Feb 1 to Feb 2:",
        values: [
          { label: "Today (Feb 2)", value: "75.07" },
          { label: "Yesterday (Feb 1)", value: "20.49" },
        ],
        result: "velocity = 75.07 - 20.49 = +54.58",
      },
      plainEnglish:
        "Frustration jumped by 54.58 points today compared to yesterday - a significant increase.",
    },
    {
      title: "Velocity Z-Score",
      description:
        "Finally, we compare today's velocity to historical velocities. This tells us if today's change is unusual.",
      formula: "velocity_zscore = (velocity - hist_mean) / hist_std",
      formulaBreakdown: [
        { variable: "hist_mean", explanation: "Average daily change over past 7 days" },
        { variable: "hist_std", explanation: "Standard deviation of daily changes" },
      ],
      example: {
        description: "Is +54.58 velocity unusual?",
        values: [
          { label: "Today's velocity", value: "+54.58" },
          { label: "Historical mean", value: "-2.15" },
          { label: "Historical std", value: "25.62" },
        ],
        result: "velocity_zscore = (54.58 - (-2.15)) / 25.62 = +2.21",
      },
      plainEnglish:
        "A z-score of +2.21 means today's increase is 2.2 standard deviations above normal - this only happens about 1-2% of the time. It's a statistically significant spike.",
    },
  ],
};
