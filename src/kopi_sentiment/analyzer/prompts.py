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
    "fears": ["<verbatim quote 1>", "<verbatim quote 2>"],
    "frustrations": ["<verbatim quote 1>", "<verbatim quote 2>"],
    "goals": ["<verbatim quote 1>", "<verbatim quote 2>"],
    "aspirations": ["<verbatim quote 1>", "<verbatim quote 2>"]
}}

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
    }}
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

Your task is to synthesize multiple individual post analyses into a cohesive 2-sentence summary for each FFGA category.

Guidelines:
1. Each summary must be EXACTLY 2 sentences
2. First sentence: State the dominant theme/concern for this category
3. Second sentence: Provide context, nuance, or notable outliers
4. Use clear, journalistic language suitable for a dashboard
5. Reference Singapore-specific context where relevant (HDB, CPF, COE, etc.)
6. Avoid generic statements - be specific about WHAT people are feeling
7. Ground your summaries in the actual quotes and data provided

Example output:
- Fears: "Singaporeans are expressing growing anxiety about job security amid global AI disruption. Many worry about mid-career obsolescence and the ability to upskill fast enough."
- Frustrations: "Housing affordability continues to dominate frustrations, with HDB resale prices hitting new highs. There is palpable anger at perceived government inaction on cooling measures."
"""

WEEKLY_SUMMARY_USER_PROMPT = """Based on the following analyzed posts from Singapore subreddits for the week of {week_id}, generate 2-sentence summaries for each FFGA category.

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

Generate a 2-sentence summary for each category that captures the week's sentiment.
Determine the OVERALL intensity for each category based on the intensity distribution.

Respond in this exact JSON format:
{{
    "fears": {{
        "intensity": "<mild|moderate|strong>",
        "summary": "<2-sentence summary>"
    }},
    "frustrations": {{
        "intensity": "<mild|moderate|strong>",
        "summary": "<2-sentence summary>"
    }},
    "goals": {{
        "intensity": "<mild|moderate|strong>",
        "summary": "<2-sentence summary>"
    }},
    "aspirations": {{
        "intensity": "<mild|moderate|strong>",
        "summary": "<2-sentence summary>"
    }}
}}

Return ONLY valid JSON, no other text.
"""


# ============================================================
# STEP 4: Trending Topics Detection
# ============================================================

TRENDING_TOPICS_SYSTEM_PROMPT = """You are an expert at identifying trending topics and themes from social media discussions.

Your task is to identify the 5 most prominent topics being discussed across multiple Reddit posts from Singapore subreddits.

Guidelines:
1. Identify specific, concrete topics (e.g., "HDB Resale Prices", "AI Job Displacement", "COE Prices")
2. Do NOT use generic topics like "economy" or "politics" - be specific
3. Count approximate mentions across all posts
4. Identify which FFGA category each topic primarily falls into
5. Assess if sentiment is improving, stable, or worsening compared to typical discussions

Consider Singapore-specific topics:
- Housing: HDB, BTO, resale, rental
- Transport: COE, MRT, ERP, grab
- Finance: CPF, GST, cost of living, inflation
- Education: PSLE, O-levels, university, tuition
- Work: jobs, salaries, WFH, retrenchment
"""

TRENDING_TOPICS_USER_PROMPT = """Identify the top 5 trending topics from this week's Singapore Reddit discussions.

**Posts Analyzed:**
{post_titles}

**Sample Quotes by Category:**
Fears: {sample_fears}
Frustrations: {sample_frustrations}
Goals: {sample_goals}
Aspirations: {sample_aspirations}

---

Identify the 5 most prominent topics being discussed.

Respond in this exact JSON format:
{{
    "trending_topics": [
        {{
            "topic": "<specific topic name>",
            "mentions": <approximate count>,
            "dominant_emotion": "<fear|frustration|goal|aspiration>",
            "sentiment_shift": "<improving|stable|worsening>"
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
) -> str:
    """Build the weekly summary prompt (Step 3)."""
    return WEEKLY_SUMMARY_USER_PROMPT.format(
        week_id=week_id,
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


def build_trending_topics_prompt(
    post_titles: list[str],
    sample_fears: list[str],
    sample_frustrations: list[str],
    sample_goals: list[str],
    sample_aspirations: list[str],
) -> str:
    """Build the trending topics detection prompt (Step 4)."""
    return TRENDING_TOPICS_USER_PROMPT.format(
        post_titles="\n".join(f"- {t}" for t in post_titles) or "(No posts)",
        sample_fears=sample_fears[:10] if sample_fears else ["(none)"],
        sample_frustrations=sample_frustrations[:10] if sample_frustrations else ["(none)"],
        sample_goals=sample_goals[:10] if sample_goals else ["(none)"],
        sample_aspirations=sample_aspirations[:10] if sample_aspirations else ["(none)"],
    )
