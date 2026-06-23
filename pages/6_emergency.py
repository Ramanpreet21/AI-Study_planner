# pages/5_emergency.py

import streamlit as st
import time
from datetime import date
from database.db_manager import get_connection
from engines.task_redistributor import redistribute_deferred_tasks
from engines.burnout_scorer import get_burnout_score

st.set_page_config(page_title="Emergency Mode", page_icon="🚨", layout="centered")

# ── Styling ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Sora:wght@300;400;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Sora', sans-serif; }

.emergency-header {
    text-align: center;
    padding: 2rem 0 1rem 0;
}

.emergency-title {
    font-size: 2.2rem;
    font-weight: 700;
    color: #f87171;
    letter-spacing: -0.03em;
    margin-bottom: 0.3rem;
}

.emergency-sub {
    font-size: 0.9rem;
    color: #666;
    font-weight: 300;
}

/* State cards */
.state-card {
    border-radius: 14px;
    padding: 1.6rem 2rem;
    margin: 1rem 0;
    line-height: 1.7;
    font-size: 0.92rem;
}

.state-idle {
    background: #0f0f0f;
    border: 1px solid #2a2a2a;
    color: #aaa;
}

.state-active {
    background: #180005;
    border: 1px solid #7f1d1d;
    color: #fca5a5;
}

.state-recovery {
    background: #0d1f0f;
    border: 1px solid #1e5c24;
    color: #86efac;
}

/* Grounding protocol steps */
.protocol-step {
    background: #111;
    border-left: 3px solid #f87171;
    border-radius: 0 10px 10px 0;
    padding: 1rem 1.4rem;
    margin: 0.6rem 0;
    font-size: 0.88rem;
    color: #ddd;
    transition: border-color 0.4s;
}

.protocol-step.done {
    border-left-color: #4ade80;
    color: #888;
}

.protocol-step-num {
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
    color: #555;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 0.3rem;
}

.protocol-step-text {
    font-weight: 500;
    color: inherit;
}

.protocol-step-detail {
    font-size: 0.8rem;
    color: #666;
    margin-top: 0.2rem;
}

/* Timer display */
.timer-display {
    text-align: center;
    font-family: 'DM Mono', monospace;
    font-size: 4rem;
    font-weight: 500;
    color: #f87171;
    letter-spacing: 0.05em;
    padding: 1rem 0;
    line-height: 1;
}

.timer-label {
    text-align: center;
    font-size: 0.78rem;
    color: #555;
    font-family: 'DM Mono', monospace;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-bottom: 1.5rem;
}

/* Redistribution log */
.resch-row {
    display: flex;
    justify-content: space-between;
    padding: 0.5rem 0;
    border-bottom: 1px solid #1a1a1a;
    font-size: 0.83rem;
}

.resch-subject { color: #ccc; }
.resch-date    { font-family: 'DM Mono', monospace; color: #555; }

.warning-item {
    background: #1a1000;
    border-left: 3px solid #f59e0b;
    border-radius: 0 8px 8px 0;
    padding: 0.6rem 1rem;
    margin: 0.4rem 0;
    font-size: 0.83rem;
    color: #d97706;
}

.mono { font-family: 'DM Mono', monospace; }

.disclaimer {
    font-size: 0.75rem;
    color: #3a3a3a;
    font-family: 'DM Mono', monospace;
    line-height: 1.6;
    text-align: center;
    margin-top: 2rem;
    padding-top: 1rem;
    border-top: 1px solid #1a1a1a;
}
</style>
""", unsafe_allow_html=True)

# ── Session state initialisation ───────────────────────────────────────────────
# All UI state lives here — nothing is persisted to DB until the user confirms.
if 'emergency_state' not in st.session_state:
    st.session_state.emergency_state = 'idle'
    # States: idle → confirming → active → grounding → recovery → complete

if 'grounding_step' not in st.session_state:
    st.session_state.grounding_step = 0

if 'redistribution_result' not in st.session_state:
    st.session_state.redistribution_result = None

if 'reentry_chosen' not in st.session_state:
    st.session_state.reentry_chosen = None

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="emergency-header">
    <div class="emergency-title">🚨 Emergency Mode</div>
    <div class="emergency-sub">Acute stress intervention · Your schedule will be handled</div>
</div>
""", unsafe_allow_html=True)

# ── Helper: fetch today's plan ─────────────────────────────────────────────────
def get_todays_plan():
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM plans WHERE plan_date = ? AND user_id = 'default'",
            (date.today().isoformat(),)
        ).fetchone()

# ══════════════════════════════════════════════════════════════════════════════
# STATE: IDLE
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.emergency_state == 'idle':

    burnout = get_burnout_score()
    plan    = get_todays_plan()

    # Contextual risk banner
    if burnout:
        level = burnout['level']
        if level == 'red':
            st.markdown("""
            <div class="state-card state-active">
                <strong>Your burnout score is in the HIGH RISK range.</strong><br>
                Emergency mode will cancel today's remaining schedule, redistribute 
                your tasks to future days, and guide you through a 15-minute 
                grounding protocol.
            </div>
            """, unsafe_allow_html=True)
        elif level == 'orange':
            st.markdown("""
            <div class="state-card state-idle">
                Your burnout score is elevated but not critical. Emergency mode 
                is available if you feel you need a full stop today.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="state-card state-idle">
                Your current burnout indicators are not in a critical range. 
                Emergency mode is still available if you are experiencing acute 
                stress that the score does not reflect.
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="state-card state-idle">
            Burnout scoring is not yet active (insufficient baseline data). 
            Emergency mode is still fully available regardless of system phase.
        </div>
        """, unsafe_allow_html=True)

    # What will happen — shown before activation so user knows what to expect
    st.markdown("#### What happens when you activate")
    st.markdown("""
    <div style="font-size:0.87rem; color:#888; line-height:1.9;">
        <span class="mono" style="color:#f87171;">01</span> &nbsp; Today's study schedule is cancelled and logged as deferred.<br>
        <span class="mono" style="color:#f87171;">02</span> &nbsp; All deferred tasks are redistributed to future available days.<br>
        <span class="mono" style="color:#f87171;">03</span> &nbsp; You are guided through a 15-minute grounding protocol.<br>
        <span class="mono" style="color:#f87171;">04</span> &nbsp; After recovery, you choose whether to re-enter with a light task or fully rest.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    if not plan:
        st.warning("No study plan found for today. Generate a plan first before activating Emergency Mode.")
    else:
        col_btn, col_space = st.columns([1, 2])
        with col_btn:
            if st.button("🚨 Activate Emergency Mode", type="primary", use_container_width=True):
                st.session_state.emergency_state = 'confirming'
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# STATE: CONFIRMING
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.emergency_state == 'confirming':

    st.markdown("""
    <div class="state-card state-active">
        <strong>Confirm activation.</strong><br>
        Today's plan will be cancelled. Tasks will be redistributed automatically. 
        This action is logged and cannot be undone for today's date.
    </div>
    """, unsafe_allow_html=True)

    col_confirm, col_cancel = st.columns(2)

    with col_confirm:
        if st.button("✅ Yes, cancel today and begin", type="primary", use_container_width=True):
            st.session_state.emergency_state = 'active'
            st.rerun()

    with col_cancel:
        if st.button("← Go back", use_container_width=True):
            st.session_state.emergency_state = 'idle'
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# STATE: ACTIVE — redistribute tasks, then move to grounding
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.emergency_state == 'active':

    # Only run redistribution once
    if st.session_state.redistribution_result is None:
        plan = get_todays_plan()

        if plan is None:
            st.error("Could not find today's plan. Please go back and generate one first.")
            if st.button("← Back"):
                st.session_state.emergency_state = 'idle'
                st.rerun()
            st.stop()

        with st.spinner("Redistributing your tasks to future days..."):
            try:
                warnings = redistribute_deferred_tasks(plan['plan_id'])
                st.session_state.redistribution_result = {
                    "success":  True,
                    "warnings": warnings,
                    "plan_id":  plan['plan_id']
                }
            except Exception as e:
                st.session_state.redistribution_result = {
                    "success": False,
                    "error":   str(e)
                }

    result = st.session_state.redistribution_result

    if not result['success']:
        st.error(f"Redistribution failed: {result['error']}")
        st.caption("Your plan has not been modified. Please try again or redistribute manually.")
        if st.button("← Back to idle"):
            st.session_state.emergency_state = 'idle'
            st.session_state.redistribution_result = None
            st.rerun()
        st.stop()

    # Show redistribution summary
    st.markdown("### ✅ Schedule cleared")
    st.markdown(
        '<div style="font-size:0.85rem; color:#4ade80; font-family:\'DM Mono\',monospace; margin-bottom:1rem;">'
        'Tasks redistributed to future days. Your exam deadlines are protected.'
        '</div>',
        unsafe_allow_html=True
    )

    # Warnings for tasks that couldn't be placed
    if result['warnings']:
        st.markdown("**Manual attention required:**")
        for w in result['warnings']:
            st.markdown(f'<div class="warning-item">⚠️ {w}</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Ready to begin your grounding protocol?")
    st.markdown(
        '<div style="font-size:0.87rem; color:#888;">15 minutes · 4 steps · No performance required.</div>',
        unsafe_allow_html=True
    )

    if st.button("Begin grounding protocol →", type="primary"):
        st.session_state.emergency_state = 'grounding'
        st.session_state.grounding_step  = 0
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# STATE: GROUNDING — 4-step protocol, one step at a time
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.emergency_state == 'grounding':

    GROUNDING_STEPS = [
        {
            "title":    "Step away from your desk",
            "detail":   "Move to a different room or step outside if possible. Physical distance from your study space matters.",
            "duration": "2 minutes",
            "icon":     "🚶"
        },
        {
            "title":    "Box breathing",
            "detail":   "Inhale for 4 counts → Hold for 4 → Exhale for 4 → Hold for 4. Repeat 6 times. This directly activates your parasympathetic nervous system.",
            "duration": "4 minutes",
            "icon":     "🫁"
        },
        {
            "title":    "5-4-3-2-1 grounding",
            "detail":   "Name 5 things you can see · 4 you can touch · 3 you can hear · 2 you can smell · 1 you can taste. Say them out loud.",
            "duration": "5 minutes",
            "icon":     "🧘"
        },
        {
            "title":    "Drink water and sit quietly",
            "detail":   "No phone, no music. Just sit. Notice if your shoulders are raised — let them drop. You do not need to solve anything right now.",
            "duration": "4 minutes",
            "icon":     "💧"
        },
    ]

    current_step = st.session_state.grounding_step
    total_steps  = len(GROUNDING_STEPS)

    st.markdown(f"### Grounding Protocol &nbsp; <span class='mono' style='font-size:1rem; color:#555;'>{current_step}/{total_steps} complete</span>", unsafe_allow_html=True)

    # Progress bar
    st.progress(current_step / total_steps)
    st.markdown("")

    # Render completed steps (collapsed)
    for i in range(current_step):
        step = GROUNDING_STEPS[i]
        st.markdown(f"""
        <div class="protocol-step done">
            <div class="protocol-step-num">Step {i+1} · Complete ✓</div>
            <div class="protocol-step-text">{step['icon']} {step['title']}</div>
        </div>
        """, unsafe_allow_html=True)

    # Render active step
    if current_step < total_steps:
        step = GROUNDING_STEPS[current_step]
        st.markdown(f"""
        <div class="protocol-step">
            <div class="protocol-step-num">Step {current_step + 1} of {total_steps} · {step['duration']}</div>
            <div class="protocol-step-text">{step['icon']} {step['title']}</div>
            <div class="protocol-step-detail">{step['detail']}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f'<div class="timer-label">Suggested duration</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="timer-display">{step["duration"]}</div>', unsafe_allow_html=True)

        col_done, col_skip = st.columns([2, 1])
        with col_done:
            if st.button(f"✅ Done — next step", type="primary", use_container_width=True):
                st.session_state.grounding_step += 1
                st.rerun()
        with col_skip:
            if st.button("Skip step", use_container_width=True):
                st.session_state.grounding_step += 1
                st.rerun()

    else:
        # All steps complete
        st.session_state.emergency_state = 'recovery'
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# STATE: RECOVERY — light re-entry choice
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.emergency_state == 'recovery':

    st.markdown("""
    <div class="state-card state-recovery">
        <strong>Protocol complete.</strong><br>
        You have finished the grounding sequence. There is no expectation to 
        return to study today. The choice below is entirely optional.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### Optional: light re-entry")
    st.markdown(
        '<div style="font-size:0.87rem; color:#888; margin-bottom:1rem;">'
        'If you feel ready, choose one low-stakes task. If not, choose full rest — '
        'your tasks have already been redistributed.'
        '</div>',
        unsafe_allow_html=True
    )

    reentry_options = [
        "📖 Read notes for 20 minutes (no active recall)",
        "✍️ Rewrite one page of existing notes",
        "🗂️ Organise your study materials",
        "😴 Full rest — I am done for today",
    ]

    chosen = st.radio(
        "What feels right right now?",
        reentry_options,
        index=3,   # Default to full rest
        label_visibility="collapsed"
    )

    if st.button("Confirm and finish", type="primary"):
        st.session_state.reentry_chosen   = chosen
        st.session_state.emergency_state  = 'complete'
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# STATE: COMPLETE
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.emergency_state == 'complete':

    chosen = st.session_state.reentry_chosen
    is_rest = "Full rest" in chosen

    st.markdown("""
    <div class="state-card state-recovery">
        <strong>Emergency session complete.</strong><br>
        Your schedule has been adjusted. Your check-in data has been recorded. 
        The system will account for today when generating tomorrow's plan.
    </div>
    """, unsafe_allow_html=True)

    if is_rest:
        st.markdown("### 😴 Rest well.")
        st.markdown(
            '<div style="font-size:0.9rem; color:#888; line-height:1.8;">'
            'Rest is not lost productivity. Returning tomorrow at reduced capacity '
            'is better than not returning at all. Your plan will be waiting.'
            '</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(f"### You chose: {chosen}")
        st.markdown(
            '<div style="font-size:0.9rem; color:#888; line-height:1.8;">'
            'Keep it light. Stop the moment it stops feeling manageable. '
            'The goal is re-entry, not recovery of lost hours.'
            '</div>',
            unsafe_allow_html=True
        )

    st.markdown("---")

    # Summary log
    result = st.session_state.redistribution_result
    if result and result.get('warnings'):
        st.markdown("**Tasks requiring manual attention:**")
        for w in result['warnings']:
            st.markdown(f'<div class="warning-item">⚠️ {w}</div>', unsafe_allow_html=True)

    # Reset button — starts a fresh session
    st.markdown("")
    if st.button("← Return to dashboard", use_container_width=False):
        for key in ['emergency_state', 'grounding_step', 'redistribution_result', 'reentry_chosen']:
            del st.session_state[key]
        st.switch_page("pages/4_burnout_dashboard.py")

# ── Disclaimer ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="disclaimer">
    Emergency mode is a study management tool, not a mental health intervention.<br>
    If you are experiencing persistent distress, please contact a counsellor or 
    crisis support service. This system cannot assess or respond to clinical need.
</div>
""", unsafe_allow_html=True)
