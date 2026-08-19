from datetime import datetime, timedelta, timezone


def schedule(quality: int, interval: int, ease_factor: float, repetitions: int):
    """Standard SM-2 spaced-repetition update. quality is 0-5 (self-assessed recall)."""
    if quality < 3:
        repetitions = 0
        interval = 1
    else:
        if repetitions == 0:
            interval = 1
        elif repetitions == 1:
            interval = 6
        else:
            interval = round(interval * ease_factor)
        repetitions += 1

    ease_factor = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    ease_factor = max(ease_factor, 1.3)

    next_review_at = datetime.now(timezone.utc) + timedelta(days=interval)

    return {
        "interval": interval,
        "ease_factor": round(ease_factor, 4),
        "repetitions": repetitions,
        "next_review_at": next_review_at,
    }
