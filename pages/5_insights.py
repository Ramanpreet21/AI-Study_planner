# pages/5_insights.py

import streamlit as st
import pandas as pd
from engines.insights_engine import get_insights
from engines.phase_manager import get_phase, get_log_count
from database.db_manager import get_connection

st.set_page_config(page_title="Behavioral Insights", page_icon="📊", layout="wide")

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

/* Gate banner */
.gate-banner {
    background: #0f0f0f;
    border: 1px solid #222;
    border-radius: 12px;
    padding: 1.4rem 1.8rem;
    margin-bottom: 1.5rem;
}

.gate-title {
    font-size: 1rem;
    font-weight: 600;
    color: #aaa;
    margin-bottom: 0.4rem;
}

.gate-body {
    font-size: 0.85rem;
    color: #555;
    line-height: 1.7;
}

.gate-progress {
    height: 3px;
    background: #1a1a1a;
    border-radius: 2px;
    margin: 0.8rem 0 0.4rem 0;
    overflow: hidden;
}

.gate-progress-fill {
    height: 100%;
    border-radius: 2px;
    background: linear-gradient(90deg, #2E75B6, #4ade80);
}

/* Insight card */
.insight-card {
    background: #080808;
    border: 1px solid #1a1a1a;
    border-radius: 16px;
    padding: 1.6rem 1.8rem;
    margin-bottom: 1.2rem;
    position: relative;
}

.insight-card:hover {
    border-color: #2a2a2a;
}

.insight-signal-tag {
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    padding: 0.2rem 0.7rem;
    border-radius: 20px;
    display: inline-block;
    margin-bottom: 0.9rem;
}

.tag-sleep   { background: #0d1f35; color: #60a5fa; border: 1px solid #1e3d6e; }
.tag-mood    { background: #1a0d2e; color: #c084fc; border: 1px solid #3d1f6e; }
.tag-energy  { background: #1a1a08; color: #fbbf24; border: 1px solid #6e5a1f; }
.tag-stress  { background: #1a0d0d; color: #f87171; border: 1px solid #6e1f1f; }

.insight-text {
    font-size: 0.92rem;
    color: #ccc;
    line-height: 1.75;
    margin-bottom: 1rem;
}

.insight-confounder {
    font-size: 0.78rem;
    color: #444;
    line-height: 1.6;
    border-top: 1px solid #111;
    padding-top: 0.8rem;
    font-family: 'DM Mono', monospace;
}

/* Stat pills */
.stat-row {
    display: flex;
    gap: 0.6rem;
    margin-bottom: 0.8rem;
    flex-wrap: wrap;
}

.stat-pill {
    font-family: 'DM Mono', monospace;
    font-size: 0.75rem;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    background: #111;
    border: 1px solid #222;
    color: #666;
}

.stat-pill.positive { border-color: #1e5c24; color: #4ade80; }
.stat-pill.negative { border-color: #7f1d1d; color: #f87171; }
.stat-pill.neutral  { border-color: #333;    color: #888;    }

/* Scatter section */
.chart-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #444;
    margin-bottom: 0.5rem;
}

/* Empty state */
.empty-state {
    text-align: center;
    padding: 3rem 2rem;
    color: #444;
}

.empty-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
    opacity: 0.4;
}

.empty-title {
    font-size: 1rem;
    font-weight: 600;
    color: #555;
    margin-bottom: 0.5rem;
}

.empty-body {
    font-size: 0.83rem;
    color: #3a3a3a;
    line-height: 1.6;
}

/* Causality warning banner */
.causality-banner {
    background: #0a0a0a;
    border: 1px solid #1e1e1e;
    border-left: 3px solid #2E75B6;
    border-radius: 0 10px 10px 0;
    padding: 0.9rem 1.3rem;
    font-size: 0.8rem;
    color: #555;
    line-height: 1.65;
    margin-bottom: 1.8rem;
    font-family: 'DM Mono', monospace;
}

.causality-banner strong { color: #888; }

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
st.markdown('<div class="page-title">📊 Behavioral Insights</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="page-sub">Spearman rank correlations · Observational patterns only · '
    'No causal claims</div>',
    unsafe_allow_html=True
)

# ── Phase gate ─────────────────────────────────────────────────────────────────
phase     = get_phase()
log_count = get_log_count()

# Count how many plans have completion data (needed for insights join)
with get_connection() as conn:
    completion_count = conn.execute("""
        SELECT COUNT(*) as cnt FROM plans
        WHERE user_id = 'default'
        AND output_completion_pct IS NOT NULL
    """).fetchone()['cnt']

INSIGHT_MIN_DAYS     = 14
INSIGHT_MIN_OUTCOMES = 14

days_pct    = min(log_count       / INSIGHT_MIN_DAYS,     1.0) * 100
outcome_pct = min(completion_count / INSIGHT_MIN_OUTCOMES, 1.0) * 100
overall_pct = min(days_pct, outcome_pct)

if phase != 'adaptive' or completion_count < INSIGHT_MIN_OUTCOMES:
    st.markdown(f"""
    <div class="gate-banner">
        <div class="gate-title">🔒 Insights not yet available</div>
        <div class="gate-body">
            The insights engine requires 14 days of check-ins AND 14 days of 
            logged task completion before running correlation analysis. 
            Surfacing patterns on small samples produces misleading results.
            <br><br>
            <span class="mono" style="color:#666;">
                Check-in days: {log_count} / {INSIGHT_MIN_DAYS} &nbsp;·&nbsp;
                Completion outcomes: {completion_count} / {INSIGHT_MIN_OUTCOMES}
            </span>
        </div>
        <div class="gate-progress">
            <div class="gate-progress-fill" style="width:{overall_pct:.1f}%"></div>
        </div>
        <div style="font-family:'DM Mono',monospace; font-size:0.72rem; color:#444;">
            {overall_pct:.0f}% of minimum data collected
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Show what will be available — sets expectations
    st.markdown("#### What unlocks here")
    st.markdown("""
    <div style="font-size:0.87rem; color:#555; line-height:2;">
        <span class="mono" style="color:#2E75B6;">→</span> &nbsp;
        Correlation between sleep duration and task completion rate<br>
        <span class="mono" style="color:#2E75B6;">→</span> &nbsp;
        Relationship between stress level and productive output<br>
        <span class="mono" style="color:#2E75B6;">→</span> &nbsp;
        Mood and energy patterns across your study days<br>
        <span class="mono" style="color:#2E75B6;">→</span> &nbsp;
        All insights shown with r-value, p-value, and sample size<br>
        <span class="mono" style="color:#2E75B6;">→</span> &nbsp;
        No recommendations — patterns only, with confounder notes
    </div>
    """, unsafe_allow_html=True)

    st.stop()

# ── Causality disclaimer — shown before every insight ─────────────────────────
st.markdown("""
<div class="causality-banner">
    <strong>How to read these insights:</strong> All patterns below are 
    Spearman rank correlations between your behavioral signals and task 
    completion rate. Correlation does not establish causation. Each insight 
    notes that a third variable may explain the pattern. No behavioral 
    recommendations are made by this system.
</div>
""", unsafe_allow_html=True)

# ── Fetch insights ─────────────────────────────────────────────────────────────
insights = get_insights()

SIGNAL_TAG_CLASS = {
    'sleep_hours':   ('Sleep',  'tag-sleep'),
    'mood_score':    ('Mood',   'tag-mood'),
    'energy_score':  ('Energy', 'tag-energy'),
    'stress_score':  ('Stress', 'tag-stress'),
}

# ── No significant findings ────────────────────────────────────────────────────
if not insights:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-icon">🔍</div>
        <div class="empty-title">No significant patterns found yet</div>
        <div class="empty-body">
            The engine ran but found no correlations meeting the p &lt; 0.10 threshold 
            in your current data. This is a valid result — it means your behavioral 
            signals and completion rate are not yet showing a consistent relationship.<br><br>
            Continue logging daily check-ins and end-of-day completion rates. 
            Patterns typically emerge after 3–4 weeks of consistent data.
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Layout: insight cards + raw data ──────────────────────────────────────────
col_insights, col_data = st.columns([1.5, 1])

with col_insights:
    st.markdown(
        f'<div class="chart-label">{len(insights)} pattern{"s" if len(insights) != 1 else ""} '
        f'found · p &lt; 0.10 threshold · N = {insights[0]["p"] and insights[0].get("n", "—")}</div>',
        unsafe_allow_html=True
    )

    for insight in insights:
        signal   = insight['signal']
        rho      = insight['rho']
        p_val    = insight['p']
        tag_name, tag_cls = SIGNAL_TAG_CLASS.get(signal, ('Unknown', 'tag-sleep'))

        direction     = "positive" if rho > 0 else "negative"
        strength_word = (
            "weak"     if abs(rho) < 0.3 else
            "moderate" if abs(rho) < 0.6 else
            "strong"
        )

        # Stat pills
        rho_cls = "positive" if rho > 0 else "negative"
        p_cls   = "positive" if p_val < 0.05 else "neutral"

        # Split insight text from confounder note
        # insights_engine always appends the confounder sentence last
        text_parts = insight['text'].split("This is an observed pattern")
        main_text   = text_parts[0].strip()
        confounder  = "This is an observed pattern" + text_parts[1] if len(text_parts) > 1 else ""

        st.markdown(f"""
        <div class="insight-card">
            <span class="insight-signal-tag {tag_cls}">{tag_name}</span>
            <div class="stat-row">
                <span class="stat-pill {rho_cls}">r = {rho:+.2f}</span>
                <span class="stat-pill {p_cls}">p = {p_val:.3f}</span>
                <span class="stat-pill neutral">{strength_word} {direction} correlation</span>
            </div>
            <div class="insight-text">{main_text}</div>
            <div class="insight-confounder">⚠ {confounder}</div>
        </div>
        """, unsafe_allow_html=True)

with col_data:
    st.markdown('<div class="chart-label">Raw signal vs. completion data</div>', unsafe_allow_html=True)

    # Fetch joined data for scatter plots
    with get_connection() as conn:
        raw_rows = conn.execute("""
            SELECT
                l.log_date,
                l.sleep_hours,
                l.mood_score,
                l.energy_score,
                l.stress_score,
                p.output_completion_pct as completion
            FROM daily_logs l
            JOIN plans p ON l.log_date = p.plan_date
            WHERE l.user_id = 'default'
            AND p.output_completion_pct IS NOT NULL
            ORDER BY l.log_date ASC
            LIMIT 60
        """).fetchall()

    if raw_rows:
        df = pd.DataFrame([dict(r) for r in raw_rows])

        # Signal selector
        signal_options = {
            'Sleep Hours':    'sleep_hours',
            'Mood Score':     'mood_score',
            'Energy Score':   'energy_score',
            'Stress Score':   'stress_score',
        }

        selected_label = st.selectbox(
            "Plot signal vs. completion",
            options=list(signal_options.keys()),
            label_visibility="collapsed"
        )
        selected_col = signal_options[selected_label]

        # Scatter via st.scatter_chart
        plot_df = df[['log_date', selected_col, 'completion']].copy()
        plot_df = plot_df.rename(columns={
            selected_col: selected_label,
            'completion': 'Completion %'
        }).set_index('log_date')

        st.scatter_chart(plot_df, x=selected_label, y='Completion %', height=260)

        st.markdown(
            '<div style="font-size:0.72rem; color:#333; font-family:\'DM Mono\',monospace; margin-top:0.3rem;">'
            'Each point = one day. No trendline shown intentionally — '
            'visual trendlines overstate pattern strength.'
            '</div>',
            unsafe_allow_html=True
        )

        # Rolling averages table
        st.markdown('<div class="chart-label" style="margin-top:1.2rem;">14-day rolling averages</div>', unsafe_allow_html=True)

        avg_data = {
            "Signal":  ["Sleep",          "Mood",          "Energy",          "Stress",          "Completion"],
            "14d Avg": [
                f"{df['sleep_hours'].mean():.1f}h",
                f"{df['mood_score'].mean():.1f}/10",
                f"{df['energy_score'].mean():.1f}/10",
                f"{df['stress_score'].mean():.1f}/10",
                f"{df['completion'].mean():.1f}%",
            ]
        }
        st.dataframe(
            pd.DataFrame(avg_data),
            hide_index=True,
            use_container_width=True
        )

# ── Full data table (collapsed by default) ────────────────────────────────────
st.markdown("---")
with st.expander("View raw data table", expanded=False):
    if raw_rows:
        display_df = pd.DataFrame([dict(r) for r in raw_rows])
        display_df.columns = ['Date', 'Sleep (h)', 'Mood', 'Energy', 'Stress', 'Completion %']
        st.dataframe(display_df, hide_index=True, use_container_width=True)
    else:
        st.caption("No joined data available yet.")

# ── Interpretation guide ───────────────────────────────────────────────────────
st.markdown("---")
with st.expander("How to interpret these numbers", expanded=False):
    st.markdown("""
    **r (Spearman correlation coefficient)**
    Ranges from -1 to +1. A positive r means the two variables tend to move 
    together. A negative r means when one is high the other tends to be low. 
    Values below 0.3 in absolute terms are considered weak regardless of 
    p-value significance.

    **p-value**
    The probability of observing this correlation by chance if there were 
    actually no relationship. This system surfaces insights at p < 0.10 — 
    a relaxed threshold appropriate for small personal datasets. A p-value 
    does not measure the size or importance of an effect.

    **Why no causal language**
    These correlations are computed on observational self-report data with no 
    control conditions. A correlation between sleep and completion may exist 
    because both are caused by a third variable — for example, low-stress days 
    may produce both better sleep and higher completion, making sleep appear 
    causally responsible when it is not.

    **What to do with this information**
    Nothing prescriptive. These patterns describe your historical data. If a 
    pattern is consistent over time and aligns with your lived experience, 
    it may be worth discussing with an academic counsellor or coach who can 
    help you interpret it in context.
    """)

# ── Disclaimer ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="disclaimer">
    Correlations are computed on your personal data only and are not 
    generalisable.<br>
    This system does not make recommendations. Consult a professional 
    for behavioural guidance.
</div>
""", unsafe_allow_html=True)
