# engines/ai_engine.py
#
# Hugging Face Inference API wrapper.
# Provides two capabilities:
#   1. generate_plan_explanation()  — natural language summary of a study plan
#   2. suggest_subject_priorities() — AI-ranked subject order with reasoning
#
# Model: google/flan-t5-base (instruction-tuned, fast, free tier compatible)
# All prompts are structured so the model returns focused, bounded responses.
# This module never reads from or writes to the database directly.

import os
import requests
from dotenv import load_dotenv

from dotenv import load_dotenv
import os
load_dotenv(dotenv_path=os.path.join('/home/rs/projects/study_planner/api_key.env'))

HF_API_KEY  = os.getenv("HF_API_KEY")
MODEL_ID    = "google/flan-t5-base"
API_URL     = f"https://api-inference.huggingface.co/models/{MODEL_ID}"

# Fallback model if flan-t5-base is cold (takes ~20s to warm up on free tier)
FALLBACK_MODEL_ID = "google/flan-t5-small"
FALLBACK_URL      = f"https://api-inference.huggingface.co/models/{FALLBACK_MODEL_ID}"

HEADERS = {"Authorization": f"Bearer {HF_API_KEY}"}

# ── Core request function ──────────────────────────────────────────────────────
def _query(prompt: str, max_new_tokens: int = 200, retries: int = 2) -> str:
    """
    Sends a prompt to the Hugging Face Inference API.
    Handles model loading delays (503) with a single retry on the fallback model.
    Returns the generated text string or raises on persistent failure.
    """
    if not HF_API_KEY:
        raise EnvironmentError(
            "HF_API_KEY not found. Add it to your .env file: HF_API_KEY=hf_..."
        )

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": max_new_tokens,
            "temperature":    0.7,
            "do_sample":      True,
            "repetition_penalty": 1.3,
        },
        "options": {
            "wait_for_model": True,   # blocks until model is warm, avoids 503
            "use_cache":      False,
        }
    }

    for attempt, url in enumerate([API_URL, FALLBACK_URL]):
        try:
            response = requests.post(url, headers=HEADERS, json=payload, timeout=30)

            if response.status_code == 200:
                result = response.json()
                # flan-t5 returns [{"generated_text": "..."}]
                if isinstance(result, list) and result:
                    return result[0].get("generated_text", "").strip()
                return str(result).strip()

            elif response.status_code == 503:
                # Model still loading — wait_for_model should handle this
                # but fall through to fallback on second attempt
                if attempt < retries - 1:
                    continue
                raise RuntimeError(
                    "Model is unavailable. The free tier may be overloaded. "
                    "Try again in 30 seconds."
                )

            elif response.status_code == 401:
                raise PermissionError(
                    "Invalid HF_API_KEY. Check your .env file."
                )

            else:
                raise RuntimeError(
                    f"API returned {response.status_code}: {response.text[:200]}"
                )

        except requests.exceptions.Timeout:
            if attempt < retries - 1:
                continue
            raise RuntimeError(
                "Request timed out. The model may be cold-starting. Try again."
            )

    raise RuntimeError("All API attempts failed.")


# ── Feature 1: Plan explanation ────────────────────────────────────────────────
def generate_plan_explanation(plan: dict, subjects: list, phase: str) -> str:
    """
    Takes a generated plan dict and returns a natural language explanation
    of why the hours were allocated the way they were.

    plan:     output of generate_daily_plan()
    subjects: list of subject dicts with name, difficulty, days_until_exam
    phase:    current system phase string
    """
    # Build a structured subject summary for the prompt
    subject_lines = "\n".join([
        f"- {s['name']}: difficulty {s['difficulty']}/10, "
        f"{s['days_until_exam']} days until exam"
        for s in subjects
    ])

    task_lines = "\n".join([
        f"- {t['subject']}: {t['minutes']} minutes (priority score {t['priority']})"
        for t in plan['tasks']
    ])

    was_capped = plan.get('was_capped', False)
    cap_note   = (
        "The total hours were reduced by the Reality Check Engine due to "
        "recent low task completion rates." if was_capped else
        "No hour cap was applied."
    )

    prompt = f"""You are a study planner assistant. Explain this study plan to a student in 3 clear sentences.

Student's subjects:
{subject_lines}

Today's allocated schedule:
{task_lines}

Total hours: {plan['total_allocated_hours']}
System mode: {phase.replace('_', ' ')}
{cap_note}

Explain why each subject received the time it did, and what the student should focus on first. Be direct and practical."""

    return _query(prompt, max_new_tokens=180)


# ── Feature 2: Subject prioritization suggestions ─────────────────────────────
def suggest_subject_priorities(subjects: list, burnout_level: str) -> str:
    """
    Returns AI-generated subject prioritization advice based on
    exam proximity, difficulty, and current burnout level.

    subjects:      list of subject dicts
    burnout_level: 'low', 'yellow', 'orange', or 'red'
    """
    subject_lines = "\n".join([
        f"- {s['name']}: difficulty {s['difficulty']}/10, "
        f"{s['days_until_exam']} days until exam"
        for s in subjects
    ])

    burnout_context = {
        'low':    "The student is well-rested and has good energy today.",
        'yellow': "The student is showing early signs of fatigue.",
        'orange': "The student is at elevated burnout risk. Avoid high-difficulty tasks first.",
        'red':    "The student is at high burnout risk. Only light review tasks are appropriate.",
    }.get(burnout_level, "Burnout level unknown.")

    prompt = f"""You are a study advisor. Rank these subjects by study priority for today and give one sentence of advice for each.

Subjects:
{subject_lines}

Student's current state: {burnout_context}

Rules:
- Subjects with fewer days until exam and higher difficulty should be ranked higher
- If burnout is orange or red, suggest lighter approaches for difficult subjects
- Give a clear ranked list with one practical tip per subject

Provide the ranked list now:"""

    return _query(prompt, max_new_tokens=220)


# ── Feature 3: Burnout interpretation ─────────────────────────────────────────
def interpret_burnout_score(score: float, level: str, days_used: int,
                             signals: dict) -> str:
    """
    Returns a natural language interpretation of the current burnout score.
    signals: dict with keys mood, energy, stress, sleep and their today values.
    """
    signal_lines = "\n".join([
        f"- {k.title()}: {v}" for k, v in signals.items()
    ])

    prompt = f"""You are a wellbeing coach. Interpret this burnout score for a student in 2 sentences. Do not give medical advice.

Burnout score: {score:+.2f} (range: negative = below baseline, positive = above baseline)
Risk level: {level.upper()}
Based on {days_used} days of personal baseline data

Today's signals:
{signal_lines}

Explain what this score means for the student's study session today. Be honest but constructive:"""

    return _query(prompt, max_new_tokens=120)
