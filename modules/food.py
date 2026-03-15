"""Food module - meal planning, grocery lists, and cooking time blocks."""

import json
import random
from datetime import date, time
from pathlib import Path

import yaml

from core.models import TimeBlockRequest, BlockCategory, WeeklyMealPlan

COLOR_FOOD = "2"  # sage green

DAY_NAMES = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def load_food_config(path: str = "config/food.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def _get_inventory_proteins() -> set[str]:
    """Get protein items currently in inventory."""
    try:
        from modules.inventory import load_inventory
        inv = load_inventory()
        proteins = set()
        for loc in ["fridge", "freezer"]:
            for item in inv.get(loc, []):
                proteins.add(item["item"])
        return proteins
    except Exception:
        return set()


# Map inventory items to recipe ingredients
INVENTORY_TO_RECIPE = {
    "ground_beef": ["burgers", "ground_beef_pasta"],
    "chicken_breast": ["chicken_rice_broccoli", "chicken_tikka_masala", "butter_chicken"],
    "chicken_thigh": ["stir_fry", "sheet_pan_chicken_veggies", "chicken_tikka_masala",
                       "butter_chicken", "chicken_burrito_bowl", "sheet_pan_fajitas",
                       "healthy_chicken_bowl", "budget_burrito_bowl", "pressure_cooker_chicken_rice"],
    "smoked_salmon": [],  # eat as-is, on bagels, etc.
    "salmon": ["salmon_sweet_potato"],
    "turkey_deli": ["turkey_wrap"],
    "avocados": ["eggs_toast", "chicken_burrito_bowl", "healthy_chicken_bowl"],
    "strawberries": ["overnight_oats", "protein_smoothie"],
    "bananas": ["protein_smoothie", "overnight_oats"],
    "buns": ["burgers"],
    "greek_yogurt": ["overnight_oats", "chicken_tikka_masala", "cucumber_raita",
                      "butter_chicken", "budget_burrito_bowl"],
    "russet_potatoes": ["sheet_pan_chicken_veggies"],
    "rice": ["stir_fry", "chicken_tikka_masala", "chicken_burrito_bowl",
             "pressure_cooker_chicken_rice", "weeknight_fried_rice", "beef_broccoli",
             "healthy_chicken_bowl", "budget_burrito_bowl"],
}


def generate_meal_plan(week_start: date, config: dict | None = None) -> WeeklyMealPlan:
    """Generate a weekly meal plan prioritizing what's in the fridge."""
    if config is None:
        config = load_food_config()

    meals = config["meals"]
    inventory = _get_inventory_proteins()

    dislikes = set(config.get("preferences", {}).get("dislikes", []))
    breakfasts = [k for k, v in meals.items() if v["type"] == "breakfast" and k not in dislikes]
    lunches = [k for k, v in meals.items() if v["type"] == "lunch" and k not in dislikes]
    dinners = [k for k, v in meals.items() if v["type"] == "dinner" and k not in dislikes]

    # Prioritize recipes that use what we have
    def _score_recipe(recipe_name: str) -> int:
        """Higher score = uses more inventory items."""
        recipe_ingredients = set(meals.get(recipe_name, {}).get("ingredients", {}).keys())
        # Check which inventory items map to this recipe
        score = 0
        for inv_item, recipes in INVENTORY_TO_RECIPE.items():
            if inv_item in inventory and recipe_name in recipes:
                score += 2
        # Also check direct ingredient matches
        for inv_item in inventory:
            if inv_item in recipe_ingredients:
                score += 1
        return score

    # Sort by inventory score, use highest-scoring recipes first
    scored_dinners = sorted(dinners, key=_score_recipe, reverse=True)
    scored_lunches = sorted(lunches, key=_score_recipe, reverse=True)
    scored_breakfasts = sorted(breakfasts, key=_score_recipe, reverse=True)

    plan_days = {}
    used_dinners = []
    for i, day in enumerate(DAY_NAMES):
        # Rotate through scored recipes, preferring inventory-matched ones
        breakfast = scored_breakfasts[i % len(scored_breakfasts)]
        lunch = scored_lunches[i % len(scored_lunches)]
        # For dinners, try to use each recipe ~2x (batch cooking)
        dinner_idx = i // 2  # same dinner for 2 consecutive days
        dinner = scored_dinners[dinner_idx % len(scored_dinners)]

        plan_days[day] = {
            "breakfast": breakfast,
            "lunch": lunch,
            "dinner": dinner,
        }

    plan = WeeklyMealPlan(week_start=week_start, days=plan_days)

    # Save to disk
    out_dir = Path("data/meal_plans")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{week_start.isoformat()}.json"
    out_path.write_text(plan.model_dump_json(indent=2))

    return plan


def load_meal_plan(week_start: date) -> WeeklyMealPlan | None:
    """Load an existing meal plan from disk."""
    path = Path(f"data/meal_plans/{week_start.isoformat()}.json")
    if path.exists():
        return WeeklyMealPlan.model_validate_json(path.read_text())
    return None


def get_week_start(target_date: date) -> date:
    """Get the Monday of the week containing target_date."""
    return target_date - __import__("datetime").timedelta(days=target_date.weekday())


def generate_grocery_list(plan: WeeklyMealPlan, config: dict | None = None) -> dict[str, list[str]]:
    """Generate a grocery list from a meal plan, excluding pantry staples and inventory."""
    if config is None:
        config = load_food_config()

    meals = config["meals"]
    staples = set(config.get("pantry_staples", []))
    shopping: dict[str, list[str]] = {}

    # Get what we already have
    try:
        from modules.inventory import load_inventory
        inv = load_inventory()
        on_hand = set()
        for loc in ["fridge", "freezer", "pantry"]:
            for item in inv.get(loc, []):
                on_hand.add(item["item"])
    except Exception:
        on_hand = set()

    for day, day_meals in plan.days.items():
        for meal_type, meal_name in day_meals.items():
            if meal_name not in meals:
                continue
            for ingredient, amount in meals[meal_name].get("ingredients", {}).items():
                if ingredient not in staples and ingredient not in on_hand:
                    shopping.setdefault(ingredient, []).append(f"{amount} ({day} {meal_type})")

    # Save to disk
    out_dir = Path("data/grocery_lists")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{plan.week_start.isoformat()}.json"
    out_path.write_text(json.dumps(shopping, indent=2))

    return shopping


def _meal_description(meal_name: str, config: dict) -> str:
    """Build a description with ingredients for a meal."""
    meal_info = config["meals"].get(meal_name, {})
    if not meal_info:
        return ""
    ingredients = meal_info.get("ingredients", {})
    if not ingredients:
        return ""
    lines = [f"Ingredients for {meal_name.replace('_', ' ').title()}:"]
    for item, amount in ingredients.items():
        lines.append(f"  - {item.replace('_', ' ').title()}: {amount}")
    prep = meal_info.get("prep_minutes", 0)
    cook = meal_info.get("cook_minutes", 0)
    if prep or cook:
        lines.append(f"\nPrep: {prep}min | Cook: {cook}min")
    servings = meal_info.get("servings", 1)
    if servings > 1:
        lines.append(f"Makes {servings} servings")
    return "\n".join(lines)


def load_travel_blackouts(path: str = "config/travel.yaml") -> set[str]:
    try:
        with open(path) as f:
            data = yaml.safe_load(f)
        return set(data.get("blackout_dates", []))
    except FileNotFoundError:
        return set()


def generate_requests(target_date: date, profile: dict) -> list[TimeBlockRequest]:
    """Generate cooking/meal prep time blocks for today."""
    # No cooking on travel days
    blackouts = load_travel_blackouts()
    if target_date.isoformat() in blackouts:
        return []

    config = load_food_config()
    requests = []

    day_name = target_date.strftime("%a").lower()
    is_weekday = day_name in profile["work"]["days"]

    meal_times = profile["meals"]["preferred_times"]
    prep_times = profile["meals"]["prep_time_minutes"]

    # Try to load this week's meal plan
    week_start = get_week_start(target_date)
    plan = load_meal_plan(week_start)

    # Determine today's meals
    today_meals = {}
    if plan and day_name in plan.days:
        today_meals = plan.days[day_name]

    # Breakfast prep
    breakfast_name = today_meals.get("breakfast", "Breakfast")
    requests.append(
        TimeBlockRequest(
            category=BlockCategory.FOOD_PREP,
            title=f"Breakfast: {breakfast_name.replace('_', ' ').title()}",
            duration_minutes=prep_times["breakfast"],
            earliest=time(6, 30),
            latest=time(8, 0),
            priority=4,
            description=_meal_description(breakfast_name, config),
            color_id=COLOR_FOOD,
        )
    )

    # Lunch prep (skip if batch-cooked meal)
    lunch_name = today_meals.get("lunch", "Lunch")
    meal_info = config["meals"].get(lunch_name, {})
    is_batch = "batch_friendly" in meal_info.get("tags", [])

    if not is_batch:
        requests.append(
            TimeBlockRequest(
                category=BlockCategory.FOOD_PREP,
                title=f"Lunch: {lunch_name.replace('_', ' ').title()}",
                duration_minutes=prep_times["lunch"],
                earliest=time(11, 30),
                latest=time(13, 0),
                priority=5,
                description=_meal_description(lunch_name, config),
                color_id=COLOR_FOOD,
            )
        )

    # Dinner prep — FIXED anchor, highest priority after work
    # Dinner is not flexible. It happens at 6:30 PM. Gym works around it.
    dinner_name = today_meals.get("dinner", "Dinner")
    if dinner_name != "eating_out":
        requests.append(
            TimeBlockRequest(
                category=BlockCategory.FOOD_PREP,
                title=f"Dinner: {dinner_name.replace('_', ' ').title()}",
                duration_minutes=prep_times["dinner"],
                earliest=time(18, 0),
                latest=time(19, 0),
                priority=1,  # highest priority — gym schedules around dinner
                flexible=False,
                description=_meal_description(dinner_name, config),
                color_id=COLOR_FOOD,
            )
        )


    return requests
