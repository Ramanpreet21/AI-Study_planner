# app.py

import streamlit as st
from database.db_manager import initialize_db
from engines.phase_manager import get_phase, get_log_count
from engines.burnout_scorer import get_burnout_score
from datetime import date

# ── Initialize database on first run ──────────────────────────────────────────
# This is the only place initialize_db() is called. Every other module
# assumes the database already exists and never calls this themselves.
initialize_db()

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title  = "Study Planner",
    page_icon   = "🎓",
    layout      = "wide",
    initial_sidebar_state = "expanded",
)

# ── Global styling ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Sora:wght@300;400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Sora', sans-serif;
    background-color: #050505;
    color: #ccc;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #080808;
    border-right: 1px solid #141414;
}

[data-testid="stSidebar"] * {
    font-family: 'Sora', sans-serif !important;
}

/* Sidebar nav labels */
[data-testid="stSidebarNav"] a {
    font-size: 0.88rem;
    color: #666 !important;
    padding: 0.4rem 0.8rem;
    border-radius: 8px;
    transition: background 0.15s;
}

[data-testid="stSidebarNav"] a:hover {
    background: #111 !important;
    color: #ddd !important;
}

[data-testid="stSidebarNav"] a[aria-current="page"] {
    background: #0d1f35 !important;
    color: #60a5fa !important;
}

/* Remove default Streamlit top padding */
.block-container { padding-top: 2rem; }

/* Scrollbar */
::-webkit-scrollbar       { width: 4px; }
::-webkit-scrollbar-track { background: #080808; }
::-webkit-scrollbar-thumb { background: #222; border-radius: 2px; }

/* Buttons */
.stButton button {
    font-family: 'Sora', sans-serif !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
}

/* Metrics */
[data-testid="stMetric"] {
    background: #080808;
    border: 1px solid #1a1a1a;
    border-radius: 12px;
    padding: 0.8rem 1rem;
}

/* Inputs */
.stSlider, .stNumberInput, .stSelectbox, .stTextInput {
    font-family: 'Sora', sans-serif !important;
}

/* Toast */
[data-testid="stToast"] {
    background: #111 !important;
    color: #ddd !important;
    border: 1px solid #222 !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.8rem !important;
}
</style>
""", unsafe_allow_html=True)

# ── Sidebar status panel ───────────────────────────────────────────────────────
# Shown on every page — gives the user a persistent system status strip
# without requiring them to navigate to the burnout dashboard.

with st.sidebar:
    st.markdown("""
    <div style="
        font-family:'DM Mono',monospace;
        font-size:0.68rem;
        text-transform:uppercase;
        letter-spacing:0.14em;
        color:#333;
        padding: 0.5rem 0 0.3rem 0;
        margin-bottom:0.5rem;
        border-bottom:1px solid #141414;
    ">System Status</div>
    """, unsafe_allow_html=True)

    # Phase
    phase     = get_phase()
    log_count = get_log_count()

    PHASE_COLORS = {
        'cold_start':    '#60a5fa',
        'bootstrapping': '#fbbf24',
        'adaptive':      '#4ade80',
    }
    phase_color = PHASE_COLORS[phase]
    phase_label = phase.replace('_', ' ').title()

    st.markdown(f"""
    <div style="
        display:flex; justify-content:space-between; align-items:center;
        padding:0.5rem 0; border-bottom:1px solid #0f0f0f; font-size:0.82rem;
    ">
        <span style="color:#555;">Phase</span>
        <span style="
            font-family:'DM Mono',monospace;
            color:{phase_color};
            font-size:0.78rem;
        ">{phase_label}</span>
    </div>
    """, unsafe_allow_html=True)

    # Days logged
    progress_pct = min(log_count / 14, 1.0) * 100
    st.markdown(f"""
    <div style="padding:0.5rem 0; border-bottom:1px solid #0f0f0f;">
        <div style="
            display:flex; justify-content:space-between;
            font-size:0.82rem; margin-bottom:0.4rem;
        ">
            <span style="color:#555;">Days logged</span>
            <span style="
                font-family:'DM Mono',monospace; color:#888;
                font-size:0.78rem;
            ">{log_count} / 14</span>
        </div>
        <div style="height:2px; background:#111; border-radius:1px; overflow:hidden;">
            <div style="
                height:100%; width:{progress_pct:.0f}%;
                background:linear-gradient(90deg,#2E75B6,#4ade80);
                border-radius:1px;
            "></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Burnout level
    burnout = get_burnout_score()

    BURNOUT_COLORS = {
        'low':    '#4ade80',
        'yellow': '#fbbf24',
        'orange': '#fb923c',
        'red':    '#f87171',
        }

    if burnout:
        b_color = BURNOUT_COLORS[burnout['level']]
        b_label = burnout['level'].upper()
        b_score = f"{burnout['score']:+.2f}"
    else:
        b_color = '#333'
        b_label = 'NOT ACTIVE'
        b_score = '—'

    st.markdown(f"""
    <div style="
        display:flex; justify-content:space-between; align-items:center;
        padding:0.5rem 0; border-bottom:1px solid #0f0f0f; font-size:0.82rem;
    ">
        <span style="color:#555;">Burnout</span>
        <span style="
            font-family:'DM Mono',monospace;
            color:{b_color};
            font-size:0.78rem;
        ">{b_label} {b_score}</span>
    </div>
    """, unsafe_allow_html=True)

    # Today's plan status
    with __import__('database.db_manager', fromlist=['get_connection']).get_connection() as conn:
        today_plan = conn.execute(
            "SELECT output_allocated_hours, output_completion_pct, output_capped "
            "FROM plans WHERE plan_date = ? AND user_id = 'default'",
            (date.today().isoformat(),)
        ).fetchone()

    if today_plan:
        completion_str = (
            f"{today_plan['output_completion_pct']:.0f}%"
            if today_plan['output_completion_pct'] is not None
            else "pending"
        )
        capped_str = " · capped" if today_plan['output_capped'] else ""
        plan_str   = f"{today_plan['output_allocated_hours']:.1f}h · {completion_str}{capped_str}"
        plan_color = "#ddd"
    else:
        plan_str   = "not generated"
        plan_color = "#333"

    st.markdown(f"""
    <div style="
        display:flex; justify-content:space-between; align-items:center;
        padding:0.5rem 0; border-bottom:1px solid #0f0f0f; font-size:0.82rem;
    ">
        <span style="color:#555;">Today's plan</span>
        <span style="
            font-family:'DM Mono',monospace;
            color:{plan_color};
            font-size:0.76rem;
        ">{plan_str}</span>
    </div>
    """, unsafe_allow_html=True)

    # Today's check-in status
    with __import__('database.db_manager', fromlist=['get_connection']).get_connection() as conn:
        today_log = conn.execute(
            "SELECT mood_score, stress_score FROM daily_logs "
            "WHERE log_date = ? AND user_id = 'default'",
            (date.today().isoformat(),)
        ).fetchone()

    if today_log:
        log_str   = f"mood {today_log['mood_score']} · stress {today_log['stress_score']}"
        log_color = "#ddd"
    else:
        log_str   = "not submitted"
        log_color = "#f59e0b"   # amber — actionable missing item

    st.markdown(f"""
    <div style="
        display:flex; justify-content:space-between; align-items:center;
        padding:0.5rem 0; font-size:0.82rem;
    ">
        <span style="color:#555;">Check-in</span>
        <span style="
            font-family:'DM Mono',monospace;
            color:{log_color};
            font-size:0.76rem;
        ">{log_str}</span>
    </div>
    """, unsafe_allow_html=True)

    # Emergency mode shortcut — always visible, prominent when burnout is red
    st.markdown("<br>", unsafe_allow_html=True)

    if burnout and burnout['level'] == 'red':
        st.markdown("""
        <div style="
            background:#180005;
            border:1px solid #7f1d1d;
            border-radius:10px;
            padding:0.7rem 1rem;
            font-size:0.78rem;
            color:#f87171;
            font-family:'DM Mono',monospace;
            margin-bottom:0.6rem;
            text-align:center;
        ">
            🔴 High burnout detected
        </div>
        """, unsafe_allow_html=True)

    st.page_link("pages/4_burnout_dashborad.py", label="Emergency Mode", icon="🚨")

    # Daily flow reminder
    st.markdown("""
    <div style="
        font-family:'DM Mono',monospace;
        font-size:0.65rem;
        color:#222;
        line-height:1.8;
        margin-top:1.4rem;
        padding-top:0.8rem;
        border-top:1px solid #0f0f0f;
    ">
        Daily flow:<br>
        Check-in → Plan → Study → End of Day
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# HOME PAGE CONTENT
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div style="
    font-size:2.4rem;
    font-weight:700;
    letter-spacing:-0.04em;
    margin-bottom:0.3rem;
    line-height:1.1;
">
    Adaptive Study Planner
</div>
<div style="
    font-size:0.9rem;
    color:#555;
    font-weight:300;
    margin-bottom:2.5rem;
">
    Burnout detection · Behavioral feedback · Sustainable performance
</div>
""", unsafe_allow_html=True)

# ── Daily action card ──────────────────────────────────────────────────────────
# Figures out what the user should do next and surfaces it prominently.

st.markdown("""
<div style="
    font-family:'DM Mono',monospace;
    font-size:0.68rem;
    text-transform:uppercase;
    letter-spacing:0.14em;
    color:#333;
    margin-bottom:0.6rem;
">Next action</div>
""", unsafe_allow_html=True)

# Determine what's missing today in priority order
if not today_log:
    next_action = {
        "title":  "Complete your daily check-in",
        "body":   "Mood, energy, stress, and sleep data has not been submitted today. "
                  "The burnout scorer and plan generator use this data.",
        "page":   "pages/1_daily_checkin.py",
        "label":  "Go to Check-in",
        "icon":   "📋",
        "border": "#2E75B6",
    }
elif not today_plan:
    next_action = {
        "title":  "Generate today's study plan",
        "body":   "Check-in complete. Your behavioral signals are ready. "
                  "Generate an optimised plan for today.",
        "page":   "pages/2_study_plan.py",
        "label":  "Go to Study Plan",
        "icon":   "📅",
        "border": "#4ade80",
    }
elif today_plan and today_plan['output_completion_pct'] is None:
    next_action = {
        "title":  "Log your end-of-day completion",
        "body":   "Plan generated. When your study session ends, log what "
                  "percentage of tasks you completed. This feeds the Reality Check Engine.",
        "page":   "pages/3_end_of_the_day.py",
        "label":  "Go to End of Day",
        "icon":   "🌙",
        "border": "#f59e0b",
    }
else:
    next_action = {
        "title":  "All done for today",
        "body":   f"Check-in logged · Plan generated · "
                  f"Completion: {today_plan['output_completion_pct']:.0f}%. "
                  f"Check your burnout dashboard or insights if you want to review your data.",
        "page":   "pages/4_burnout_dashboard.py",
        "label":  "View Burnout Dashboard",
        "icon":   "🧠",
        "border": "#4ade80",
    }

st.markdown(f"""
<div style="
    background:#080808;
    border:1px solid #1a1a1a;
    border-left:3px solid {next_action['border']};
    border-radius:0 14px 14px 0;
    padding:1.4rem 1.8rem;
    margin-bottom:2rem;
">
    <div style="font-size:1rem; font-weight:600; color:#ddd; margin-bottom:0.4rem;">
        {next_action['icon']} {next_action['title']}
    </div>
    <div style="font-size:0.85rem; color:#666; line-height:1.65; margin-bottom:1rem;">
        {next_action['body']}
    </div>
</div>
""", unsafe_allow_html=True)

st.page_link(next_action['page'], label=next_action['label'], icon=next_action['icon'])

# ── System overview cards ──────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<div style="
    font-family:'DM Mono',monospace;
    font-size:0.68rem;
    text-transform:uppercase;
    letter-spacing:0.14em;
    color:#333;
    margin-bottom:0.8rem;
">All pages</div>
""", unsafe_allow_html=True)

pages = [
    ("📋", "Daily Check-in",      "Log mood, energy, stress, and sleep.",
     "pages/1_daily_checkin.py"),
    ("📅", "Study Plan",          "Generate today's optimised schedule.",
     "pages/2_study_plan.py"),
    ("🌙", "End of Day",          "Log task completion and close the loop.",
     "pages/3_end_of_the_day.py"),
    ("🧠", "Burnout Dashboard",   "14-day trend and composite risk score.",
     "pages/4_burnout_dashborad.py"),
    ("📊", "Insights",            "Spearman correlations after 14+ days.",
     "pages/5_insights.py"),
    ("🚨", "Emergency Mode",      "Cancel today and begin grounding protocol.",
     "pages/6_emergency.py"),
]

cols = st.columns(3)

for idx, (icon, title, desc, page) in enumerate(pages):
    with cols[idx % 3]:
        st.markdown(f"""
        <div style="
            background:#080808;
            border:1px solid #1a1a1a;
            border-radius:12px;
            padding:1.1rem 1.3rem;
            margin-bottom:0.8rem;
            min-height:100px;
        ">
            <div style="font-size:1.3rem; margin-bottom:0.4rem;">{icon}</div>
            <div style="
                font-size:0.88rem;
                font-weight:600;
                color:#ccc;
                margin-bottom:0.3rem;
            ">{title}</div>
            <div style="font-size:0.78rem; color:#444; line-height:1.5;">{desc}</div>
        </div>
        """, unsafe_allow_html=True)
        st.page_link(page, label=f"Open {title}", icon=icon)

# ── Architecture note ──────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)

with st.expander("System architecture notes", expanded=False):
    st.markdown("""
    **Feedback loop separation**  
    `plan_generator.py` (Pipeline A) reads only plan input columns. 
    `evaluator.py` (Pipeline B) reads only plan outcome columns. 
    The only permitted bridge is `feedback_splitter.py`, which exposes 
    a single hours-cap value derived from rolling completion rate.

    **Cold start handling**  
    `phase_manager.py` gates all adaptive features behind data thresholds. 
    Fewer than 7 logs: cold start, fixed 80% buffer only. 
    7–13 logs: bootstrapping, Reality Check and burnout scorer active. 
    14+ logs: adaptive, all features including correlation insights active.

    **Correlation honesty**  
    `insights_engine.py` uses Spearman rank correlation with a p < 0.10 
    threshold. All output uses observational language templates. 
    Causal framing is architecturally prohibited — no insight statement 
    uses causal language and every insight appends a confounder note.

    **Burnout scoring**  
    Composite Z-score weighted across stress (30%), mood (25%), energy (20%), 
    sleep (15%), completion (10%). All signals are normalised against the 
    user's personal 14-day rolling baseline, not a population norm.
    """)

# ── Disclaimer ─────────────────────────────────────────────────────────────────
st.markdown("""
<div style="
    font-size:0.73rem;
    color:#1e1e1e;
    font-family:'DM Mono',monospace;
    line-height:1.6;
    text-align:center;
    margin-top:3rem;
    padding-top:1rem;
    border-top:1px solid #0f0f0f;
">
    This system monitors study patterns only. It does not assess or respond to clinical need.<br>
    If you are experiencing persistent distress, please contact a counsellor or support service.
</div>
""", unsafe_allow_html=True)
