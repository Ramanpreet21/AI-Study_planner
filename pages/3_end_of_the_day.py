# pages/1_daily_checkin.py

import streamlit as st
from datetime import date
from database.db_manager import get_connection
from engines.phase_manager import get_phase, get_log_count

st.set_page_config(page_title="Daily Check-in", page_icon="📋", layout="centered")

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

/* Phase progress bar */
.phase-track {
    background: #111;
    border: 1px solid #222;
    border-radius: 10px;
    padding: 1rem 1.4rem;
    margin-bottom: 1.8rem;
}

.phase-track-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #555;
    margin-bottom: 0.6rem;
}

.phase-track-bar {
    height: 4px;
    border-radius: 2px;
    background: #1a1a1a;
    margin: 0.4rem 0 0.6rem 0;
    overflow: hidden;
}

.phase-track-fill {
    height: 100%;
    border-radius: 2px;
    background: linear-gradient(90deg, #2E75B6, #4ade80);
    transition: width 0.4s ease;
}

.phase-track-status {
    font-family: 'DM Mono', monospace;
    font-size: 0.78rem;
    color: #888;
}

/* Input section cards */
.section-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #555;
    margin: 1.6rem 0 0.4rem 0;
}

/* Score display badges */
.score-badge-row {
    display: flex;
    gap: 0.6rem;
    margin-bottom: 0.4rem;
    flex-wrap: wrap;
}

.score-badge {
    font-family: 'DM Mono', monospace;
    font-size: 0.75rem;
    padding: 0.2rem 0.6rem;
    border-radius: 6px;
    background: #111;
    border: 1px solid #222;
    color: #666;
}

.score-badge.active {
    background: #0d1f35;
    border-color: #2E75B6;
    color: #60a5fa;
}

/* Already logged banner */
.logged-banner {
    background: #0d1f0f;
    border: 1px solid #1e5c24;
    border-radius: 12px;
    padding: 1.2rem 1.6rem;
    color: #4ade80;
    font-size: 0.88rem;
    line-height: 1.7;
    margin-bottom: 1.5rem;
}

.logged-banner-title {
    font-weight: 600;
    font-size: 1rem;
    margin-bottom: 0.3rem;
}

/* Summary card after submit */
.summary-card {
    background: #0a0a0a;
    border: 1px solid #1e1e1e;
    border-radius: 14px;
    padding: 1.4rem 1.8rem;
    margin-top: 1rem;
}

.summary-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem 0;
    border-bottom: 1px solid #141414;
    font-size: 0.85rem;
}

.summary-row:last-child { border-bottom: none; }
.summary-key   { color: #666; font-weight: 400; }
.summary-value { font-family: 'DM Mono', monospace; color: #ddd; font-weight: 500; }

/* Contextual tip box */
.tip-box {
    background: #0f1117;
    border-left: 3px solid #2E75B6;
    border-radius: 0 10px 10px 0;
    padding: 0.9rem 1.2rem;
    margin-top: 1.2rem;
    font-size: 0.83rem;
    color: #888;
    line-height: 1.6;
}

.tip-box strong { color: #aaa; }

.mono { font-family: 'DM Mono', monospace; }

.disclaimer {
    font-size: 0.73rem;
    color: #2a2a2a;
    font-family: 'DM Mono', monospace;
    line-height: 1.6;
    text-align: center;
    margin-top: 2.5rem;
    padding-top: 1rem;
    border-top: 1px solid #141414;
}
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="page-title">📋 Daily Check-in</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="page-sub">Behavioral signals · {date.today().strftime("%A, %B %d %Y")}</div>',
    unsafe_allow_html=True
)

# ── Phase progress tracker ─────────────────────────────────────────────────────
phase     = get_phase()
log_count = get_log_count()

PHASE_MILESTONES = [
    (7,  "cold_start",    "Bootstrapping unlocks at 7 days"),
    (14, "bootstrapping", "Adaptive mode unlocks at 14 days"),
]

progress_pct = min(log_count / 14, 1.0) * 100
phase_label  = phase.replace("_", " ").upper()

next_milestone_text = ""
for threshold, p, msg in PHASE_MILESTONES:
    if log_count < threshold:
        days_left = threshold - log_count
        next_milestone_text = f"{msg} · {days_left} day{'s' if days_left != 1 else ''} remaining"
        break

if not next_milestone_text:
    next_milestone_text = "All adaptive features active"

st.markdown(f"""
<div class="phase-track">
    <div class="phase-track-label">System Phase</div>
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <span class="phase-track-status">{phase_label}</span>
        <span class="phase-track-status">{log_count} / 14 days</span>
    </div>
    <div class="phase-track-bar">
        <div class="phase-track-fill" style="width:{progress_pct:.1f}%"></div>
    </div>
    <div class="phase-track-status">{next_milestone_text}</div>
</div>
""", unsafe_allow_html=True)

# ── Check: already logged today? ───────────────────────────────────────────────
def get_todays_log():
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM daily_logs WHERE log_date = ? AND user_id = 'default'",
            (date.today().isoformat(),)
        ).fetchone()

existing = get_todays_log()

if existing:
    st.markdown(f"""
    <div class="logged-banner">
        <div class="logged-banner-title">✅ Today's check-in is already logged.</div>
        Mood: <strong>{existing['mood_score']}/10</strong> &nbsp;·&nbsp;
        Energy: <strong>{existing['energy_score']}/10</strong> &nbsp;·&nbsp;
        Stress: <strong>{existing['stress_score']}/10</strong> &nbsp;·&nbsp;
        Sleep: <strong>{existing['sleep_hours']}h</strong>
    </div>
    """, unsafe_allow_html=True)

    if not st.checkbox("Edit today's entry"):
        st.stop()
    else:
        st.info("Submitting again will overwrite today's record.")

# ── Input form ─────────────────────────────────────────────────────────────────
# Prefill with existing values if editing
defaults = {
    "mood":   existing['mood_score']   if existing else 5,
    "energy": existing['energy_score'] if existing else 5,
    "stress": existing['stress_score'] if existing else 5,
    "sleep":  existing['sleep_hours']  if existing else 7.0,
}

with st.form("daily_checkin_form", clear_on_submit=False):

    # ── Mood ──────────────────────────────────────────────────────────────────
    st.markdown('<div class="section-label">Mood</div>', unsafe_allow_html=True)
    st.caption("How are you feeling overall right now? 1 = very low, 10 = excellent.")
    mood = st.slider(
        "Mood score",
        min_value=1, max_value=10,
        value=defaults["mood"],
        label_visibility="collapsed"
    )

    MOOD_LABELS = {
        (1, 2): "Very low — significant emotional difficulty",
        (3, 4): "Below baseline — noticeable low feeling",
        (5, 6): "Neutral to moderate",
        (7, 8): "Good — generally positive",
        (9, 10): "Excellent — strong emotional state",
    }
    for rng, label in MOOD_LABELS.items():
        if rng[0] <= mood <= rng[1]:
            st.markdown(
                f'<div style="font-size:0.78rem; color:#555; font-family:\'DM Mono\',monospace;">'
                f'→ {label}</div>',
                unsafe_allow_html=True
            )
            break

    # ── Energy ────────────────────────────────────────────────────────────────
    st.markdown('<div class="section-label">Energy</div>', unsafe_allow_html=True)
    st.caption("Physical and mental energy available for focused work. 1 = exhausted, 10 = fully alert.")
    energy = st.slider(
        "Energy score",
        min_value=1, max_value=10,
        value=defaults["energy"],
        label_visibility="collapsed"
    )

    ENERGY_LABELS = {
        (1, 2): "Exhausted — cognitive function significantly impaired",
        (3, 4): "Low energy — concentration will be difficult",
        (5, 6): "Moderate — manageable with structure",
        (7, 8): "Good energy — suitable for demanding tasks",
        (9, 10): "High energy — optimal focus conditions",
    }
    for rng, label in ENERGY_LABELS.items():
        if rng[0] <= energy <= rng[1]:
            st.markdown(
                f'<div style="font-size:0.78rem; color:#555; font-family:\'DM Mono\',monospace;">'
                f'→ {label}</div>',
                unsafe_allow_html=True
            )
            break

    # ── Stress ────────────────────────────────────────────────────────────────
    st.markdown('<div class="section-label">Stress</div>', unsafe_allow_html=True)
    st.caption("Current stress load from all sources — academic, personal, environmental. 1 = none, 10 = severe.")
    stress = st.slider(
        "Stress score",
        min_value=1, max_value=10,
        value=defaults["stress"],
        label_visibility="collapsed"
    )

    STRESS_LABELS = {
        (1, 2): "Minimal stress — clear headspace",
        (3, 4): "Low stress — manageable background pressure",
        (5, 6): "Moderate stress — noticeable but functional",
        (7, 8): "High stress — affecting concentration and wellbeing",
        (9, 10): "Severe stress — significant impairment likely",
    }
    for rng, label in STRESS_LABELS.items():
        if rng[0] <= stress <= rng[1]:
            st.markdown(
                f'<div style="font-size:0.78rem; color:#555; font-family:\'DM Mono\',monospace;">'
                f'→ {label}</div>',
                unsafe_allow_html=True
            )
            break

    # ── Sleep ─────────────────────────────────────────────────────────────────
    st.markdown('<div class="section-label">Sleep</div>', unsafe_allow_html=True)
    st.caption("Hours slept last night. Used to detect sleep deprivation patterns over time.")

    sleep = st.number_input(
        "Sleep hours",
        min_value=0.0, max_value=24.0,
        value=float(defaults["sleep"]),
        step=0.5,
        label_visibility="collapsed"
    )

    SLEEP_LABELS = [
        (0,   4,   "Severely sleep deprived — cognitive performance markedly reduced"),
        (4,   6,   "Below recommended — likely affecting focus and memory consolidation"),
        (6,   8,   "Adequate — within typical functional range"),
        (8,   10,  "Well rested — optimal for learning and retention"),
        (10,  24,  "Extended sleep — may indicate recovery need or illness"),
    ]
    for lo, hi, label in SLEEP_LABELS:
        if lo <= sleep < hi:
            st.markdown(
                f'<div style="font-size:0.78rem; color:#555; font-family:\'DM Mono\',monospace;">'
                f'→ {label}</div>',
                unsafe_allow_html=True
            )
            break

    st.markdown("---")

    # ── Reliability note ──────────────────────────────────────────────────────
    st.markdown("""
    <div class="tip-box">
        <strong>On accurate reporting:</strong> The burnout scorer normalises your inputs 
        against your own baseline — not a population average. Consistently over- or 
        under-reporting will shift your baseline and reduce detection accuracy. 
        Report what you actually feel, not what you think you should feel.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("")
    submitted = st.form_submit_button("Submit check-in", type="primary", use_container_width=True)

# ── Handle submission ──────────────────────────────────────────────────────────
if submitted:

    # Validate — belt-and-suspenders on top of slider constraints
    errors = []
    if not (1 <= mood   <= 10): errors.append("Mood must be between 1 and 10.")
    if not (1 <= energy <= 10): errors.append("Energy must be between 1 and 10.")
    if not (1 <= stress <= 10): errors.append("Stress must be between 1 and 10.")
    if not (0 <= sleep  <= 24): errors.append("Sleep hours must be between 0 and 24.")

    if errors:
        for e in errors:
            st.error(e)
        st.stop()

    try:
        with get_connection() as conn:
            # Upsert — insert or replace if editing today's record
            conn.execute("""
                INSERT INTO daily_logs
                    (user_id, log_date, mood_score, energy_score, stress_score, sleep_hours)
                VALUES ('default', ?, ?, ?, ?, ?)
                ON CONFLICT(log_date) DO UPDATE SET
                    mood_score   = excluded.mood_score,
                    energy_score = excluded.energy_score,
                    stress_score = excluded.stress_score,
                    sleep_hours  = excluded.sleep_hours,
                    created_at   = datetime('now')
            """, (
                date.today().isoformat(),
                mood, energy, stress, sleep
            ))

        # ── Success summary ────────────────────────────────────────────────────
        new_count = get_log_count()
        action    = "updated" if existing else "logged"

        st.success(f"Check-in {action} for {date.today().strftime('%B %d')}.")

        st.markdown(f"""
        <div class="summary-card">
            <div class="summary-row">
                <span class="summary-key">Mood</span>
                <span class="summary-value">{mood} / 10</span>
            </div>
            <div class="summary-row">
                <span class="summary-key">Energy</span>
                <span class="summary-value">{energy} / 10</span>
            </div>
            <div class="summary-row">
                <span class="summary-key">Stress</span>
                <span class="summary-value">{stress} / 10</span>
            </div>
            <div class="summary-row">
                <span class="summary-key">Sleep</span>
                <span class="summary-value">{sleep}h</span>
            </div>
            <div class="summary-row">
                <span class="summary-key">Total days logged</span>
                <span class="summary-value">{new_count} / 14</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Phase unlock notification
        if new_count == 7:
            st.balloons()
            st.success("🔓 Bootstrapping phase unlocked. The Reality Check Engine and burnout scorer are now active.")
        elif new_count == 14:
            st.balloons()
            st.success("🔓 Adaptive phase unlocked. All features are now active including correlation insights.")

        # Contextual next-step prompt
        st.markdown('<div class="section-label" style="margin-top:1.4rem;">Next steps</div>', unsafe_allow_html=True)

        if stress >= 8 or (mood <= 3 and energy <= 3):
            st.markdown("""
            <div class="tip-box" style="border-left-color: #f87171;">
                <strong>High stress or very low mood/energy detected.</strong>
                Consider checking your burnout dashboard before generating today's plan.
                If you are experiencing acute distress, Emergency Mode is available.
            </div>
            """, unsafe_allow_html=True)
        elif sleep < 5:
            st.markdown("""
            <div class="tip-box" style="border-left-color: #fbbf24;">
                <strong>Low sleep logged.</strong>
                The plan generator will factor this into your burnout score.
                Consider a reduced schedule today if energy is also low.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="tip-box">
                Check-in complete. Head to the <strong>Study Plan</strong> page to 
                generate today's schedule.
            </div>
            """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Failed to save check-in: {e}")
        raise  # Remove in production

# ── Disclaimer ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="disclaimer">
    Self-reported scores are normalized against your personal baseline only.<br>
    This system does not assess mental health. If you are struggling, 
    please speak with a counsellor or support service.
</div>
""", unsafe_allow_html=True)
