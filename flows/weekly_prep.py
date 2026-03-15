"""Weekly prep flow - meal planning and grocery list generation."""

import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.food import generate_meal_plan, generate_grocery_list, load_food_config, get_week_start


def weekly_prep(week_start: date | None = None) -> str:
    """Generate meal plan and grocery list for the upcoming week."""
    if week_start is None:
        # Next Monday
        today = date.today()
        week_start = get_week_start(today)
        if week_start <= today:
            week_start += timedelta(weeks=1)

    config = load_food_config()

    # Generate meal plan
    plan = generate_meal_plan(week_start, config)

    # Generate grocery list
    grocery = generate_grocery_list(plan, config)

    # Format output
    lines = [f"Meal Plan for week of {week_start}", "=" * 40]
    for day, meals in plan.days.items():
        lines.append(f"\n{day.upper()}:")
        for meal_type, meal_name in meals.items():
            lines.append(f"  {meal_type}: {meal_name.replace('_', ' ').title()}")

    lines.append(f"\n{'=' * 40}")
    lines.append("Grocery List:")
    for item, amounts in grocery.items():
        lines.append(f"  {item.replace('_', ' ').title()}: {', '.join(amounts)}")

    return "\n".join(lines)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Weekly meal prep")
    parser.add_argument("--week", type=str, help="Week start date (YYYY-MM-DD)")
    args = parser.parse_args()

    target = date.fromisoformat(args.week) if args.week else None
    result = weekly_prep(target)
    print(result)


if __name__ == "__main__":
    main()
