from engines.evaluator import get_rolling_completion_rate

# This is the only permitted bridge between Pipeline B and Pipeline A.
# It exposes ONE controlled value: a hours cap derived from completion rate.
# plan_generator.py reads this cap but nothing else from the evaluation pipeline.

def get_reality_check_cap(requested_hours):
    """
    Returns a capped hours value if completion rate justifies it.
    Returns requested_hours unchanged if data is insufficient or rate is healthy.
    """
    rate = get_rolling_completion_rate()

    if rate is None:
        return requested_hours, False  # (hours, was_capped)

    if rate >= 80:
        return requested_hours, False
    elif rate >= 60:
        cap = requested_hours * 0.85
    elif rate >= 40:
        cap = requested_hours * 0.70
    else:
        cap = requested_hours * 0.55

    return round(min(cap, requested_hours), 2), True
