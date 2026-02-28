from engines.phase_manager import get_phase

COLD_START_BUFFER = 0.80
BREAK_BUFFER_MINUTES = 20

def _calculate_priority(difficulty, days_until_exam):
    """Higher difficulty + fewer days = higher priority."""
    return difficulty * (1 / max(days_until_exam, 1))

def _allocate_hours(available_hours, subjects, phase):
    """
    Distributes hours across subjects weighted by priority.
    Applies 80% buffer during cold_start.
    """
    if phase == 'cold_start':
        usable_hours = available_hours * COLD_START_BUFFER
    else:
        usable_hours = available_hours  # Reality Check cap applied separately

    usable_minutes = usable_hours * 60

    priorities = [
        _calculate_priority(s['difficulty'], s['days_until_exam'])
        for s in subjects
    ]
    total_priority = sum(priorities)

    tasks = []
    for i, subject in enumerate(subjects):
        weight        = priorities[i] / total_priority
        raw_minutes   = usable_minutes * weight
        study_minutes = max(int(raw_minutes) - BREAK_BUFFER_MINUTES, 15)

        tasks.append({
            "subject":      subject['name'],
            "minutes":      study_minutes,
            "break_buffer": BREAK_BUFFER_MINUTES,
            "priority":     round(priorities[i], 3)
        })
        # Redistribute minutes from tasks below floor to avoid unusable sessions
        MINIMUM_SESSION = 25
        short = [t for t in tasks if t['minutes'] < MINIMUM_SESSION]
        viable = [t for t in tasks if t['minutes'] >= MINIMUM_SESSION]
    if short and viable:
        # Drop short sessions and redistribute their minutes to viable ones
        recovered = sum(t['minutes'] + BREAK_BUFFER_MINUTES for t in short)
        total_priority_viable = sum(t['priority'] for t in viable)
        for t in viable:
            t['minutes'] += int(recovered * (t['priority'] / total_priority_viable))
        tasks = viable

    return tasks

def generate_daily_plan(available_hours, subjects):
    """
    Main entry point. Returns a plan dict.
    Pipeline A — reads only user inputs, never touches plan outcomes.
    """
    if not subjects:
        raise ValueError("subjects list cannot be empty")
    if available_hours <= 0:
        raise ValueError("available_hours must be positive")

    phase = get_phase()
    tasks = _allocate_hours(available_hours, subjects, phase)

    total_minutes = sum(t['minutes'] for t in tasks)

    return {
        "phase":                 phase,
        "tasks":                 tasks,
        "total_allocated_hours": round(total_minutes / 60, 2),
        "was_capped":            False  # Reality Check sets this to True when active
    }
