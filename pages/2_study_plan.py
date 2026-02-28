# pages/2_study_plan.py

import streamlit as st
import json
from datetime import date
from engines.plan_generator import generate_daily_plan
from engines.phase_manager import get_phase, get_log_count
from engines.feedback_splitter import get_reality_check_cap
from engines.burnout_scorer import get_burnout_score
from database.db_manager import get_connection

st.set_page_config(page_title="Study Plan", page_icon="📅", layout="wide")

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

/* Phase badge */
.phase-badge {
    display: inline-block;
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    padding: 0.25rem 0.8rem;
    border-radius: 20px;
    margin-bottom: 1.6rem;
}

.badge-cold        { background:#0d1f35; color:#60a5fa; border:1px solid #1e3d6e; }
.badge-bootstrap   { background:#1a1400; color:#fbbf24; border:1px solid #92610a; }
.badge-adaptive    { background:#0d1f0f; color:#4ade80; border:1px solid #1e5c24; }

/* Task card */
.task-card {
    background: #080808;
    border: 1px solid #1a1a1a;
    border-radius: 14px;
    padding: 1.3rem 1.6rem;
    margin-bottom: 0.9rem;
    position: relative;
}

.task-card:hover { border-color: #2a2a2a; }

.task-subject {
    font-size: 1rem;
    font-weight: 600;
    color: #ddd;
    margin-bottom: 0.5rem;
}

.task-meta-row {
    display: flex;
    gap: 0.6rem;
    flex-wrap: wrap;
    margin-bottom: 0.5rem;
}

.task-pill {
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
    padding: 0.2rem 0.65rem;
    border-radius: 20px;
    background: #111;
    border: 1px solid #222;
    color: #666;
}

.task-pill.time    { border-color:#1e3d6e; color:#60a5fa; }
.task-pill.buffer  { border-color:#1e5c24; color:#4ade80; }
.task-pill.priority{ border-color:#3d1f6e; color:#c084fc; }

.task-bar-bg {
    height: 3px;
    background: #111;
    border-radius: 2px;
    margin-top: 0.7rem;
    overflow: hidden;
}

.task-bar-fill {
    height: 100%;
    border-radius: 2px;
    background: linear-gradient(90deg, #2E75B6, #4ade80);
}

/* Summary sidebar card */
.summary-block {
    background: #080808;
    border: 1px solid #1a1a1a;
    border-radius: 14px;
    padding: 1.3rem 1.6rem;
    margin-bottom: 1rem;
}

.summary-block-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    color: #444;
    margin-bottom: 0.9rem;
}

.summary-stat-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.42rem 0;
    border-bottom: 1px solid #0f0f0f;
    font-size: 0.83rem;
}

.summary-stat-row:last-child { border-bottom: none; }
.stat-key   { color: #555; }
.stat-value {
    font-family: 'DM Mono', monospace;
    color: #ddd;
    font-weight: 500;
}

/* Cap / burnout alert boxes */
.alert-box {
    border-radius: 10px;
    padding: 1rem 1.3rem;
    margin-bottom: 1rem;
    font-size: 0.83rem;
    line-height: 1.65;
}

.alert-cap     { background:#100a00; border-left:3px solid #f59e0b; color:#d97706; }
.alert-burnout { background:#180005; border-left:3px solid #f87171; color:#f87171; }
.alert-info    { background:#080808; border-left:3px solid #2E75B6; color:#555;    }

/* Already-planned banner */
.existing-banner {
    background: #0d1f0f;
    border: 1px solid #1e5c24;
    border-radius: 12px;
    padding: 1.1rem 1.5rem;
    color: #4ade80;
    font-size: 0.87rem;
    line-height: 1.7;
    margin-bottom: 1.4rem;
}

/* Section label */
.section-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    color: #444;
    margin: 1.4rem 0 0.5rem 0;
}

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
st.markdown('<div class="page-title">📅 Study Plan</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="page-sub">Optimised schedule · {date.today().strftime("%A, %B %d %Y")}</div>',
    unsafe_allow_html=True
)

# ── Phase badge ────────────────────────────────────────────────────────────────
phase     = get_phase()
log_count = get_log_count()

PHASE_BADGE = {
    'cold_start':    ('badge-cold',      'Cold Start'),
    'bootstrapping': ('badge-bootstrap', 'Bootstrapping'),
    'adaptive':      ('badge-adaptive',  'Adaptive'),
}
badge_cls, badge_text = PHASE_BADGE[phase]
st.markdown(
    f'<span class="phase-badge {badge_cls}">{badge_text} · {log_count} days logged</span>',
    unsafe_allow_html=True
)

# ── Cold start info strip ──────────────────────────────────────────────────────
if phase == 'cold_start':
    st.markdown("""
    <div class="alert-box alert-info">
        <strong>Cold Start Mode:</strong> Fewer than 7 days of check-in data exist.
        Plans use a fixed 80% conservative buffer. Reality Check and burnout 
        interventions activate at Day 7.
    </div>
    """, unsafe_allow_html=True)

# ── Check for existing plan ────────────────────────────────────────────────────
def get_todays_plan():
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM plans WHERE plan_date = ? AND user_id = 'default'",
            (date.today().isoformat(),)
        ).fetchone()

existing_plan = get_todays_plan()

if existing_plan:
    subjects_saved = []
    try:
        subjects_saved = json.loads(existing_plan['input_subjects'])
    except Exception:
        pass

    st.markdown(f"""
    <div class="existing-banner">
        <strong>✅ A plan already exists for today.</strong><br>
        {len(subjects_saved)} subject(s) · 
        {existing_plan['output_allocated_hours']:.1f}h allocated · 
        Phase: {existing_plan['phase_at_creation'].replace('_',' ').title()} · 
        Capped: {"Yes" if existing_plan['output_capped'] else "No"}
    </div>
    """, unsafe_allow_html=True)

    if not st.checkbox("Regenerate today's plan"):
        # ── Render saved plan without regenerating ─────────────────────────
        st.markdown('<div class="section-label">Today\'s schedule</div>', unsafe_allow_html=True)

        col_tasks, col_sidebar = st.columns([1.6, 1])

        with col_tasks:
            if subjects_saved:
                # Reconstruct display from saved subjects + allocated hours
                total_mins = existing_plan['output_allocated_hours'] * 60
                priorities = [
                    s['difficulty'] * (1 / max(s['days_until_exam'], 1))
                    for s in subjects_saved
                ]
                total_p = sum(priorities)

                for i, subj in enumerate(subjects_saved):
                    weight     = priorities[i] / total_p
                    task_mins  = max(int(total_mins * weight) - 20, 15)
                    pct_of_day = (task_mins / (total_mins or 1)) * 100

                    st.markdown(f"""
                    <div class="task-card">
                        <div class="task-subject">📚 {subj['name']}</div>
                        <div class="task-meta-row">
                            <span class="task-pill time">{task_mins} mins study</span>
                            <span class="task-pill buffer">+20 min buffer</span>
                            <span class="task-pill priority">
                                priority {priorities[i]:.2f}
                            </span>
                        </div>
                        <div class="task-bar-bg">
                            <div class="task-bar-fill" style="width:{pct_of_day:.0f}%"></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.caption("Could not parse saved subjects.")

        with col_sidebar:
            _b = get_burnout_score()
            burnout_display = (
                f"{_b['level'].upper()} ({_b['score']:+.2f})" if _b else "Not active"
            )
            st.markdown(f"""
            <div class="summary-block">
                <div class="summary-block-label">Plan Summary</div>
                <div class="summary-stat-row">
                    <span class="stat-key">Allocated</span>
                    <span class="stat-value">{existing_plan['output_allocated_hours']:.1f}h</span>
                </div>
                <div class="summary-stat-row">
                    <span class="stat-key">Requested</span>
                    <span class="stat-value">{existing_plan['input_available_hours']:.1f}h</span>
                </div>
                <div class="summary-stat-row">
                    <span class="stat-key">Capped</span>
                    <span class="stat-value">
                        {"Yes" if existing_plan['output_capped'] else "No"}
                    </span>
                </div>
                <div class="summary-stat-row">
                    <span class="stat-key">Burnout level</span>
                    <span class="stat-value">{burnout_display}</span>
                </div>
                <div class="summary-stat-row">
                    <span class="stat-key">Completion logged</span>
                    <span class="stat-value">
                        {f"{existing_plan['output_completion_pct']:.0f}%" 
                         if existing_plan['output_completion_pct'] is not None 
                         else "Pending"}
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if existing_plan['output_completion_pct'] is None:
                st.markdown("""
                <div class="alert-box alert-info" style="font-size:0.8rem;">
                    Remember to log your completion on the 
                    <strong>End of Day</strong> page tonight.
                </div>
                """, unsafe_allow_html=True)
        st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# INPUT SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### Plan Parameters")

    available_hours = st.number_input(
        "Available hours today",
        min_value=0.5, max_value=16.0,
        value=4.0, step=0.5
    )

    # Reality Check preview in sidebar
    if phase != 'cold_start':
        capped_hours, will_cap = get_reality_check_cap(available_hours)
        if will_cap:
            st.markdown(f"""
            <div class="alert-box alert-cap" style="font-size:0.78rem; margin-top:0.5rem;">
                Reality Check will cap this to <strong>{capped_hours:.1f}h</strong> 
                based on your recent completion rate.
            </div>
            """, unsafe_allow_html=True)

    st.divider()
    st.markdown("### Subjects")

    num_subjects = st.number_input(
        "Number of subjects", min_value=1, max_value=6, value=2
    )

    subjects = []
    all_valid = True

    for i in range(int(num_subjects)):
        st.markdown(f"**Subject {i + 1}**")

        name = st.text_input(
            f"Name", key=f"name_{i}",
            value=f"Subject {i + 1}"
        ).strip()

        diff = st.slider(
            f"Difficulty", 1, 10, 5, key=f"diff_{i}"
        )

        days = st.number_input(
            f"Days until exam", min_value=1, max_value=365,
            value=10, key=f"days_{i}"
        )

        if not name:
            st.warning(f"Subject {i + 1} needs a name.")
            all_valid = False

        subjects.append({
            "name":           name,
            "difficulty":     diff,
            "days_until_exam": int(days)
        })

        if i < int(num_subjects) - 1:
            st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# BURNOUT GATE — reduce hours before generation if score is high
# ══════════════════════════════════════════════════════════════════════════════
burnout        = get_burnout_score()
burnout_capped = False
burnout_cap_hrs = available_hours

if burnout:
    if burnout['level'] == 'red':
        burnout_cap_hrs = min(available_hours, 2.0)
        burnout_capped  = True
        st.markdown("""
        <div class="alert-box alert-burnout">
            <strong>🔴 High burnout risk detected.</strong> Today's plan has been 
            capped at 2 hours regardless of your input. Check the Burnout Dashboard 
            or consider activating Emergency Mode.
        </div>
        """, unsafe_allow_html=True)
    elif burnout['level'] == 'orange':
        burnout_cap_hrs = available_hours * 0.75
        burnout_capped  = True
        st.markdown(f"""
        <div class="alert-box alert-cap">
            <strong>🔶 Elevated burnout score.</strong> Study intensity reduced by 25%. 
            Allocated hours capped at {burnout_cap_hrs:.1f}h.
        </div>
        """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# GENERATE BUTTON
# ══════════════════════════════════════════════════════════════════════════════
if not all_valid:
    st.button("Generate Plan", disabled=True)
    st.caption("Fill in all subject names to continue.")
else:
    if st.button("Generate Optimised Plan", type="primary"):

        # Apply burnout cap first, then reality check cap on top
        hours_after_burnout             = burnout_cap_hrs
        hours_after_reality, was_capped = get_reality_check_cap(hours_after_burnout)
        final_hours                     = hours_after_reality
        final_capped                    = was_capped or burnout_capped

        try:
            plan = generate_daily_plan(final_hours, subjects)
        except ValueError as e:
            st.error(f"Plan generation failed: {e}")
            st.stop()

        # ── Layout ─────────────────────────────────────────────────────────────
        col_tasks, col_summary = st.columns([1.6, 1])

        # ── Task cards ─────────────────────────────────────────────────────────
        with col_tasks:
            st.markdown(
                f'<div class="section-label">'
                f'Schedule · {len(plan["tasks"])} block(s) · '
                f'{plan["total_allocated_hours"]:.1f}h total</div>',
                unsafe_allow_html=True
            )

            max_mins = max(t['minutes'] for t in plan['tasks']) if plan['tasks'] else 1

            for task in plan['tasks']:
                pct = (task['minutes'] / max_mins) * 100
                st.markdown(f"""
                <div class="task-card">
                    <div class="task-subject">📚 {task['subject']}</div>
                    <div class="task-meta-row">
                        <span class="task-pill time">{task['minutes']} mins study</span>
                        <span class="task-pill buffer">+{task['break_buffer']} min buffer</span>
                        <span class="task-pill priority">priority {task['priority']:.2f}</span>
                    </div>
                    <div class="task-bar-bg">
                        <div class="task-bar-fill" style="width:{pct:.0f}%"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # ── Summary sidebar ────────────────────────────────────────────────────
        with col_summary:
            burnout_display = (
                f"{burnout['level'].upper()} ({burnout['score']:+.2f})"
                if burnout else "Not active"
            )

            st.markdown(f"""
            <div class="summary-block">
                <div class="summary-block-label">Plan Summary</div>
                <div class="summary-stat-row">
                    <span class="stat-key">Requested</span>
                    <span class="stat-value">{available_hours:.1f}h</span>
                </div>
                <div class="summary-stat-row">
                    <span class="stat-key">After burnout cap</span>
                    <span class="stat-value">{hours_after_burnout:.1f}h</span>
                </div>
                <div class="summary-stat-row">
                    <span class="stat-key">After reality check</span>
                    <span class="stat-value">{hours_after_reality:.1f}h</span>
                </div>
                <div class="summary-stat-row">
                    <span class="stat-key">Allocated</span>
                    <span class="stat-value">{plan['total_allocated_hours']:.1f}h</span>
                </div>
                <div class="summary-stat-row">
                    <span class="stat-key">Plan capped</span>
                    <span class="stat-value">{"Yes" if final_capped else "No"}</span>
                </div>
                <div class="summary-stat-row">
                    <span class="stat-key">Phase</span>
                    <span class="stat-value">{plan['phase'].replace('_',' ').title()}</span>
                </div>
                <div class="summary-stat-row">
                    <span class="stat-key">Burnout level</span>
                    <span class="stat-value">{burnout_display}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Minimum session warning
            short_tasks = [t for t in plan['tasks'] if t['minutes'] < 25]
            if short_tasks:
                names = ", ".join(t['subject'] for t in short_tasks)
                st.markdown(f"""
                <div class="alert-box alert-cap" style="font-size:0.78rem;">
                    <strong>Short sessions:</strong> {names} received under 25 minutes. 
                    Consider reducing the number of subjects or increasing available hours.
                </div>
                """, unsafe_allow_html=True)

        # ── Save to database ───────────────────────────────────────────────────
        avg_diff = sum(s['difficulty'] for s in subjects) / len(subjects)

        try:
            with get_connection() as conn:
                # Remove any existing plan for today before inserting
                conn.execute(
                    "DELETE FROM plans WHERE plan_date = ? AND user_id = 'default'",
                    (date.today().isoformat(),)
                )
                conn.execute("""
                    INSERT INTO plans (
                        plan_date, user_id,
                        input_available_hours, input_subjects,
                        input_difficulty_avg,  output_allocated_hours,
                        output_capped,         phase_at_creation
                    ) VALUES (?, 'default', ?, ?, ?, ?, ?, ?)
                """, (
                    date.today().isoformat(),
                    available_hours,
                    json.dumps(subjects),
                    round(avg_diff, 2),
                    plan['total_allocated_hours'],
                    1 if final_capped else 0,
                    plan['phase']
                ))

            st.toast("Plan saved.")

        except Exception as e:
            st.error(f"Failed to save plan: {e}")
            raise

        # ── End-of-day reminder ────────────────────────────────────────────────
        st.markdown("""
        <div class="alert-box alert-info" style="margin-top:1rem;">
            Remember to log your task completion tonight on the 
            <strong>End of Day</strong> page. Completion data powers the 
            Reality Check Engine and insights engine.
        </div>
        """, unsafe_allow_html=True)

# ── Disclaimer ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="disclaimer">
    Plans are generated from your inputs and current phase data only.<br>
    Burnout caps and reality check adjustments are logged for transparency.
</div>
""", unsafe_allow_html=True)
