"""Morning planning flow - runs daily to schedule the day."""

import sys
from datetime import date
from pathlib import Path

import yaml

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.calendar_client import CalendarClient
from core.scheduler import Scheduler
from modules import fitness, food, entrepreneurship, travel


class FitnessModule:
    def generate_requests(self, target_date, profile):
        return fitness.generate_requests(target_date, profile)


class FoodModule:
    def generate_requests(self, target_date, profile):
        return food.generate_requests(target_date, profile)


class EntrepreneurshipModule:
    def generate_requests(self, target_date, profile):
        return entrepreneurship.generate_requests(target_date, profile)


class TravelModule:
    def generate_requests(self, target_date, profile):
        return travel.generate_requests(target_date, profile)


def load_profile() -> dict:
    with open("config/profile.yaml") as f:
        return yaml.safe_load(f)


def plan_day(target_date: date | None = None, commit: bool = False) -> str:
    """
    Plan a day's schedule.

    Args:
        target_date: Date to plan (defaults to today)
        commit: If True, write events to Google Calendar

    Returns:
        Human-readable schedule preview
    """
    if target_date is None:
        target_date = date.today()

    profile = load_profile()
    google_cfg = profile["google"]

    cal_client = CalendarClient(
        credentials_path=google_cfg["credentials_path"],
        token_path=google_cfg["token_path"],
        calendar_id=google_cfg["calendar_id"],
    )

    scheduler = Scheduler("config/profile.yaml", cal_client)
    scheduler.register_module(FitnessModule())
    scheduler.register_module(FoodModule())
    scheduler.register_module(EntrepreneurshipModule())
    scheduler.register_module(TravelModule())

    blocks = scheduler.solve(target_date)
    preview = scheduler.preview(blocks)

    if commit:
        scheduler.commit(blocks)
        preview += "\n\n[Committed to Google Calendar]"

        # Pre-populate workout tracker if there's a gym block today
        try:
            from modules.workout_tracker import prepopulate_workout
            from modules.fitness import get_todays_workout, load_fitness_config

            fitness_config = load_fitness_config()
            workout = get_todays_workout(target_date, fitness_config)
            if workout:
                # Get structured exercises from config
                # Use short name (e.g. "Legs" not "Legs (Quads/Hams/Glutes)")
                short_name = workout.name.split("(")[0].strip()
                cycle = fitness_config["program"]["cycle"]
                for w in cycle:
                    if w["name"] == workout.name:
                        result = prepopulate_workout(
                            short_name, w["exercises"], target_date
                        )
                        preview += f"\n[Tracker: {result}]"
                        break
        except Exception as e:
            preview += f"\n[Tracker error: {e}]"

    return preview


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Plan your day")
    parser.add_argument("--date", type=str, help="Date to plan (YYYY-MM-DD), defaults to today")
    parser.add_argument("--commit", action="store_true", help="Write to Google Calendar")
    parser.add_argument("--preview", action="store_true", default=True, help="Show preview")
    args = parser.parse_args()

    target = date.fromisoformat(args.date) if args.date else None
    result = plan_day(target, commit=args.commit)
    print(result)


if __name__ == "__main__":
    main()
