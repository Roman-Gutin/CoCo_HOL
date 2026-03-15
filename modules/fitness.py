"""Fitness module - generates workout schedule and calendar blocks."""

from datetime import date, time

import yaml

from core.models import TimeBlockRequest, BlockCategory, Workout

# Google Calendar color IDs
COLOR_FITNESS = "9"   # blueberry
COLOR_COMMUTE = "8"   # graphite


def load_travel_blackouts(path: str = "config/travel.yaml") -> set[str]:
    try:
        with open(path) as f:
            data = yaml.safe_load(f)
        return set(data.get("blackout_dates", []))
    except FileNotFoundError:
        return set()


def load_fitness_config(path: str = "config/fitness.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def get_todays_workout(target_date: date, config: dict) -> Workout | None:
    """Determine which workout is scheduled for today based on the cycle."""
    fitness = config if "program" in config else load_fitness_config()
    day_name = target_date.strftime("%a").lower()

    training_days = fitness["program"]["training_days"]
    if day_name not in training_days:
        return None

    cycle = fitness["program"]["cycle"]
    # Simple rotation: count training days since a reference date
    # Aligned so Sat 3/7 = Pull, Sun 3/8 = Legs, Mon 3/9 = Upper, etc.
    ref = date(2026, 3, 6)  # calibrated to Roman's current cycle
    days_since = (target_date - ref).days
    training_day_count = sum(
        1 for d in range(days_since)
        if (ref + __import__("datetime").timedelta(days=d)).strftime("%a").lower() in training_days
    )
    workout_data = cycle[training_day_count % len(cycle)]
    # Format exercises as strings for display, keep raw data accessible
    exercise_strs = []
    for ex in workout_data["exercises"]:
        if isinstance(ex, dict):
            exercise_strs.append(f"{ex['name']} {ex['sets']}x{ex['reps']}")
        else:
            exercise_strs.append(str(ex))
    return Workout(name=workout_data["name"], exercises=exercise_strs, day=day_name)


def is_cardio_day(target_date: date, config: dict) -> bool:
    fitness = config if "cardio" in config else load_fitness_config()
    day_name = target_date.strftime("%a").lower()
    return day_name in fitness["cardio"]["preferred_days"]


def generate_requests(target_date: date, profile: dict) -> list[TimeBlockRequest]:
    """Generate time block requests for fitness activities."""
    fitness_config = load_fitness_config()
    requests = []

    # Skip if traveling
    blackouts = load_travel_blackouts()
    if target_date.isoformat() in blackouts:
        return requests

    gym_commute = profile["gym"]["commute_minutes"]
    gym_duration = profile["gym"]["session_duration_minutes"]
    day_name = target_date.strftime("%a").lower()
    is_weekday = day_name in profile["work"]["days"]

    workout = get_todays_workout(target_date, fitness_config)

    if workout:
        group_id = f"gym_{target_date.isoformat()}"

        if is_weekday:
            # Before work: need to finish gym + commute + buffer before 8:30
            # Or after work: start after 5:00 PM
            preferred = profile["gym"]["preferred_times"]

            # Try morning first (6:00 AM default)
            gym_start = time.fromisoformat(preferred[0])
            # Commute starts 20 min before gym
            commute_start_hour = gym_start.hour
            commute_start_min = gym_start.minute - gym_commute
            if commute_start_min < 0:
                commute_start_hour -= 1
                commute_start_min += 60
            commute_start = time(commute_start_hour, commute_start_min)
            latest = time(17, 30)  # can also go after work
        else:
            # Weekend: flexible, prefer 9 AM
            commute_start = time(8, 40)
            gym_start = time(9, 0)
            latest = time(16, 0)

        exercises_str = "\n".join(f"  - {e}" for e in workout.exercises)

        # Link to workout tracker spreadsheet
        try:
            from modules.workout_tracker import get_spreadsheet_url
            tracker_url = get_spreadsheet_url()
            tracker_link = f"\n\nLog your sets: {tracker_url}" if tracker_url else ""
        except Exception:
            tracker_link = ""

        requests.extend([
            TimeBlockRequest(
                category=BlockCategory.COMMUTE,
                title="Drive to gym",
                duration_minutes=gym_commute,
                earliest=commute_start,
                latest=latest,
                priority=2,
                group_id=group_id,
                group_order=0,
                color_id=COLOR_COMMUTE,
            ),
            TimeBlockRequest(
                category=BlockCategory.FITNESS,
                title=f"Gym: {workout.name}",
                duration_minutes=gym_duration,
                earliest=gym_start,
                latest=latest,
                priority=2,
                group_id=group_id,
                group_order=1,
                description=f"Workout:\n{exercises_str}{tracker_link}",
                color_id=COLOR_FITNESS,
            ),
            TimeBlockRequest(
                category=BlockCategory.COMMUTE,
                title="Drive home from gym",
                duration_minutes=gym_commute,
                earliest=gym_start,
                latest=time(21, 0),
                priority=2,
                group_id=group_id,
                group_order=2,
                color_id=COLOR_COMMUTE,
            ),
        ])

    if is_cardio_day(target_date, fitness_config) and not workout:
        # Cardio on rest days (can be done at home or gym)
        cardio_duration = fitness_config["cardio"]["duration_minutes"]
        requests.append(
            TimeBlockRequest(
                category=BlockCategory.CARDIO,
                title="Cardio (incline walk / run)",
                duration_minutes=cardio_duration,
                earliest=time(6, 0) if is_weekday else time(8, 0),
                latest=time(20, 0),
                priority=3,
                description="30 min incline walk or easy run",
                color_id=COLOR_FITNESS,
            )
        )

    return requests
