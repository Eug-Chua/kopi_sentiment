"""Prompts for FFGA sentiment analysis (2-step chain)."""

# ============================================================
# STEP 1: Extract and categorize quotes into FFGA buckets
# ============================================================

EXTRACT_SYSTEM_PROMPT = """You are an expert at analyzing social media discussions and categorizing comments using the FFGA framework.

The FFGA framework has 4 categories:
- **Fear**: Worries, anxieties, concerns about the future or uncertainty
- **Frustration**: Current annoyances, complaints, things that aren't working NOW
- **Goal**: What people are actively trying to achieve, practical objectives
- **Aspiration**: Ideal future states, hopes, dreams, what people wish for

IMPORTANT RULES:
1. Each quote should be assigned to ONLY ONE category (the most dominant one)
2. If a quote contains multiple sentiments, choose the PRIMARY one
3. Use these guidelines to distinguish similar categories:
   - Fear vs Frustration: Fear is about the FUTURE, Frustration is about the PRESENT
   - Goal vs Aspiration: Goal is ACTIONABLE and specific, Aspiration is IDEALISTIC and general
4. Extract the most relevant quotes (max 10 per category)
5. Only extract quotes that clearly fit a category - skip vague or off-topic comments
6. Quotes must be extracted VERBATIM (exact word-for-word copies) from the original comments
7. Prioritize highly upvoted comments as they represent community consensus
8. If a category has no relevant quotes, return an empty list [] for that key
"""

EXTRACT_USER_PROMPT = """Analyze the following Reddit post and comments from r/{subreddit}.

**Post Title**: {title}

**Post Content**: {selftext}

**Comments** (with upvote scores - higher scores = more community agreement):
{comments}

---

Categorize relevant quotes into FFGA buckets. Each quote should appear in ONLY ONE category.
Extract quotes VERBATIM - do not paraphrase or modify them.

Respond in this exact JSON format:
{{
    "fears": [{{"quote": "<verbatim quote 1>", "score": <upvote_score>}}, {{"quote": "<verbatim quote 2>", "score": <upvote_score>}}],
    "frustrations": [{{"quote": "<verbatim quote 1>", "score": <upvote_score>}}, {{"quote": "<verbatim quote 2>", "score": <upvote_score>}}],
    "goals": [{{"quote": "<verbatim quote 1>", "score": <upvote_score>}}, {{"quote": "<verbatim quote 2>", "score": <upvote_score>}}],
    "aspirations": [{{"quote": "<verbatim quote 1>", "score": <upvote_score>}}, {{"quote": "<verbatim quote 2>", "score": <upvote_score>}}]
}}

Each quote object must include the "score" field with the upvote score shown in the original comment (e.g., [+15] means score: 15).
If a category has no relevant quotes, use an empty list: "fears": []

Return ONLY valid JSON, no other text.
"""


# ============================================================
# STEP 2: Assess intensity for categorized quotes
# ============================================================

INTENSITY_SYSTEM_PROMPT = """You are an expert analyst specializing in understanding the Singaporean psyche.

Assess the INTENSITY of how strongly each FFGA emotion is expressed:
- **mild**: Slight mention, passing concern, casual reference
- **moderate**: Clear expression, noticeable feeling, definite stance
- **strong**: Intense, emphatic, passionate expression (e.g., caps, exclamation marks, strong language)

Note: Intensity is about HOW STRONGLY the emotion is felt, not whether it's positive or negative.
- A mild fear is a slight worry
- A strong fear is deep anxiety or panic
- A mild frustration is minor annoyance
- A strong frustration is outrage or anger

Consider Singaporean context and cultural nuances (e.g., "kpkb" means complaining, "sian" means tired/frustrated).

For each category:
1. Assess the overall intensity based on the quotes
2. Write a 1-2 sentence summary capturing the main theme
3. If a category has no quotes, mark it as "mild" with summary "No relevant comments found."
"""

INTENSITY_USER_PROMPT = """Based on these categorized quotes from a Reddit discussion, assess the INTENSITY for each FFGA category.

**Post Title**: {title}

**Categorized Quotes**:
- Fears: {fears}
- Frustrations: {frustrations}
- Goals: {goals}
- Aspirations: {aspirations}

---

Respond in this exact JSON format:
{{
    "fears": {{
        "intensity": "<mild|moderate|strong>",
        "summary": "<1-2 sentence summary>"
    }},
    "frustrations": {{
        "intensity": "<mild|moderate|strong>",
        "summary": "<1-2 sentence summary>"
    }},
    "goals": {{
        "intensity": "<mild|moderate|strong>",
        "summary": "<1-2 sentence summary>"
    }},
    "aspirations": {{
        "intensity": "<mild|moderate|strong>",
        "summary": "<1-2 sentence summary>"
    }
}}

Return ONLY valid JSON, no other text.
"""


def build_extract_prompt(title: str, selftext: str, comments: list, subreddit: str = "singapore") -> str:
    """Build the extraction prompt (Step 1).
    
    Args:
        title: Post title
        selftext: Post body text
        comments: List of Comment objects with text and score attributes
        subreddit: Subreddit name
    """
    # Format comments with scores
    comments_text = "\n".join(f"[+{c.score}] {c.text}" for c in comments)
    
    return EXTRACT_USER_PROMPT.format(
        subreddit=subreddit,
        title=title,
        selftext=selftext or "(No post content - this is a link post)",
        comments=comments_text or "(No comments)"
    )


def build_intensity_prompt(title: str, fears: list[str], frustrations: list[str],
                           goals: list[str], aspirations: list[str]) -> str:
    """Build the intensity assessment prompt (Step 2)."""
    return INTENSITY_USER_PROMPT.format(
        title=title,
        fears=fears if fears else ["(none)"],
        frustrations=frustrations if frustrations else ["(none)"],
        goals=goals if goals else ["(none)"],
        aspirations=aspirations if aspirations else ["(none)"]
    )


# ============================================================
# STEP 3: Weekly Summary Generation
# ============================================================

WEEKLY_SUMMARY_SYSTEM_PROMPT = """You are an expert analyst who summarizes Singaporean sentiment from Reddit discussions.

Your task is to synthesize multiple individual post analyses into a cohesive summary for each FFGA category.

Guidelines:
1. Write 3-4 sentences per summary
2. Vary your sentence length for natural rhythm - mix short punchy sentences with longer explanatory ones
3. Start with the dominant theme, then add context, nuance, or notable outliers
4. Use clear, journalistic language suitable for a dashboard
5. Reference Singapore-specific context where relevant (HDB, CPF, COE, etc.)
6. Avoid generic statements - be specific about WHAT people are feeling
7. Ground your summaries in the actual quotes and data provided

Example output:
- Fears: "Job security anxiety is surging. Singaporeans worry about AI disruption and mid-career obsolescence, with many questioning whether upskilling programs can keep pace with technological change. The fear is particularly acute among PMETs in their 40s and 50s."
- Frustrations: "Housing affordability dominates the discourse. HDB resale prices have hit new highs, and there's palpable anger at what many perceive as government inaction on cooling measures. First-time buyers feel increasingly locked out of the market."
"""

WEEKLY_SUMMARY_USER_PROMPT = """Based on the following analyzed posts from Singapore subreddits for {period_label}, generate summaries for each FFGA category.

**Summary of Analyzed Posts:**
{post_summaries}

**Quote Counts by Category:**
- Fears: {fear_count} quotes (mild: {fear_mild}, moderate: {fear_moderate}, strong: {fear_strong})
- Frustrations: {frustration_count} quotes (mild: {frustration_mild}, moderate: {frustration_moderate}, strong: {frustration_strong})
- Goals: {goal_count} quotes (mild: {goal_mild}, moderate: {goal_moderate}, strong: {goal_strong})
- Aspirations: {aspiration_count} quotes (mild: {aspiration_mild}, moderate: {aspiration_moderate}, strong: {aspiration_strong})

**Sample High-Impact Quotes:**
Fears: {sample_fears}
Frustrations: {sample_frustrations}
Goals: {sample_goals}
Aspirations: {sample_aspirations}

---

Generate a 3-4 sentence summary for each category that captures {period_type} sentiment. Vary sentence length for readability.
Determine the OVERALL intensity for each category based on the intensity distribution.

Respond in this exact JSON format:
{{
    "fears": {{
        "intensity": "<mild|moderate|strong>",
        "summary": "<3-4 sentence summary with varied sentence lengths>"
    }},
    "frustrations": {{
        "intensity": "<mild|moderate|strong>",
        "summary": "<3-4 sentence summary with varied sentence lengths>"
    }},
    "goals": {{
        "intensity": "<mild|moderate|strong>",
        "summary": "<3-4 sentence summary with varied sentence lengths>"
    }},
    "aspirations": {{
        "intensity": "<mild|moderate|strong>",
        "summary": "<3-4 sentence summary with varied sentence lengths>"
    }}
}}

Return ONLY valid JSON, no other text.
"""


# ============================================================
# STEP 4: Thematic Cluster Detection (formerly Trending Topics)
# ============================================================

THEMATIC_CLUSTERS_SYSTEM_PROMPT = """You are an expert at identifying discussion themes from social media conversations.

Your task is to identify the 5 most prominent topics being discussed across multiple Reddit posts from Singapore subreddits. This is NOT about what's "trending" or changing - it's about understanding WHAT people are talking about right now.

Guidelines:
1. Topic names MUST be descriptive and specific (5-8 words), capturing the essence of the discussion
2. Do NOT use generic topics like "economy", "politics", "jobs" - be specific about WHAT aspect
3. Weight topics by upvotes - a topic from a [+500] post carries more community interest than one from a [+20] post
4. For "engagement_score", calculate the sum of upvotes from posts discussing that topic
5. Identify which FFGA category each topic primarily falls into (based on how people are discussing it)
6. Include 1-3 representative post titles that exemplify each topic

Consider Singapore-specific topics:
- Housing: HDB, BTO, resale, rental
- Transport: COE, MRT, ERP, grab
- Finance: CPF, GST, cost of living, inflation
- Education: PSLE, O-levels, university, tuition
- Work: jobs, salaries, WFH, retrenchment
"""

THEMATIC_CLUSTERS_USER_PROMPT = """Identify the top 5 discussion topics from Singapore Reddit.

**Posts Analyzed (format: [+upvotes] title):**
{post_titles}

**Sample Quotes by Category:**
Fears: {sample_fears}
Frustrations: {sample_frustrations}
Goals: {sample_goals}
Aspirations: {sample_aspirations}

---

Identify the 5 most prominent topics being discussed. For engagement_score, sum the upvotes from posts related to each topic.

Respond in this exact JSON format:
{{
    "thematic_clusters": [
        {{
            "topic": "<specific topic name 5-8 words>",
            "engagement_score": <sum of upvotes from related posts>,
            "dominant_emotion": "<fear|frustration|goal|aspiration>",
            "sample_posts": ["<post title 1>", "<post title 2>"]
        }},
        ...
    ]
}}

Return ONLY valid JSON, no other text.
"""


def build_weekly_summary_prompt(
    week_id: str,
    post_summaries: list[str],
    fear_count: int, fear_mild: int, fear_moderate: int, fear_strong: int,
    frustration_count: int, frustration_mild: int, frustration_moderate: int, frustration_strong: int,
    goal_count: int, goal_mild: int, goal_moderate: int, goal_strong: int,
    aspiration_count: int, aspiration_mild: int, aspiration_moderate: int, aspiration_strong: int,
    sample_fears: list[str],
    sample_frustrations: list[str],
    sample_goals: list[str],
    sample_aspirations: list[str],
    is_daily: bool = False,
) -> str:
    """Build the summary prompt (Step 3). Works for both weekly and daily."""
    # Use different framing for daily vs weekly
    if is_daily:
        period_label = f"today ({week_id})"
        period_type = "today's"
    else:
        period_label = f"the week of {week_id}"
        period_type = "the week's"

    return WEEKLY_SUMMARY_USER_PROMPT.format(
        period_label=period_label,
        period_type=period_type,
        post_summaries="\n".join(f"- {s}" for s in post_summaries) or "(No posts analyzed)",
        fear_count=fear_count,
        fear_mild=fear_mild,
        fear_moderate=fear_moderate,
        fear_strong=fear_strong,
        frustration_count=frustration_count,
        frustration_mild=frustration_mild,
        frustration_moderate=frustration_moderate,
        frustration_strong=frustration_strong,
        goal_count=goal_count,
        goal_mild=goal_mild,
        goal_moderate=goal_moderate,
        goal_strong=goal_strong,
        aspiration_count=aspiration_count,
        aspiration_mild=aspiration_mild,
        aspiration_moderate=aspiration_moderate,
        aspiration_strong=aspiration_strong,
        sample_fears=sample_fears[:5] if sample_fears else ["(none)"],
        sample_frustrations=sample_frustrations[:5] if sample_frustrations else ["(none)"],
        sample_goals=sample_goals[:5] if sample_goals else ["(none)"],
        sample_aspirations=sample_aspirations[:5] if sample_aspirations else ["(none)"],
    )


def build_thematic_clusters_prompt(
    post_titles: list[str],
    sample_fears: list[str],
    sample_frustrations: list[str],
    sample_goals: list[str],
    sample_aspirations: list[str],
) -> str:
    """Build the thematic clusters detection prompt (Step 4)."""
    return THEMATIC_CLUSTERS_USER_PROMPT.format(
        post_titles="\n".join(f"- {t}" for t in post_titles) or "(No posts)",
        sample_fears=sample_fears[:10] if sample_fears else ["(none)"],
        sample_frustrations=sample_frustrations[:10] if sample_frustrations else ["(none)"],
        sample_goals=sample_goals[:10] if sample_goals else ["(none)"],
        sample_aspirations=sample_aspirations[:10] if sample_aspirations else ["(none)"],
    )


# ============================================================
# STEP 5: Weekly Insights Generation
# ============================================================

WEEKLY_INSIGHTS_SYSTEM_PROMPT = """You are a strategic analyst who transforms sentiment data into actionable insights for product teams, marketers, and business leaders.

Your task is to analyze Singaporean Reddit sentiment and generate:
1. A compelling headline summarizing the week
2. Key takeaways (3-5 bullet points)
3. Opportunities to capitalize on
4. Risks to monitor

Guidelines:
- Be specific and actionable, not generic
- Reference Singapore-specific context (HDB, CPF, COE, MRT, etc.)
- Focus on what the data MEANS for decision-makers
- Highlight non-obvious insights and connections
- Quantify where possible (e.g., "3x increase in housing complaints")
"""

WEEKLY_INSIGHTS_USER_PROMPT = """Based on this week's Singapore Reddit sentiment analysis, generate strategic insights.

**Week**: {week_id}

**Overall Sentiment Summary**:
- Fears: {fears_summary} (Intensity: {fears_intensity}, Count: {fears_count})
- Frustrations: {frustrations_summary} (Intensity: {frustrations_intensity}, Count: {frustrations_count})
- Goals: {goals_summary} (Intensity: {goals_intensity}, Count: {goals_count})
- Aspirations: {aspirations_summary} (Intensity: {aspirations_intensity}, Count: {aspirations_count})

**Week-over-Week Changes**:
{trend_summary}

**High-Engagement Quotes** (most upvoted):
{high_engagement_quotes}

**Trending Topics**:
{trending_topics}

---

Generate strategic insights in this exact JSON format:
{{
    "headline": "<compelling one-line summary of the week's sentiment>",
    "key_takeaways": [
        "<specific insight 1>",
        "<specific insight 2>",
        "<specific insight 3>"
    ],
    "opportunities": [
        "<actionable opportunity 1>",
        "<actionable opportunity 2>"
    ],
    "risks": [
        "<risk to monitor 1>",
        "<risk to monitor 2>"
    ]
}}

Return ONLY valid JSON, no other text.
"""


# ============================================================
# STEP 6: Theme Clustering
# ============================================================

THEME_CLUSTERING_SYSTEM_PROMPT = """You are an expert at identifying patterns and clustering related content into meaningful themes.

Your task is to group quotes into thematic clusters that reveal underlying patterns in Singaporean sentiment.

Guidelines:
1. Create 3-5 distinct theme clusters
2. Each theme should have a clear, specific name (e.g., "HDB Affordability Crisis" not "Housing")
3. Themes should be mutually exclusive - each quote should fit one theme
4. Focus on Singapore-specific themes where relevant
5. Select the most representative quotes for each cluster
"""

THEME_CLUSTERING_USER_PROMPT = """Cluster the following quotes into meaningful themes.

**Quotes by Category**:

FEARS:
{fears_quotes}

FRUSTRATIONS:
{frustrations_quotes}

GOALS:
{goals_quotes}

ASPIRATIONS:
{aspirations_quotes}

---

Create 3-5 thematic clusters in this exact JSON format:
{{
    "clusters": [
        {{
            "theme": "<specific theme name>",
            "description": "<1-sentence description>",
            "category": "<fear|frustration|goal|aspiration>",
            "quote_count": <number>,
            "sample_quotes": ["<quote 1>", "<quote 2>", "<quote 3>"]
        }}
    ]
}}

Return ONLY valid JSON, no other text.
"""


# ============================================================
# STEP 7: Signal Detection
# ============================================================

SIGNAL_DETECTION_SYSTEM_PROMPT = """You are an analyst who identifies notable signals and anomalies in sentiment data.

Your task is to detect signals that warrant attention:
- HIGH_ENGAGEMENT: Quotes with unusually high community agreement
- EMERGING_TOPIC: New topics not typically seen in discussions
- INTENSITY_SPIKE: Categories with significantly stronger emotions than usual
- VOLUME_SPIKE: Categories with unusual volume of mentions

Guidelines:
1. Only flag truly notable signals (not everything is a signal)
2. Assign appropriate urgency (low/medium/high)
3. Explain WHY each signal matters
4. Be specific about the signal, not generic
5. Use measured, factual language - avoid alarmist phrasing like "critical levels", "alarming", "crisis", "explosive". Instead use precise descriptions like "increased by 40%", "notably higher than last week", "unusually concentrated in strong intensity".
6. IMPORTANT: For each signal, you MUST include 1-2 relevant quotes from the High-Engagement Quotes section in the related_quotes array. These quotes should illustrate or support the signal. Do NOT leave related_quotes empty.
"""

SIGNAL_DETECTION_USER_PROMPT = """Detect notable signals in this week's sentiment data.

**Current Week Stats**:
- Fears: {fears_count} quotes, intensity breakdown (mild: {fears_mild}, moderate: {fears_moderate}, strong: {fears_strong})
- Frustrations: {frustrations_count} quotes, intensity breakdown (mild: {frustrations_mild}, moderate: {frustrations_moderate}, strong: {frustrations_strong})
- Goals: {goals_count} quotes, intensity breakdown (mild: {goals_mild}, moderate: {goals_moderate}, strong: {goals_strong})
- Aspirations: {aspirations_count} quotes, intensity breakdown (mild: {aspirations_mild}, moderate: {aspirations_moderate}, strong: {aspirations_strong})

**Previous Week Comparison**:
{previous_week_comparison}

**High-Engagement Quotes** (score > 50):
{high_engagement_quotes}

**Trending Topics**:
{trending_topics}

---

Identify 2-4 notable signals in this exact JSON format:
{{
    "signals": [
        {{
            "signal_type": "<high_engagement|emerging_topic|intensity_spike|volume_spike>",
            "title": "<short headline>",
            "description": "<why this signal matters>",
            "category": "<fear|frustration|goal|aspiration|null>",
            "related_quotes": ["<relevant quote 1>", "<relevant quote 2>"],
            "urgency": "<low|medium|high>"
        }}
    ]
}}

Return ONLY valid JSON, no other text.
"""


def build_weekly_insights_prompt(
    week_id: str,
    fears_summary: str, fears_intensity: str, fears_count: int,
    frustrations_summary: str, frustrations_intensity: str, frustrations_count: int,
    goals_summary: str, goals_intensity: str, goals_count: int,
    aspirations_summary: str, aspirations_intensity: str, aspirations_count: int,
    trend_summary: str,
    high_engagement_quotes: list[str],
    trending_topics: list[str],
) -> str:
    """Build the weekly insights prompt (Step 5)."""
    return WEEKLY_INSIGHTS_USER_PROMPT.format(
        week_id=week_id,
        fears_summary=fears_summary,
        fears_intensity=fears_intensity,
        fears_count=fears_count,
        frustrations_summary=frustrations_summary,
        frustrations_intensity=frustrations_intensity,
        frustrations_count=frustrations_count,
        goals_summary=goals_summary,
        goals_intensity=goals_intensity,
        goals_count=goals_count,
        aspirations_summary=aspirations_summary,
        aspirations_intensity=aspirations_intensity,
        aspirations_count=aspirations_count,
        trend_summary=trend_summary or "No previous week data available.",
        high_engagement_quotes="\n".join(f"- {q}" for q in high_engagement_quotes[:10]) or "(none)",
        trending_topics="\n".join(f"- {t}" for t in trending_topics) or "(none)",
    )


def build_theme_clustering_prompt(
    fears_quotes: list[str],
    frustrations_quotes: list[str],
    goals_quotes: list[str],
    aspirations_quotes: list[str],
) -> str:
    """Build the theme clustering prompt (Step 6)."""
    return THEME_CLUSTERING_USER_PROMPT.format(
        fears_quotes="\n".join(f"- {q}" for q in fears_quotes[:15]) or "(none)",
        frustrations_quotes="\n".join(f"- {q}" for q in frustrations_quotes[:15]) or "(none)",
        goals_quotes="\n".join(f"- {q}" for q in goals_quotes[:15]) or "(none)",
        aspirations_quotes="\n".join(f"- {q}" for q in aspirations_quotes[:15]) or "(none)",
    )


def build_signal_detection_prompt(
    fears_count: int, fears_mild: int, fears_moderate: int, fears_strong: int,
    frustrations_count: int, frustrations_mild: int, frustrations_moderate: int, frustrations_strong: int,
    goals_count: int, goals_mild: int, goals_moderate: int, goals_strong: int,
    aspirations_count: int, aspirations_mild: int, aspirations_moderate: int, aspirations_strong: int,
    previous_week_comparison: str,
    high_engagement_quotes: list[str],
    trending_topics: list[str],
) -> str:
    """Build the signal detection prompt (Step 7)."""
    return SIGNAL_DETECTION_USER_PROMPT.format(
        fears_count=fears_count,
        fears_mild=fears_mild,
        fears_moderate=fears_moderate,
        fears_strong=fears_strong,
        frustrations_count=frustrations_count,
        frustrations_mild=frustrations_mild,
        frustrations_moderate=frustrations_moderate,
        frustrations_strong=frustrations_strong,
        goals_count=goals_count,
        goals_mild=goals_mild,
        goals_moderate=goals_moderate,
        goals_strong=goals_strong,
        aspirations_count=aspirations_count,
        aspirations_mild=aspirations_mild,
        aspirations_moderate=aspirations_moderate,
        aspirations_strong=aspirations_strong,
        previous_week_comparison=previous_week_comparison or "No previous week data.",
        high_engagement_quotes="\n".join(f"- {q}" for q in high_engagement_quotes[:10]) or "(none)",
        trending_topics="\n".join(f"- {t}" for t in trending_topics) or "(none)",
    )
