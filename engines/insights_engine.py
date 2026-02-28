from scipy import stats
from database.db_manager import get_connection
from engines.phase_manager import get_phase

MIN_SAMPLE = 14
P_THRESHOLD = 0.10

SIGNAL_LABELS = {
    'sleep_hours':   'sleep duration',
    'mood_score':    'mood',
    'energy_score':  'energy level',
    'stress_score':  'stress level',
}

def get_insights():
    """
    Returns a list of observational insight strings.
    Returns empty list if phase is not adaptive or sample is too small.
    """
    if get_phase() != 'adaptive':
        return []

    with get_connection() as conn:
        rows = conn.execute("""
            SELECT l.sleep_hours, l.mood_score, l.energy_score, l.stress_score,
                   p.output_completion_pct
            FROM daily_logs l
            JOIN plans p ON l.log_date = p.plan_date
            WHERE l.user_id = 'default'
            AND p.output_completion_pct IS NOT NULL
            ORDER BY l.log_date DESC
            LIMIT 60
        """).fetchall()

    if len(rows) < MIN_SAMPLE:
        return []

    completion = [r['output_completion_pct'] for r in rows]
    insights   = []

    for signal, label in SIGNAL_LABELS.items():
        values = [r[signal] for r in rows]
        rho, p = stats.spearmanr(values, completion)
        n      = len(rows)

        if p >= P_THRESHOLD:
            continue  # Not significant enough to surface

        direction = "higher" if rho > 0 else "lower"
        strength  = abs(rho)

        insight = (
            f"On days when your {label} is higher, your task completion tends to be {direction} "
            f"(r={rho:.2f}, p={p:.2f}, N={n}). "
            f"This is an observed pattern in your data. It may reflect a third factor, "
            f"such as workload pressure affecting both variables simultaneously."
        )
        insights.append({"text": insight, "rho": rho, "p": p, "signal": signal})

    return insights
