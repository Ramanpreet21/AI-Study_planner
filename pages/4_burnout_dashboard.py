# pages/3_burnout_dashboard.py

import streamlit as st
import pandas as pd
from datetime import date, timedelta
from engines.burnout_scorer import get_burnout_score
from engines.phase_manager import get_phase, get_log_count
from database.db_manager import get_connection

st.set_page_config(page_title="Burnout Dashboard", page_icon="🧠", layout="wide")

# ── Custom Styling ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Sora:wght@300;400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Sora', sans-serif;
}

.dash-title {
    font-size: 2rem;
    font-weight: 700;
    letter-spacing: -0.03em;
    margin-bottom: 0.2rem;
}

.dash-subtitle {
    font-size: 0.9rem;
    color: #888;
    margin-bottom: 2rem;
    font-weight: 300;
}

/* Risk level cards */
.risk-card {
    border-radius: 16px;
    padding: 1.5rem 1.8rem;
    margin-bottom: 1rem;
}

.risk-low    { background: #0d1f0f; border: 1px solid #1e5c24; color: #4ade80; }
.risk-yellow { background: #1f1a08; border: 1px solid #92610a; color: #fbbf24; }
.risk-orange { background: #1f0f06; border: 1px solid #92420a; color: #fb923c; }
.risk-red    { background: #1f0608; border: 1px solid #7f1d1d; color: #f87171; }

.risk-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    opacity: 0.7;
    margin-bottom: 0.4rem;
}

.risk-score {
    font-size: 3.5rem;
    font-weight: 700;
    line-height: 1;
    font-family: 'DM Mono', monospace;
}

.risk-level-text {
    font-size: 1rem;
    font-weight: 600;
    margin-top: 0.5rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

/* Signal breakdown row */
.signal-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.6rem 0;
    border-bottom: 1px solid #1e1e1e;
    font-size: 0.88rem;
}

.signal-name  { color: #aaa; font-weight: 400; }
.signal-value { font-family: 'DM Mono', monospace; color: #eee; font-weight: 500; }
.signal-weight { font-family: 'DM Mono', monospace; color: #555; font-size: 0.78rem; }

/* Phase banner */
.phase-banner {
    background: #111;
    border: 1px solid #2a2a2a;
    border-radius: 10px;
    padding: 1rem 1.4rem;
    font-family: 'DM Mono', monospace;
    font-size: 0.8rem;
    color: #666;
    margin-bottom: 1.5rem;
}

.phase-banner span { color: #eee; }

/* Trend table */
.trend-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
    color: #555;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 0.5rem;
}

/* Intervention box */
.intervention-box {
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    margin-top: 1rem;
    font-size: 0.88rem;
    line-height: 1.6;
}

.intervention-yellow { background: #1a1500; border-left: 3px solid #fbbf24; color: #d4a017; }
.intervention-orange { background: #180e00; border-left: 3px solid #fb923c; color: #d97706; }
.intervention-red    { background: #180005; border-left: 3px solid #f87171; color: #ef4444; }

.mono { font-family: 'DM Mono', monospace; }
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="dash-title">🧠 Burnout Dashboard</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="dash-subtitle">Personal baseline monitoring · {date.today().strftime("%A, %B %d %Y")}</div>',
    unsafe_allow_html=True
)

# ── Phase gate ─────────────────────────────────────────────────────────────────
phase     = get_phase()
log_count = get_log_count()

st.markdown(
    f'<div class="phase-banner">System phase: <span>{phase.replace("_", " ").upper()}</span>'
    f' &nbsp;·&nbsp; Logs collected: <span>{log_count} / 14</span>'
    f' &nbsp;·&nbsp; Burnout scoring: <span>{"active" if phase != "cold_start" else "unlocks at day 7"}</span></div>',
    unsafe_allow_html=True
)

if phase == 'cold_start':
    st.info(
        f"**Burnout detection is not yet active.** The system needs at least 7 days of "
        f"check-in data to establish your personal baseline. You have {log_count} day(s) logged. "
        f"Keep completing your daily check-ins."
    )
    st.stop()

# ── Fetch score ────────────────────────────────────────────────────────────────
result = get_burnout_score()

if result is None:
    st.warning("Not enough data to compute a burnout score yet. Complete your daily check-in.")
    st.stop()

score = result['score']
level = result['level']
days  = result['days_used']

LEVEL_CONFIG = {
    "low":    {"css": "risk-low",    "label": "LOW RISK",    "emoji": "✅", "color": "#4ade80"},
    "yellow": {"css": "risk-yellow", "label": "WATCH",       "emoji": "⚠️", "color": "#fbbf24"},
    "orange": {"css": "risk-orange", "label": "ELEVATED",    "emoji": "🔶", "color": "#fb923c"},
    "red":    {"css": "risk-red",    "label": "HIGH RISK",   "emoji": "🔴", "color": "#f87171"},
}

cfg = LEVEL_CONFIG[level]

# ── Main layout ────────────────────────────────────────────────────────────────
col_score, col_signals, col_trend = st.columns([1.2, 1.4, 1.4])

# ── Score card ─────────────────────────────────────────────────────────────────
with col_score:
    st.markdown(f"""
    <div class="risk-card {cfg['css']}">
        <div class="risk-label">Composite Burnout Score</div>
        <div class="risk-score">{score:+.2f}</div>
        <div class="risk-level-text">{cfg['emoji']} {cfg['label']}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="font-size:0.78rem; color:#555; font-family:'DM Mono',monospace; margin-top:0.5rem;">
        Based on {days} days of personal baseline data.<br>
        Score = weighted Z-score vs. your own mean.
    </div>
    """, unsafe_allow_html=True)

    # Threshold reference
    st.markdown("---")
    st.markdown('<div class="trend-label">Threshold Reference</div>', unsafe_allow_html=True)
    thresholds = [
        ("< 1.0",  "Low",      "#4ade80"),
        ("1.0–1.5","Watch",    "#fbbf24"),
        ("1.5–2.0","Elevated", "#fb923c"),
        ("≥ 2.0",  "High",     "#f87171"),
    ]
    for rng, lbl, clr in thresholds:
        active = "→ " if lbl.lower() == level or lbl.lower().startswith(level) else "  "
        st.markdown(
            f'<div class="signal-row">'
            f'<span class="signal-name mono">{active}{rng}</span>'
            f'<span style="color:{clr}; font-family:\'DM Mono\',monospace; font-size:0.82rem;">{lbl}</span>'
            f'</div>',
            unsafe_allow_html=True
        )

# ── Signal breakdown ───────────────────────────────────────────────────────────
with col_signals:
    st.markdown('<div class="trend-label">Signal Breakdown (Today vs. Your Baseline)</div>', unsafe_allow_html=True)

    with get_connection() as conn:
        today_log = conn.execute("""
            SELECT mood_score, energy_score, stress_score, sleep_hours
            FROM daily_logs
            WHERE user_id = 'default'
            ORDER BY log_date DESC LIMIT 1
        """).fetchone()

        baseline = conn.execute("""
            SELECT 
                AVG(mood_score)   as avg_mood,
                AVG(energy_score) as avg_energy,
                AVG(stress_score) as avg_stress,
                AVG(sleep_hours)  as avg_sleep
            FROM (
                SELECT mood_score, energy_score, stress_score, sleep_hours
                FROM daily_logs WHERE user_id = 'default'
                ORDER BY log_date DESC LIMIT 14
            )
        """).fetchone()

    if today_log and baseline:
        signals = [
            ("Stress",  today_log['stress_score'], baseline['avg_stress'], "30%", False),
            ("Mood",    today_log['mood_score'],   baseline['avg_mood'],   "25%", True),
            ("Energy",  today_log['energy_score'], baseline['avg_energy'], "20%", True),
            ("Sleep",   today_log['sleep_hours'],  baseline['avg_sleep'],  "15%", True),
        ]

        for name, today_val, base_val, weight, lower_is_worse in signals:
            if base_val:
                delta    = today_val - base_val
                # For inverted signals: below baseline = bad (red), above = good (green)
                # For stress: above baseline = bad (red), below = good (green)
                is_worse = (delta < 0) if lower_is_worse else (delta > 0)
                arrow    = "↓" if delta < 0 else "↑"
                clr      = "#f87171" if is_worse else "#4ade80"
                st.markdown(
                    f'<div class="signal-row">'
                    f'<span class="signal-name">{name}</span>'
                    f'<span class="signal-value">{today_val} '
                    f'<span style="color:{clr}; font-size:0.78rem;">{arrow}{abs(delta):.1f}</span></span>'
                    f'<span class="signal-weight">{weight}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
    else:
        st.caption("Complete today's check-in to see signal breakdown.")

# ── 14-day trend chart ─────────────────────────────────────────────────────────
with col_trend:
    st.markdown('<div class="trend-label">14-Day Score Trend</div>', unsafe_allow_html=True)

    # Build historical scores — compute for each available day
    with get_connection() as conn:
        history = conn.execute("""
            SELECT log_date, mood_score, energy_score, stress_score, sleep_hours
            FROM daily_logs
            WHERE user_id = 'default'
            ORDER BY log_date ASC
            LIMIT 14
        """).fetchall()

    if len(history) >= 3:
        def simple_zscore_batch(rows):
            """Compute a simplified burnout proxy for trend visualization."""
            scores = []
            stress_vals  = [r['stress_score']  for r in rows]
            mood_vals    = [r['mood_score']     for r in rows]
            energy_vals  = [r['energy_score']   for r in rows]
            sleep_vals   = [r['sleep_hours']    for r in rows]

            def mean(l): return sum(l) / len(l) if l else 0
            def std(l):
                m = mean(l)
                return (sum((x - m)**2 for x in l) / len(l))**0.5 if len(l) > 1 else 0

            for i, row in enumerate(rows):
                # Use expanding window for trend (only past data available at that point)
                window = rows[:i+1]
                w_stress = [r['stress_score']  for r in window]
                w_mood   = [r['mood_score']     for r in window]
                w_energy = [r['energy_score']   for r in window]
                w_sleep  = [r['sleep_hours']    for r in window]

                def z(val, lst):
                    m, s = mean(lst), std(lst)
                    return (val - m) / s if s > 0 else 0.0

                score = (
                    0.30 *  z(row['stress_score'],  w_stress) +
                    0.25 * -z(row['mood_score'],     w_mood)   +
                    0.20 * -z(row['energy_score'],   w_energy) +
                    0.15 * -z(row['sleep_hours'],    w_sleep)
                )
                scores.append({"Date": row['log_date'], "Burnout Score": round(score, 3)})
            return scores

        trend_data = simple_zscore_batch(history)
        df = pd.DataFrame(trend_data).set_index("Date")

        st.line_chart(df, color=cfg['color'], height=200)

        # Risk band reference lines as caption
        st.markdown(
            '<div style="font-size:0.72rem; color:#444; font-family:\'DM Mono\',monospace;">'
            'Watch ≥ 1.0 &nbsp;·&nbsp; Elevated ≥ 1.5 &nbsp;·&nbsp; High ≥ 2.0'
            '</div>',
            unsafe_allow_html=True
        )
    else:
        st.caption("Need at least 3 days of data to show trend.")

# ── Intervention message ───────────────────────────────────────────────────────
st.markdown("---")

if level == "low":
    st.success("✅ Your burnout indicators are within your normal range. No intervention needed.")

elif level == "yellow":
    st.markdown("""
    <div class="intervention-box intervention-yellow">
        <strong>⚠️ Advisory:</strong> One or more of your signals is trending slightly outside 
        your personal baseline. No plan changes have been made. Monitor your check-ins over the 
        next 2–3 days. Consider whether your current workload is sustainable.
    </div>
    """, unsafe_allow_html=True)

elif level == "orange":
    st.markdown("""
    <div class="intervention-box intervention-orange">
        <strong>🔶 Intervention Active:</strong> Your burnout score has crossed the elevated 
        threshold. Today's study intensity has been reduced by 25% and any tasks rated 
        difficulty 8+ have been pushed to tomorrow. This adjustment was logged automatically.
    </div>
    """, unsafe_allow_html=True)

elif level == "red":
    st.markdown("""
    <div class="intervention-box intervention-red">
        <strong>🔴 High Risk Detected:</strong> Your composite score indicates significant 
        deviation from your personal baseline across multiple signals. Today's plan has been 
        capped at 2 hours. Consider activating Emergency Mode if you are experiencing acute stress.
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/5_emergency.py", label="→ Go to Emergency Mode", icon="🚨")

# ── Disclaimer ─────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    '<div style="font-size:0.75rem; color:#444; font-family:\'DM Mono\',monospace; line-height:1.6;">'
    'Scores are Z-scored against your personal 14-day rolling baseline, not a population norm. '
    'This system does not diagnose burnout. If you are experiencing persistent distress, '
    'please speak with a counsellor or healthcare professional.'
    '</div>',
    unsafe_allow_html=True
)
