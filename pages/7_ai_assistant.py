# pages/6_ai_assistant.py

import streamlit as st
import json
from datetime import date
from engines.ai_engine import (
    generate_plan_explanation,
    suggest_subject_priorities,
    interpret_burnout_score,
)
from engines.ai_cache import get_cached, set_cached, clear_cache
from engines.phase_manager import get_phase
from engines.burnout_scorer import get_burnout_score
from database.db_manager import get_connection

st.set_page_config(page_title="AI Assistant", page_icon="🤖", layout="wide")

# ── Styling ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Sora:wght@300;400;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Sora', sans-serif; }

.page-title {
    font-size: 2rem;
    font-weight: 700;
    letter-spacing: -0.03em;
    margin-bottom: 0.2rem;
}

.page-sub {
    font-size: 0.88rem;
    color: #666;
    font-weight: 300;
    margin-bottom: 2rem;
}

/* AI response card */
.ai-card {
    background: #080808;
    border: 1px solid #1a1a1a;
    border-left: 3px solid #7c3aed;
    border-radius: 0 14px 14px 0;
    padding: 1.4rem 1.8rem;
    margin: 1rem 0;
    position: relative;
}

.ai-card-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    color: #7c3aed;
    margin-bottom: 0.7rem;
}

.ai-response-text {
    font-size: 0.93rem;
    color: #ccc;
    line-height: 1.8;
    white-space: pre-wrap;
}

/* Model badge */
.model-badge {
    display: inline-block;
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    padding: 0.2rem 0.7rem;
    border-radius: 20px;
    background: #110d1a;
    border: 1px solid #3d1f6e;
    color: #a78bfa;
    margin-bottom: 1.5rem;
}

/* Section label */
.section-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    color: #333;
    margin: 1.6rem 0 0.6rem 0;
}

/* Input context card */
.context-card {
    background: #050505;
    border: 1px solid #141414;
    border-radius: 12px;
    padding: 1rem 1.4rem;
    margin-bottom: 1rem;
    font-size: 0.82rem;
    color: #555;
    font-family: 'DM Mono', monospace;
    line-height: 1.8;
}

/* Cache indicator */
.cache-hit {
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem;
    color: #1e5c24;
    padding: 0.15rem 0.5rem;
    border-radius: 4px;
    background: #0d1f0f;
    border: 1px solid #1e5c24;
    display: inline-block;
    margin-left: 0.5rem;
}

.cache-miss {
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem;
    color: #7c3aed;
    padding: 0.15rem 0.5rem;
    border-radius: 4px;
    background: #110d1a;
    border: 1px solid #3d1f6e;
    display: inline-block;
    margin-left: 0.5rem;
}

/* Warning box */
.warn-box {
    background: #100a00;
    border-left: 3px solid #f59e0b;
    border-radius: 0 10px 10px 0;
    padding: 0.9rem 1.2rem;
    font-size: 0.82rem;
    color: #d97706;
    line-height: 1.6;
    margin-bottom: 1rem;
}

.disclaimer {
    font-size: 0.73rem;
    color: #1e1e1e;
    font-family: 'DM Mono', monospace;
    line-height: 1.6;
    text-align: center;
    margin-top: 2.5rem;
    padding-top: 1rem;
    border-top: 1px solid #0f0f0f;
}
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="page-title">🤖 AI Assistant</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="page-sub">Powered by Hugging Face Inference API · '
    'google/flan-t5-base</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<span class="model-badge">flan-t5-base · inference api · free tier</span>',
    unsafe_allow_html=True
)

# ── API key guard ──────────────────────────────────────────────────────────────
import os
from dotenv import load_dotenv
load_dotenv(dotenv_path="/home/rs/projects/study_planner/api_key.env")

if not os.getenv("HF_API_KEY"):
    st.error(
        "**HF_API_KEY not found.** Create a `.env` file in your project root "
        "with the line: `HF_API_KEY=hf_your_key_here`"
    )
    st.markdown("""
    <div class="warn-box">
        Get a free API key at huggingface.co/settings/tokens.
        Select "Read" access. No GPU or paid plan required.
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Fetch context data ─────────────────────────────────────────────────────────
phase   = get_phase()
burnout = get_burnout_score()

with get_connection() as conn:
    today_plan = conn.execute(
        "SELECT * FROM plans WHERE plan_date = ? AND user_id = 'default'",
        (date.today().isoformat(),)
    ).fetchone()

    today_log = conn.execute(
        "SELECT mood_score, energy_score, stress_score, sleep_hours "
        "FROM daily_logs WHERE log_date = ? AND user_id = 'default'",
        (date.today().isoformat(),)
    ).fetchone()

subjects = []
if today_plan:
    try:
        subjects = json.loads(today_plan['input_subjects'])
    except Exception:
        pass

plan_dict = None
if today_plan and subjects:
    from engines.plan_generator import generate_daily_plan
    try:
        plan_dict = generate_daily_plan(
            today_plan['input_available_hours'], subjects
        )
    except Exception:
        pass

# ── Layout ─────────────────────────────────────────────────────────────────────
col_left, col_right = st.columns([1.4, 1])

# ══════════════════════════════════════════════════════════════════════════════
# LEFT COLUMN — AI features
# ══════════════════════════════════════════════════════════════════════════════
with col_left:

    # ── Feature 1: Plan explanation ────────────────────────────────────────────
    st.markdown('<div class="section-label">Plan Explanation</div>', unsafe_allow_html=True)

    if not today_plan or not plan_dict:
        st.markdown("""
        <div class="warn-box">
            No study plan found for today. Generate a plan on the 
            Study Plan page first, then return here for an AI explanation.
        </div>
        """, unsafe_allow_html=True)
    else:
        # Show what data will be sent
        st.markdown(f"""
        <div class="context-card">
            Subjects: {", ".join(s['name'] for s in subjects)}<br>
            Allocated: {today_plan['output_allocated_hours']:.1f}h &nbsp;·&nbsp;
            Phase: {phase.replace('_',' ').title()} &nbsp;·&nbsp;
            Capped: {"Yes" if today_plan['output_capped'] else "No"}
        </div>
        """, unsafe_allow_html=True)

        if st.button("🤖 Explain my plan", type="primary", key="btn_explain"):
            cache_key = {
                "feature":  "plan_explanation",
                "subjects": subjects,
                "phase":    phase,
                "hours":    today_plan['output_allocated_hours'],
                "capped":   bool(today_plan['output_capped']),
                "date":     date.today().isoformat(),
            }

            cached = get_cached(cache_key)

            if cached:
                st.session_state['plan_explanation'] = cached
                st.session_state['plan_exp_cached']  = True
            else:
                with st.spinner("Generating explanation..."):
                    try:
                        result = generate_plan_explanation(
                            plan_dict, subjects, phase
                        )
                        set_cached(cache_key, result)
                        st.session_state['plan_explanation'] = result
                        st.session_state['plan_exp_cached']  = False
                    except Exception as e:
                        st.error(f"AI request failed: {e}")

        if 'plan_explanation' in st.session_state:
            cached_label = (
                '<span class="cache-hit">cached</span>'
                if st.session_state.get('plan_exp_cached')
                else '<span class="cache-miss">live response</span>'
            )
            st.markdown(
                f'<div class="ai-card-label">Plan Explanation {cached_label}</div>',
                unsafe_allow_html=True
            )
            st.markdown(f"""
            <div class="ai-card">
                <div class="ai-response-text">{st.session_state['plan_explanation']}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Feature 2: Subject prioritization ─────────────────────────────────────
    st.markdown(
        '<div class="section-label">Subject Prioritization</div>',
        unsafe_allow_html=True
    )

    if not subjects:
        st.markdown("""
        <div class="warn-box">
            No subjects found for today. Generate a study plan first.
        </div>
        """, unsafe_allow_html=True)
    else:
        burnout_level = burnout['level'] if burnout else 'low'

        st.markdown(f"""
        <div class="context-card">
            {len(subjects)} subject(s) · 
            Burnout level: {burnout_level.upper()}<br>
            {" · ".join(
                f"{s['name']} ({s['days_until_exam']}d, diff {s['difficulty']})"
                for s in subjects
            )}
        </div>
        """, unsafe_allow_html=True)

        if st.button(
            "🎯 Suggest priority order", type="primary", key="btn_priority"
        ):
            cache_key = {
                "feature":       "subject_priority",
                "subjects":      subjects,
                "burnout_level": burnout_level,
                "date":          date.today().isoformat(),
            }

            cached = get_cached(cache_key)

            if cached:
                st.session_state['priority_suggestion'] = cached
                st.session_state['priority_cached']     = True
            else:
                with st.spinner("Analysing subjects..."):
                    try:
                        result = suggest_subject_priorities(
                            subjects, burnout_level
                        )
                        set_cached(cache_key, result)
                        st.session_state['priority_suggestion'] = result
                        st.session_state['priority_cached']     = False
                    except Exception as e:
                        st.error(f"AI request failed: {e}")

        if 'priority_suggestion' in st.session_state:
            cached_label = (
                '<span class="cache-hit">cached</span>'
                if st.session_state.get('priority_cached')
                else '<span class="cache-miss">live response</span>'
            )
            st.markdown(
                f'<div class="ai-card-label">Priority Suggestion {cached_label}</div>',
                unsafe_allow_html=True
            )
            st.markdown(f"""
            <div class="ai-card">
                <div class="ai-response-text">{st.session_state['priority_suggestion']}</div>
            </div>
            """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# RIGHT COLUMN — burnout interpretation + controls
# ══════════════════════════════════════════════════════════════════════════════
with col_right:

    # ── Burnout interpretation ─────────────────────────────────────────────────
    st.markdown(
        '<div class="section-label">Burnout Interpretation</div>',
        unsafe_allow_html=True
    )

    if not burnout:
        st.markdown("""
        <div class="warn-box">
            Burnout scoring not yet active. Complete 7 days of check-ins first.
        </div>
        """, unsafe_allow_html=True)
    elif not today_log:
        st.markdown("""
        <div class="warn-box">
            Today's check-in not submitted. Submit it first to get 
            a burnout interpretation based on today's signals.
        </div>
        """, unsafe_allow_html=True)
    else:
        signals = {
            "mood":   today_log['mood_score'],
            "energy": today_log['energy_score'],
            "stress": today_log['stress_score'],
            "sleep":  today_log['sleep_hours'],
        }

        LEVEL_COLORS = {
            'low': '#4ade80', 'yellow': '#fbbf24',
            'orange': '#fb923c', 'red': '#f87171'
        }
        clr = LEVEL_COLORS.get(burnout['level'], '#888')

        st.markdown(f"""
        <div class="context-card">
            Score: <span style="color:{clr}; font-weight:600;">
                {burnout['score']:+.2f}
            </span> · Level: <span style="color:{clr};">{burnout['level'].upper()}</span><br>
            Mood {signals['mood']} · Energy {signals['energy']} · 
            Stress {signals['stress']} · Sleep {signals['sleep']}h
        </div>
        """, unsafe_allow_html=True)

        if st.button(
            "🧠 Interpret burnout score", type="primary", key="btn_burnout"
        ):
            cache_key = {
                "feature":  "burnout_interpretation",
                "score":    burnout['score'],
                "level":    burnout['level'],
                "signals":  signals,
                "date":     date.today().isoformat(),
            }

            cached = get_cached(cache_key)

            if cached:
                st.session_state['burnout_interpretation'] = cached
                st.session_state['burnout_int_cached']     = True
            else:
                with st.spinner("Interpreting score..."):
                    try:
                        result = interpret_burnout_score(
                            burnout['score'],
                            burnout['level'],
                            burnout['days_used'],
                            signals
                        )
                        set_cached(cache_key, result)
                        st.session_state['burnout_interpretation'] = result
                        st.session_state['burnout_int_cached']     = False
                    except Exception as e:
                        st.error(f"AI request failed: {e}")

        if 'burnout_interpretation' in st.session_state:
            cached_label = (
                '<span class="cache-hit">cached</span>'
                if st.session_state.get('burnout_int_cached')
                else '<span class="cache-miss">live response</span>'
            )
            st.markdown(
                f'<div class="ai-card-label">Interpretation {cached_label}</div>',
                unsafe_allow_html=True
            )
            st.markdown(f"""
            <div class="ai-card">
                <div class="ai-response-text">
                    {st.session_state['burnout_interpretation']}
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Cache controls ─────────────────────────────────────────────────────────
    st.markdown(
        '<div class="section-label">Cache Controls</div>',
        unsafe_allow_html=True
    )
    st.markdown("""
    <div style="font-size:0.78rem; color:#444; font-family:'DM Mono',monospace;
    line-height:1.7; margin-bottom:0.8rem;">
        Responses are cached for 24 hours to conserve free-tier API quota.
        Clear cache to force fresh responses.
    </div>
    """, unsafe_allow_html=True)

    if st.button("🗑 Clear AI cache", key="btn_clear_cache"):
        clear_cache()
        # Also clear session state responses
        for key in [
            'plan_explanation', 'plan_exp_cached',
            'priority_suggestion', 'priority_cached',
            'burnout_interpretation', 'burnout_int_cached',
        ]:
            st.session_state.pop(key, None)
        st.success("Cache cleared. Next requests will hit the API.")

    # ── Model info ─────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(
        '<div class="section-label">Model Info</div>',
        unsafe_allow_html=True
    )
    st.markdown("""
    <div style="font-size:0.78rem; color:#444; font-family:'DM Mono',
    monospace; line-height:1.9;">
        Model: google/flan-t5-base<br>
        Provider: Hugging Face Inference API<br>
        Tier: Free (no GPU)<br>
        Rate limit: ~30k tokens/month<br>
        Cold start: ~20s on first request<br>
        Fallback: google/flan-t5-small
    </div>
    """, unsafe_allow_html=True)

# ── Disclaimer ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="disclaimer">
    AI responses are generated by flan-t5-base and may be inaccurate or incomplete.<br>
    They are informational only. No AI output in this system constitutes 
    academic, medical, or professional advice.
</div>
""", unsafe_allow_html=True)
