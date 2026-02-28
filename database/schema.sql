CREATE TABLE IF NOT EXISTS daily_logs (
    log_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     TEXT    NOT NULL DEFAULT 'default',
    log_date    TEXT    NOT NULL UNIQUE,
    mood_score  INTEGER NOT NULL CHECK(mood_score BETWEEN 1 AND 10),
    energy_score INTEGER NOT NULL CHECK(energy_score BETWEEN 1 AND 10),
    stress_score INTEGER NOT NULL CHECK(stress_score BETWEEN 1 AND 10),
    sleep_hours REAL    NOT NULL CHECK(sleep_hours BETWEEN 0 AND 24),
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS plans (
    plan_id                INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id                TEXT    NOT NULL DEFAULT 'default',
    plan_date              TEXT    NOT NULL UNIQUE,
    input_available_hours  REAL    NOT NULL,
    input_subjects         TEXT    NOT NULL,
    input_difficulty_avg   REAL    NOT NULL,
    output_allocated_hours REAL    NOT NULL,
    output_capped          INTEGER NOT NULL DEFAULT 0,
    output_completion_pct  REAL    CHECK(output_completion_pct BETWEEN 0 AND 100),
    phase_at_creation      TEXT    NOT NULL,
    created_at             TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS interventions (
    intervention_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id            INTEGER NOT NULL REFERENCES plans(plan_id),
    trigger_type       TEXT    NOT NULL,
    trigger_value      REAL    NOT NULL,
    action_taken       TEXT    NOT NULL,
    recovery_detected  INTEGER NOT NULL DEFAULT 0,
    created_at         TEXT    NOT NULL DEFAULT (datetime('now'))
);
