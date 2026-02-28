from database.db_manager import get_connection
from engines.phase_manager import get_phase

WEIGHTS = {
    'stress_score':  0.30,
    'mood_score':    0.25,   # inverted
    'energy_score':  0.20,   # inverted
    'sleep_hours':   0.15,   # inverted
    'completion':    0.10,   # inverted
}

INVERTED_SIGNALS = {'mood_score', 'energy_score', 'sleep_hours', 'completion'}

def _zscore(value, mean, std):
    if std == 0:
        return 0.0
    return (value - mean) / std

def get_burnout_score():
    """
    Returns a dict with the composite burnout score and intervention level.
    Returns None if phase is cold_start (insufficient data).
    """
    if get_phase() == 'cold_start':
        return None

    with get_connection() as conn:
        rows = conn.execute("""
            SELECT mood_score, energy_score, stress_score, sleep_hours
            FROM daily_logs
            WHERE user_id = 'default'
            ORDER BY log_date DESC
            LIMIT 14
        """).fetchall()

        completion_row = conn.execute("""
            SELECT AVG(output_completion_pct) as avg_comp
            FROM plans
            WHERE user_id = 'default'
            AND output_completion_pct IS NOT NULL
            ORDER BY plan_date DESC
            LIMIT 14
        """).fetchone()

    if len(rows) < 7:
        return None

    signals = {
        'mood_score':   [r['mood_score']   for r in rows],
        'energy_score': [r['energy_score'] for r in rows],
        'stress_score': [r['stress_score'] for r in rows],
        'sleep_hours':  [r['sleep_hours']  for r in rows],
    }

    avg_completion = completion_row['avg_comp'] or 50.0
    signals['completion'] = [avg_completion]

    def mean(lst): return sum(lst) / len(lst)
    def std(lst):
        m = mean(lst)
        return (sum((x - m) ** 2 for x in lst) / len(lst)) ** 0.5

    # Use most recent value for each signal
    today = {k: v[0] for k, v in signals.items()}

    composite = 0.0
    for signal, weight in WEIGHTS.items():
        m   = mean(signals[signal])
        s   = std(signals[signal])
        z   = _zscore(today[signal], m, s)
        # Invert signals where lower value = higher burnout risk
        if signal in INVERTED_SIGNALS:
            z = -z
        composite += weight * z

    level = _get_level(composite)

    return {
        "score":      round(composite, 3),
        "level":      level,
        "days_used":  len(rows)
    }

def _get_level(score):
    if score < 1.0:  return "low"
    if score < 1.5:  return "yellow"
    if score < 2.0:  return "orange"
    return "red"
