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
# STEP 2: Assess sentiment for categorized quotes
# ============================================================

SENTIMENT_SYSTEM_PROMPT = """You are an expert sentiment analyst specializing in understanding the Singaporean psyche.

Assess the sentiment of categorized quotes using this scale:
- **strong_positive**: Very optimistic, hopeful, enthusiastic
- **positive**: Generally positive, satisfied, content  
- **mixed**: Neutral, balanced, or conflicting views
- **negative**: Dissatisfied, concerned, unhappy
- **strong_negative**: Very pessimistic, angry, distressed

Consider Singaporean context and cultural nuances (e.g., "kpkb" means complaining, "sian" means tired/frustrated).

For each category:
1. Assess the overall sentiment based on the quotes
2. Write a 1-2 sentence summary capturing the main theme
3. If a category has no quotes, mark it as "mixed" with summary "No relevant comments found."
"""

SENTIMENT_USER_PROMPT = """Based on these categorized quotes from a Reddit discussion, assess the sentiment for each FFGA category.

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
        "sentiment": "<strong_positive|positive|mixed|negative|strong_negative>",
        "summary": "<1-2 sentence summary>"
    }},
    "frustrations": {{
        "sentiment": "<strong_positive|positive|mixed|negative|strong_negative>",
        "summary": "<1-2 sentence summary>"
    }},
    "goals": {{
        "sentiment": "<strong_positive|positive|mixed|negative|strong_negative>",
        "summary": "<1-2 sentence summary>"
    }},
    "aspirations": {{
        "sentiment": "<strong_positive|positive|mixed|negative|strong_negative>",
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


def build_sentiment_prompt(title: str, fears: list[str], frustrations: list[str], 
                           goals: list[str], aspirations: list[str]) -> str:
    """Build the sentiment assessment prompt (Step 2)."""
    return SENTIMENT_USER_PROMPT.format(
        title=title,
        fears=fears if fears else ["(none)"],
        frustrations=frustrations if frustrations else ["(none)"],
        goals=goals if goals else ["(none)"],
        aspirations=aspirations if aspirations else ["(none)"]
    )
