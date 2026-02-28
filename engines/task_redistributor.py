import json
from datetime import date, timedelta
from database.db_manager import get_connection
from engines.plan_generator import generate_daily_plan

def redistribute_deferred_tasks(deferred_plan_id):
    """
    Called when Emergency Mode is triggered.
    Marks today's tasks as deferred and redistributes them to future days.
    Returns a list of warnings for tasks that could not be scheduled.
    """
    warnings = []

    with get_connection() as conn:
        plan = conn.execute(
            "SELECT * FROM plans WHERE plan_id = ?", (deferred_plan_id,)
        ).fetchone()

        if not plan:
            raise ValueError(f"No plan found with id {deferred_plan_id}")

        subjects   = json.loads(plan['input_subjects'])
        exam_dates = {s['name']: s['days_until_exam'] for s in subjects}

        # Find future days that don't have a plan yet
        future_slots = []
        for i in range(1, 30):
            future_date = (date.today() + timedelta(days=i)).isoformat()
            existing = conn.execute(
                "SELECT plan_id FROM plans WHERE plan_date = ?", (future_date,)
            ).fetchone()
            if not existing:
                future_slots.append(future_date)

        # Redistribute each subject to the next available slot
        for subject in subjects:
            days_left = exam_dates.get(subject['name'], 999)
            deadline  = (date.today() + timedelta(days=days_left)).isoformat()

            placed = False
            for slot in future_slots:
                if slot <= deadline:
                    # Insert a lightweight placeholder plan for this subject
                    conn.execute("""
                        INSERT OR IGNORE INTO plans
                        (plan_date, input_available_hours, input_subjects,
                         input_difficulty_avg, output_allocated_hours,
                         phase_at_creation, output_capped)
                        VALUES (?, 1.5, ?, ?, 1.0, 'redistributed', 0)
                    """, (
                        slot,
                        json.dumps([subject]),
                        subject['difficulty']
                    ))
                    future_slots.remove(slot)
                    placed = True
                    break

            if not placed:
                warnings.append(
                    f"'{subject['name']}' could not be rescheduled before its exam on {deadline}. Please adjust manually."
                )

        # Log the intervention
        conn.execute("""
            INSERT INTO interventions (plan_id, trigger_type, trigger_value, action_taken)
            VALUES (?, 'emergency_mode', 0, 'Day cancelled. Tasks redistributed to future slots.')
        """, (deferred_plan_id,))

    return warnings
