from database.db_manager import get_connection

# PIPELINE B — reads outcome columns only.
# This file must NEVER import from plan_generator.py.

def get_rolling_completion_rate(days=7):
    """
    Returns the average completion % over the last N days.
    Returns None if fewer than 3 outcomes exist (not enough data to act on).
    """
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT output_completion_pct
            FROM plans
            WHERE user_id = 'default'
            AND output_completion_pct IS NOT NULL
            ORDER BY plan_date DESC
            LIMIT ?
        """, (days,)).fetchall()

    if len(rows) < 3:
        return None

    return round(sum(r['output_completion_pct'] for r in rows) / len(rows), 2)

def get_weekly_performance_report():
    """Returns a summary dict for the dashboard."""
    rate = get_rolling_completion_rate()
    return {
        "rolling_completion_rate": rate,
        "data_sufficient":         rate is not None
    }
