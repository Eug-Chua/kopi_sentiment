import { MethodologyConfig } from "./types";

/**
 * Composite score methodology explanation - from first principles.
 *
 * OCP: Add new steps here without modifying modal component.
 */
export const compositeMethodology: MethodologyConfig = {
  id: "composite-score",
  title: "How Sentiment Score Works",
  subtitle: "From upvotes to overall mood",
  steps: [
    {
      title: "Quote Engagement",
      description:
        "Each quote has an upvote count from Reddit. We normalize this against our historical baseline to get an engagement z-score.",
      formula: "engagement_z = (upvotes - mean) / std",
      formulaBreakdown: [
        { variable: "upvotes", explanation: "Reddit score for the quote" },
        { variable: "mean", explanation: "32.31 (historical average)" },
        { variable: "std", explanation: "72.60 (historical spread)" },
      ],
      example: {
        description: "A quote with 150 upvotes:",
        values: [
          { label: "upvotes", value: "150" },
          { label: "mean", value: "32.31" },
          { label: "std", value: "72.60" },
        ],
        result: "(150 - 32.31) / 72.60 = +1.62σ",
      },
      plainEnglish:
        "High upvotes = the community strongly agrees with this sentiment.",
    },
    {
      title: "Quote Intensity",
      description:
        "LLM classifies each quote's emotional intensity (mild, moderate, strong). We convert this to a z-score.",
      formulaBreakdown: [
        { variable: "mild", explanation: "-1.64σ (bottom 5%)" },
        { variable: "moderate", explanation: "-0.49σ (bottom 31%)" },
        { variable: "strong", explanation: "+0.71σ (top 24%)" },
      ],
      example: {
        description: "A strongly emotional quote:",
        values: [
          { label: "Intensity", value: "strong" },
        ],
        result: "intensity_z = +0.71σ",
      },
      plainEnglish:
        "Strong emotions carry more weight than mild observations.",
    },
    {
      title: "Quote Score",
      description:
        "Each quote's final score combines engagement and intensity. Viral + intense = high impact.",
      formula: "quote_score = engagement_z + intensity_z",
      example: {
        description: "A viral, strongly emotional quote:",
        values: [
          { label: "engagement_z", value: "+1.62" },
          { label: "intensity_z", value: "+0.71" },
        ],
        result: "quote_score = 1.62 + 0.71 = +2.33",
      },
      plainEnglish:
        "A quote that's both popular AND emotionally charged has high impact.",
    },
    {
      title: "Daily Category Totals",
      description:
        "We sum all quote scores for each emotion category (fears, frustrations, optimism) to get daily totals.",
      formula: "category_zscore_sum = Σ(quote_scores)",
      example: {
        description: "Today's category totals:",
        values: [
          { label: "Fears", value: "-17.77" },
          { label: "Frustrations", value: "75.07" },
          { label: "Optimism", value: "-34.93" },
        ],
        result: "3 daily sentiment scores",
      },
      plainEnglish:
        "Positive = above-average activity. Negative = quieter than usual.",
    },
    {
      title: "Composite Score",
      description:
        "The final score: optimism minus (fears + frustrations). Positive = net bullish. Negative = net bearish.",
      formula: "composite = optimism - (fears + frustrations)",
      example: {
        description: "Today's overall sentiment:",
        values: [
          { label: "Optimism", value: "-34.93" },
          { label: "Fears + Frust", value: "57.30" },
        ],
        result: "-34.93 - 57.30 = -92.23 (bearish)",
      },
      plainEnglish:
        "Score of -92 means frustration significantly outweighs optimism today.",
    },
  ],
};
