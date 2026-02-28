from database.db_manager import get_connection

COLD_START_THRESHOLD    = 7
BOOTSTRAPPING_THRESHOLD = 14

def get_phase():
    """
    Returns the current system phase based on how many daily_logs exist.
    'cold_start'    — fewer than 7 logs
    'bootstrapping' — 7 to 13 logs
    'adaptive'      — 14 or more logs
    """
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM daily_logs WHERE user_id = 'default'"
        ).fetchone()
    count = row['cnt']

    if count < COLD_START_THRESHOLD:
        return 'cold_start'
    elif count < BOOTSTRAPPING_THRESHOLD:
        return 'bootstrapping'
    else:
        return 'adaptive'

def get_log_count():
    """Returns raw log count. Useful for showing progress to user."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM daily_logs WHERE user_id = 'default'"
        ).fetchone()
    return row['cnt']
