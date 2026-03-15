"""
Full bidirectional sync for second_brain.

1. DETECT — CDC from calendar, workout sheet, nutrition sheet, configs
2. LEARN — Identify preference patterns, suggest/apply adjustments
3. SYNC — Push unified state to calendar + sheets
4. REPORT — Summary of changes

Usage:
    python flows/sync_calendar.py                  # Preview next 14 days
    python flows/sync_calendar.py --commit          # Full sync
    python flows/sync_calendar.py --days 7          # Only sync next 7 days
    python flows/sync_calendar.py --date 2026-03-10 # Sync a specific date
"""

import argparse
import json
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.calendar_client import CalendarClient

TZ = ZoneInfo("America/Los_Angeles")


def load_configs():
    """Load all config files."""
    with open("config/fitness.yaml") as f:
        fitness = yaml.safe_load(f)
    with open("config/food.yaml") as f:
        food = yaml.safe_load(f)
    with open("config/profile.yaml") as f:
        profile = yaml.safe_load(f)

    travel_blackouts = set()
    travel_path = Path("config/travel.yaml")
    if travel_path.exists():
        with open(travel_path) as f:
            travel = yaml.safe_load(f) or {}
        travel_blackouts = set(travel.get("blackout_dates", []))

    tracker = {}
    tracker_path = Path("data/workout_tracker.json")
    if tracker_path.exists():
        tracker = json.loads(tracker_path.read_text())

    return fitness, food, profile, travel_blackouts, tracker


def load_active_meal_plan():
    """Find and load the most recent meal plan."""
    meal_dir = Path("data/meal_plans")
    if not meal_dir.exists():
        return None
    plans = sorted(meal_dir.glob("*.json"), reverse=True)
    if not plans:
        return None
    return json.loads(plans[0].read_text())


def load_overrides():
    """Load schedule overrides (manual workout moves, extra blackouts)."""
    path = Path("data/schedule_overrides.json")
    if path.exists():
        return json.loads(path.read_text())
    return {"overrides": [], "blackout_dates": []}


# --- CDC (Change Data Capture) ---

SNAPSHOT_PATH = Path("data/calendar_snapshot.json")
CDC_LOG_PATH = Path("data/calendar_cdc.json")


def load_snapshot():
    """Load the last-synced event snapshot."""
    if SNAPSHOT_PATH.exists():
        return json.loads(SNAPSHOT_PATH.read_text())
    return {}


def save_snapshot(snapshot):
    """Save event snapshot after sync."""
    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_PATH.write_text(json.dumps(snapshot, indent=2))


def load_cdc_log():
    """Load the CDC change log."""
    if CDC_LOG_PATH.exists():
        return json.loads(CDC_LOG_PATH.read_text())
    return {"changes": []}


def save_cdc_log(log):
    CDC_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CDC_LOG_PATH.write_text(json.dumps(log, indent=2))


def detect_changes(cal, target_date, snapshot):
    """
    Compare current calendar state against snapshot for a date.
    Returns list of detected changes (moves, deletes, edits).
    """
    date_key = target_date.isoformat()
    expected = snapshot.get(date_key, [])
    if not expected:
        return []

    # Get current managed events
    current_events = cal.list_managed_events(target_date)
    current_by_id = {e["id"]: e for e in current_events}
    changes = []

    for snap_event in expected:
        event_id = snap_event["event_id"]
        current = current_by_id.get(event_id)

        if current is None:
            # Event was deleted by user
            changes.append({
                "type": "deleted",
                "date": date_key,
                "title": snap_event["title"],
                "original_start": snap_event["start"],
                "original_end": snap_event["end"],
                "detected_at": datetime.now(TZ).isoformat(),
            })
            continue

        cur_start = current.get("start", {}).get("dateTime", "")
        cur_end = current.get("end", {}).get("dateTime", "")
        cur_title = current.get("summary", "")

        # Check if time was moved
        if cur_start != snap_event["start"] or cur_end != snap_event["end"]:
            changes.append({
                "type": "time_moved",
                "date": date_key,
                "title": snap_event["title"],
                "original_start": snap_event["start"],
                "original_end": snap_event["end"],
                "new_start": cur_start,
                "new_end": cur_end,
                "detected_at": datetime.now(TZ).isoformat(),
            })

        # Check if title was edited
        if cur_title != snap_event["title"]:
            changes.append({
                "type": "title_edited",
                "date": date_key,
                "original_title": snap_event["title"],
                "new_title": cur_title,
                "detected_at": datetime.now(TZ).isoformat(),
            })

    return changes


def detect_workout_sheet_cdc():
    """Read workout sheet, detect what Roman actually did vs what was planned."""
    try:
        from modules.workout_tracker import _get_gspread_client, _load_tracker_config
        config = _load_tracker_config()
        gc = _get_gspread_client()
        sh = gc.open_by_key(config["spreadsheet_id"])
        log_ws = sh.worksheet("Log")
        rows = log_ws.get_all_values()
    except Exception:
        return {"insights": [], "raw": []}

    insights = []
    exercises_by_date = {}

    for row in rows[1:]:
        if not row[0] or row[2] == "SESSION NOTES":
            continue
        date_str, workout, exercise, set_num = row[0], row[1], row[2], row[3]
        reps = row[4]
        weight = row[5]
        rpe = row[6]
        notes = row[7]

        if date_str not in exercises_by_date:
            exercises_by_date[date_str] = {"workout": workout, "exercises": {}}
        if exercise not in exercises_by_date[date_str]["exercises"]:
            exercises_by_date[date_str]["exercises"][exercise] = []

        exercises_by_date[date_str]["exercises"][exercise].append({
            "set": set_num, "reps": reps, "weight": weight, "rpe": rpe, "notes": notes
        })

    for date_str, data in exercises_by_date.items():
        for ex_name, sets in data["exercises"].items():
            filled_sets = [s for s in sets if s["reps"] or s["weight"]]
            skipped_sets = [s for s in sets if "skip" in s.get("notes", "").lower()]

            # Skipped exercises
            if skipped_sets and not filled_sets:
                insights.append({
                    "type": "exercise_skipped",
                    "date": date_str,
                    "exercise": ex_name,
                    "workout": data["workout"],
                })

            # RPE too high
            for s in filled_sets:
                try:
                    rpe_val = float(s["rpe"]) if s["rpe"] else None
                except ValueError:
                    rpe_val = None
                if rpe_val and rpe_val >= 10:
                    insights.append({
                        "type": "rpe_too_high",
                        "date": date_str,
                        "exercise": ex_name,
                        "rpe": rpe_val,
                        "weight": s["weight"],
                    })

            # Pain reported
            for s in sets:
                notes_lower = s.get("notes", "").lower()
                if any(kw in notes_lower for kw in ["pain", "hurt", "sharp", "ache", "flare"]):
                    insights.append({
                        "type": "pain_reported",
                        "date": date_str,
                        "exercise": ex_name,
                        "note": s["notes"],
                    })

            # Added exercises (warm-up set markers not matching program)
            if any("needed to add" in s.get("notes", "").lower() for s in sets):
                insights.append({
                    "type": "exercise_added_by_user",
                    "date": date_str,
                    "exercise": ex_name,
                    "note": next(s["notes"] for s in sets if "needed to add" in s.get("notes", "").lower()),
                })

    return {"insights": insights, "raw": exercises_by_date}


def detect_nutrition_sheet_cdc():
    """Read nutrition sheet, detect deviations from plan."""
    try:
        from modules.workout_tracker import _get_gspread_client, _load_tracker_config
        config = _load_tracker_config()
        gc = _get_gspread_client()
        sh = gc.open_by_key(config["spreadsheet_id"])
        nut_ws = sh.worksheet("Nutrition")
        rows = nut_ws.get_all_values()
    except Exception:
        return {"insights": []}

    insights = []
    for row in rows[1:]:
        if len(row) < 14 or row[1] == "DAILY TOTAL":
            continue
        date_str, meal, planned, servings = row[0], row[1], row[2], row[3]
        actual = row[8] if len(row) > 8 else ""
        notes = row[13] if len(row) > 13 else ""

        if actual and actual != planned:
            insights.append({
                "type": "meal_deviation",
                "date": date_str,
                "meal": meal,
                "planned": planned,
                "actual": actual,
                "notes": notes,
            })

    return {"insights": insights}


def learn_preferences(cdc_log):
    """
    Analyze CDC log for recurring patterns.
    Returns list of suggested preference adjustments.
    """
    suggestions = []
    changes = cdc_log.get("changes", [])

    # Count time moves by event category
    time_moves = {}
    for ch in changes:
        if ch.get("type") != "time_moved":
            continue
        title = ch.get("title", "")
        old_h = ch["original_start"].split("T")[1][:5]
        new_h = ch["new_start"].split("T")[1][:5]

        # Group by event type
        if "Dinner" in title:
            key = "dinner_time"
        elif "Lunch" in title:
            key = "lunch_time"
        elif "Breakfast" in title:
            key = "breakfast_time"
        elif "Gym" in title:
            key = "gym_time"
        elif "Prehab" in title:
            key = "prehab_time"
        else:
            continue

        time_moves.setdefault(key, []).append({"from": old_h, "to": new_h})

    # If 3+ moves in the same direction, suggest a default change
    for key, moves in time_moves.items():
        if len(moves) >= 3:
            # Most common "to" time
            to_times = [m["to"] for m in moves]
            most_common = max(set(to_times), key=to_times.count)
            suggestions.append({
                "type": "time_preference",
                "category": key,
                "suggested_time": most_common,
                "evidence_count": len(moves),
                "note": f"Roman moved {key.replace('_', ' ')} to {most_common} in {len(moves)} out of {len(moves)} edits",
            })

    # Count deletions
    deletions = {}
    for ch in changes:
        if ch.get("type") != "deleted":
            continue
        title = ch.get("title", "")
        deletions.setdefault(title, 0)
        deletions[title] += 1

    for title, count in deletions.items():
        if count >= 3:
            suggestions.append({
                "type": "event_unwanted",
                "title": title,
                "delete_count": count,
                "note": f"Roman deleted \"{title}\" {count} times — consider removing from schedule",
            })

    return suggestions


def get_non_managed_events(cal, target_date):
    """Get events that are NOT managed by second_brain."""
    all_events = cal.list_events(target_date)
    return [
        e for e in all_events
        if e.get("extendedProperties", {}).get("private", {}).get("managed_by") != "second_brain"
    ]


def get_managed_events(cal, target_date):
    """Get events managed by second_brain."""
    return cal.list_managed_events(target_date)


def time_overlaps(s1, e1, s2, e2):
    """Check if two time ranges overlap."""
    return s1 < e2 and e1 > s2


def event_to_times(event):
    """Extract start/end datetimes from an event."""
    start_str = event.get("start", {}).get("dateTime")
    end_str = event.get("end", {}).get("dateTime")
    if start_str and end_str:
        return datetime.fromisoformat(start_str), datetime.fromisoformat(end_str)
    return None, None


def is_travel_day(target_date, travel_blackouts, non_managed):
    """Check if this is a travel day via blackouts or flight events."""
    if target_date.isoformat() in travel_blackouts:
        return True
    for e in non_managed:
        summary = e.get("summary", "").lower()
        if any(kw in summary for kw in ["flight", "airport"]):
            return True
    return False


def find_free_slot(target_date, start_time, duration_min, busy_slots):
    """Find a free slot on target_date starting from start_time."""
    candidate = datetime.combine(target_date, start_time, tzinfo=TZ)
    end_of_day = datetime.combine(target_date, time(22, 0), tzinfo=TZ)
    duration = timedelta(minutes=duration_min)
    step = timedelta(minutes=15)

    while candidate + duration <= end_of_day:
        candidate_end = candidate + duration
        conflict = False
        for bs, be in busy_slots:
            if time_overlaps(candidate, candidate_end, bs, be):
                conflict = True
                break
        if not conflict:
            return candidate
        candidate += step
    return None


def build_meal_description(recipe_name, food_config, sheet_url):
    """Build a meal event description with ingredients, macros, and sheet link."""
    meals_db = food_config["meals"]
    recipe = meals_db.get(recipe_name, {})

    parts = []

    ingredients = recipe.get("ingredients", {})
    if ingredients:
        parts.append("INGREDIENTS:")
        for item, amount in ingredients.items():
            parts.append(f"  - {item.replace('_', ' ').title()}: {amount}")

    macros = recipe.get("macros", {})
    if macros:
        parts.append(f"\nMACROS (per serving):")
        parts.append(
            f"  {macros.get('calories', '?')} cal | "
            f"{macros.get('protein_g', '?')}g P | "
            f"{macros.get('carbs_g', '?')}g C | "
            f"{macros.get('fat_g', '?')}g F"
        )

    notes = recipe.get("notes", "")
    if notes:
        parts.append(f"\n{notes}")

    if sheet_url:
        parts.append(f"\nLog deviations: {sheet_url}")

    return "\n".join(parts)


def build_gym_description(workout_day, fitness_config, sheet_url):
    """Build gym event description with warm-up, exercises, progression."""
    parts = []

    warm_up = workout_day.get("warm_up", [])
    if warm_up:
        parts.append("WARM-UP:")
        for w in warm_up:
            parts.append(f"  - {w['name']}")
        parts.append("")

    parts.append("EXERCISES:")
    for ex in workout_day["exercises"]:
        line = f"  - {ex['name']}: {ex['sets']}x{ex['reps']}"
        rest = ex.get("rest_seconds")
        if rest:
            line += f" (rest {rest}s)"
        parts.append(line)
        prog = ex.get("progression", "")
        if prog:
            parts.append(f"    Progression: {prog}")
        note = ex.get("notes", "")
        if note:
            parts.append(f"    Note: {note}")

    period = fitness_config["program"].get("periodization", {})
    if period:
        parts.append(f"\nPERIODIZATION: {period.get('model', 'linear')} — {period.get('cycle_weeks', 4)}-week cycle")

    if sheet_url:
        parts.append(f"\nTrack workout: {sheet_url}")

    return "\n".join(parts)


def build_prehab_description(fitness_config):
    """Build prehab event description."""
    prehab = fitness_config.get("prehab", {})
    routine = prehab.get("routine", [])

    parts = [f"PREHAB ROUTINE ({prehab.get('duration_minutes', 15)} min):"]
    for ex in routine:
        line = f"  - {ex['name']}: {ex.get('sets', '')}x{ex.get('reps', '')}"
        note = ex.get("note", "")
        if note:
            line += f" ({note})"
        parts.append(line)

    return "\n".join(parts)


def build_cardio_description(fitness_config, day_of_week):
    """Build cardio event description with full session protocol."""
    cardio = fitness_config.get("cardio", {})
    swimming = cardio.get("swimming", {})

    # Determine which week phase (default week_1_2)
    phase = swimming.get("week_1_2", {})

    # Tue = technique, Thu = endurance
    if day_of_week == "tue":
        session = phase.get("tuesday", [])
        focus = "Technique"
    else:
        session = phase.get("thursday", [])
        focus = "Endurance"

    parts = [f"SWIMMING — {phase.get('label', '')} ({focus} Day)"]
    parts.append(f"Gear: {swimming.get('gear_needed', 'Goggles, kickboard')}\n")

    for block in session:
        time_str = f"({block.get('time', '')}) " if block.get("time") else ""
        parts.append(f"{block['block']} {time_str}— {block['do']}\n")

    # Fallbacks
    bike = cardio.get("bike", {}).get("week_1_2", {})
    if bike:
        parts.append("---\nFALLBACK — Bike:")
        for b in bike.get("protocol", []):
            parts.append(f"  {b['block']} ({b['time']}) — {b['do']}")

    incline = cardio.get("incline_walk", {}).get("week_1_2", {})
    if incline:
        parts.append("\nFALLBACK — Incline Walk:")
        for b in incline.get("protocol", []):
            parts.append(f"  {b['block']} ({b['time']}) — {b['do']}")

    return "\n".join(parts)


def get_day_name(d):
    return d.strftime("%a").lower()


def sync_day(cal, target_date, fitness, food, profile, travel_blackouts, tracker, overrides=None, commit=False):
    """Sync a single day. Returns a report dict."""
    if overrides is None:
        overrides = {"overrides": [], "blackout_dates": []}

    report = {
        "date": target_date.isoformat(),
        "day": target_date.strftime("%A"),
        "created": 0,
        "deleted": 0,
        "skipped": [],
        "conflicts": [],
        "preserved": 0,
    }

    day_name = get_day_name(target_date)
    non_managed = get_non_managed_events(cal, target_date)
    managed = get_managed_events(cal, target_date)
    sheet_url = tracker.get("spreadsheet_url", "")

    # Check both travel.yaml blackouts and override blackouts
    extra_blackouts = set(overrides.get("blackout_dates", []))
    travel = is_travel_day(target_date, travel_blackouts | extra_blackouts, non_managed)

    # Build busy slots from non-managed events
    busy_slots = []
    for e in non_managed:
        s, end = event_to_times(e)
        if s and end:
            busy_slots.append((s, end))

    # Add work hours on weekdays
    work_days = profile["work"]["days"]
    if day_name in work_days:
        work_start = datetime.combine(
            target_date, time.fromisoformat(profile["work"]["start"]), tzinfo=TZ
        )
        work_end = datetime.combine(
            target_date, time.fromisoformat(profile["work"]["end"]), tzinfo=TZ
        )
        # Split work block around lunch break (12:00-12:45) so meals can be scheduled
        lunch_start = datetime.combine(target_date, time(12, 0), tzinfo=TZ)
        lunch_end = datetime.combine(target_date, time(12, 45), tzinfo=TZ)
        busy_slots.append((work_start, lunch_start))  # morning work
        busy_slots.append((lunch_end, work_end))       # afternoon work

    busy_slots.sort(key=lambda x: x[0])

    # --- CDC: detect manual changes before clearing ---
    snapshot = load_snapshot()
    day_changes = detect_changes(cal, target_date, snapshot)
    if day_changes:
        cdc_log = load_cdc_log()
        cdc_log["changes"].extend(day_changes)
        save_cdc_log(cdc_log)
        report["cdc_changes"] = day_changes

    # Clear ALL managed events and rebuild from scratch.
    # This ensures meals schedule around gym, not on top of it.
    # Roman's manual phone edits on non-managed events are safe (we never touch those).
    preserved_summaries = set()
    if managed:
        for e in managed:
            if commit:
                cal.delete_event(e["id"])
            report["deleted"] += 1

    # --- Determine what to schedule ---
    events_to_create = []

    cycle = fitness["program"]["cycle"]
    training_days = fitness["program"].get("training_days", ["mon", "wed", "fri"])
    prehab_days = [d for d in ["mon", "tue", "wed", "thu", "fri", "sat", "sun"] if d not in training_days]
    cardio_days = fitness.get("cardio", {}).get("preferred_days", ["tue", "thu"])
    commute_min = profile["gym"]["commute_minutes"]
    session_min = profile["gym"]["session_duration_minutes"]

    # --- LIFTING ---
    # Check for workout overrides on this date
    date_str_iso = target_date.isoformat()
    workout_override = None
    for ov in overrides.get("overrides", []):
        if ov.get("date") == date_str_iso and ov.get("type") == "add_workout":
            workout_override = ov
            break

    has_workout = day_name in training_days or workout_override is not None
    if has_workout and not travel:
        if workout_override:
            cycle_idx = workout_override["workout_index"]
        else:
            cycle_idx = training_days.index(day_name) % len(cycle)
        workout_day = cycle[cycle_idx]
        workout_name = workout_day["name"]

        # Check if gym events already preserved
        gym_exists = any("Gym:" in s for s in preserved_summaries)
        if not gym_exists:
            # Find post-work slot (or morning on weekends)
            if day_name in work_days:
                gym_start_pref = time(17, 30)
            else:
                gym_start_pref = time(10, 0)

            drive_start = find_free_slot(
                target_date, gym_start_pref,
                commute_min + session_min + commute_min, busy_slots
            )

            if drive_start:
                gym_start = drive_start + timedelta(minutes=commute_min)
                gym_end = gym_start + timedelta(minutes=session_min)
                drive_home_end = gym_end + timedelta(minutes=commute_min)

                desc = build_gym_description(workout_day, fitness, sheet_url)

                events_to_create.append(("Drive to gym", drive_start, gym_start, "", "6"))
                events_to_create.append((f"Gym: {workout_name}", gym_start, gym_end, desc, "11"))
                events_to_create.append(("Drive home from gym", gym_end, drive_home_end, "", "6"))

                busy_slots.extend([
                    (drive_start, gym_start),
                    (gym_start, gym_end),
                    (gym_end, drive_home_end),
                ])
                busy_slots.sort(key=lambda x: x[0])
            else:
                report["skipped"].append(f"Gym: {workout_name} — no free slot")

    # --- PREHAB ---
    if day_name in prehab_days and not travel:
        prehab_exists = any("Prehab" in s for s in preserved_summaries)
        if not prehab_exists:
            prehab_dur = fitness.get("prehab", {}).get("duration_minutes", 15)
            prehab_start = find_free_slot(target_date, time(6, 30), prehab_dur, busy_slots)
            if prehab_start:
                prehab_end = prehab_start + timedelta(minutes=prehab_dur)
                desc = build_prehab_description(fitness)
                events_to_create.append(("Prehab: Hips/Ankles/Core", prehab_start, prehab_end, desc, "2"))
                busy_slots.append((prehab_start, prehab_end))
                busy_slots.sort(key=lambda x: x[0])

    # --- CARDIO ---
    if day_name in cardio_days and not travel:
        cardio_exists = any("Cardio" in s for s in preserved_summaries)
        if not cardio_exists:
            cardio_dur = fitness.get("cardio", {}).get("duration_minutes", 25)
            # Try to place right after prehab
            cardio_pref = time(6, 45)
            cardio_start = find_free_slot(target_date, cardio_pref, cardio_dur, busy_slots)
            if cardio_start:
                cardio_end = cardio_start + timedelta(minutes=cardio_dur)
                focus = "Technique" if day_name == "tue" else "Endurance"
                desc = build_cardio_description(fitness, day_name)
                events_to_create.append((
                    f"Cardio: Pool Swim ({focus})",
                    cardio_start, cardio_end, desc, "3"
                ))
                busy_slots.append((cardio_start, cardio_end))
                busy_slots.sort(key=lambda x: x[0])

    # --- MEALS ---
    if not travel:
        meal_plan = load_active_meal_plan()
        if meal_plan:
            day_meals = meal_plan.get("days", {}).get(day_name, {})
            meal_times_pref = profile["meals"]["preferred_times"]
            prep_times = profile["meals"]["prep_time_minutes"]

            for meal_type in ["breakfast", "lunch", "dinner"]:
                recipe_name = day_meals.get(meal_type, "")
                if not recipe_name or recipe_name == "eating_out":
                    continue

                display = recipe_name.replace("_", " ").title()
                title = f"{meal_type.title()}: {display}"

                # Check if already preserved
                meal_exists = any(meal_type.title() in s for s in preserved_summaries)
                if meal_exists:
                    continue

                meal_time_str = meal_times_pref.get(meal_type, "12:00")
                h, m = map(int, meal_time_str.split(":"))
                cook_dur = prep_times.get(meal_type, 30)

                meal_start = find_free_slot(target_date, time(h, m), cook_dur, busy_slots)
                if meal_start:
                    meal_end = meal_start + timedelta(minutes=cook_dur)
                    desc = build_meal_description(recipe_name, food, sheet_url)
                    events_to_create.append((title, meal_start, meal_end, desc, "2"))
                    busy_slots.append((meal_start, meal_end))
                    busy_slots.sort(key=lambda x: x[0])
    elif travel:
        report["skipped"].append("All meals — travel day")

    # --- CHORES ---
    chores = profile.get("chores", {}).get("weekly", [])
    for chore in chores:
        chore_day = chore.get("preferred_day", "").lower()[:3]
        if day_name != chore_day:
            continue

        chore_name = chore["name"]
        chore_exists = any(chore_name in s for s in preserved_summaries)
        if chore_exists:
            continue

        duration = chore.get("duration_minutes", 30)
        # Schedule chores in morning on weekends, evening on weekdays
        if day_name in ["sat", "sun"]:
            start_pref = time(7, 0)
        else:
            start_pref = time(19, 0)

        chore_start = find_free_slot(target_date, start_pref, duration, busy_slots)
        if chore_start:
            chore_end = chore_start + timedelta(minutes=duration)
            events_to_create.append((chore_name, chore_start, chore_end, "", "5"))
            busy_slots.append((chore_start, chore_end))
            busy_slots.sort(key=lambda x: x[0])

    # --- TRAVEL PREP (pack night before) ---
    travel_config_path = Path("config/travel.yaml")
    if travel_config_path.exists():
        with open(travel_config_path) as f:
            travel_conf = yaml.safe_load(f) or {}

        for trip in travel_conf.get("trips", []):
            depart = trip.get("depart_date", "")
            if not trip.get("pack_night_before"):
                continue

            # Pack the night before departure
            try:
                depart_date = date.fromisoformat(depart)
                pack_date = depart_date - timedelta(days=1)
            except (ValueError, TypeError):
                continue

            if pack_date != target_date:
                continue

            pack_exists = any("Pack" in s for s in preserved_summaries)
            if pack_exists:
                continue

            pack_dur = trip.get("pack_duration_minutes", 30)
            trip_name = trip.get("name", "trip")
            flight_time = trip.get("depart_flight", "")

            pack_start = find_free_slot(target_date, time(20, 0), pack_dur, busy_slots)
            if pack_start:
                pack_end = pack_start + timedelta(minutes=pack_dur)
                desc = f"Pack for {trip_name}\nFlight: {flight_time}"
                events_to_create.append((f"Pack for {trip_name}", pack_start, pack_end, desc, "5"))
                busy_slots.append((pack_start, pack_end))
                busy_slots.sort(key=lambda x: x[0])

    # --- SYNC WORKOUT SHEET ---
    if has_workout and not travel and commit:
        try:
            from modules.workout_tracker import _get_gspread_client, _load_tracker_config
            t_config = _load_tracker_config()
            t_id = t_config.get("spreadsheet_id")
            if t_id:
                gc = _get_gspread_client()
                sh = gc.open_by_key(t_id)
                log_ws = sh.worksheet("Log")
                existing_rows = log_ws.get_all_values()
                existing_keys = set(
                    f"{r[0]}|{r[1]}" for r in existing_rows[1:] if r[0] and r[1]
                )
                date_str_sheet = target_date.isoformat()
                sheet_key = f"{date_str_sheet}|{workout_name}"
                if sheet_key not in existing_keys:
                    sheet_rows = []
                    for ex in workout_day["exercises"]:
                        for s in range(1, ex["sets"] + 1):
                            notes_parts = []
                            if ex.get("reps"):
                                notes_parts.append(f"Target: {ex['reps']}")
                            if ex.get("rest_seconds"):
                                notes_parts.append(f"Rest: {ex['rest_seconds']}s")
                            sheet_rows.append([
                                date_str_sheet, workout_name, ex["name"], s,
                                "", "", "", " | ".join(notes_parts), ""
                            ])
                    if sheet_rows:
                        log_ws.append_rows(sheet_rows, value_input_option="USER_ENTERED")
                        report["skipped"].append(f"Sheet: pre-populated {len(sheet_rows)} sets for {workout_name}")
        except Exception as e:
            report["skipped"].append(f"Sheet sync failed: {e}")

    # --- CREATE EVENTS ---
    created_events = []
    for title, start, end, desc, color in events_to_create:
        if commit:
            event_id = cal.create_event(
                title=title,
                start=start,
                end=end,
                description=desc,
                category="second_brain",
                color_id=color,
            )
            created_events.append({
                "event_id": event_id,
                "title": title,
                "start": start.isoformat(),
                "end": end.isoformat(),
            })
        else:
            created_events.append({
                "event_id": "preview",
                "title": title,
                "start": start.isoformat(),
                "end": end.isoformat(),
            })
        report["created"] += 1

    report["_snapshot_events"] = created_events
    return report


def sync(days=14, commit=False, specific_date=None):
    """Run the full sync."""
    fitness, food, profile, travel_blackouts, tracker = load_configs()
    overrides = load_overrides()

    cal = CalendarClient(
        str(Path(profile["google"]["credentials_path"]).expanduser()),
        str(Path(profile["google"]["token_path"]).expanduser()),
        profile["google"]["calendar_id"],
    )
    cal.authenticate()

    if specific_date:
        dates = [specific_date]
    else:
        today = date.today()
        dates = [today + timedelta(days=d) for d in range(days)]

    mode = "COMMIT" if commit else "PREVIEW"
    print(f"\n{'='*60}")
    print(f"  Second Brain Sync — {mode}")
    print(f"  {dates[0]} to {dates[-1]} ({len(dates)} days)")
    print(f"{'='*60}")

    # --- PHASE 1: DETECT (Sheet CDC) ---
    print(f"\n{'-'*60}")
    print("  PHASE 1: DETECT")
    print(f"{'-'*60}")

    workout_cdc = detect_workout_sheet_cdc()
    nutrition_cdc = detect_nutrition_sheet_cdc()

    if workout_cdc["insights"]:
        print(f"\n  Workout Sheet:")
        for ins in workout_cdc["insights"]:
            if ins["type"] == "exercise_skipped":
                print(f"    - {ins['date']}: Skipped {ins['exercise']}")
            elif ins["type"] == "rpe_too_high":
                print(f"    - {ins['date']}: {ins['exercise']} RPE {ins['rpe']} @ {ins['weight']} lbs — too heavy")
            elif ins["type"] == "pain_reported":
                print(f"    - {ins['date']}: {ins['exercise']} — PAIN: {ins['note']}")
            elif ins["type"] == "exercise_added_by_user":
                print(f"    - {ins['date']}: Added {ins['exercise']} — \"{ins['note']}\"")
    else:
        print(f"\n  Workout Sheet: no new input detected")

    if nutrition_cdc["insights"]:
        print(f"\n  Nutrition Sheet:")
        for ins in nutrition_cdc["insights"]:
            print(f"    - {ins['date']} {ins['meal']}: planned {ins['planned']}, ate {ins['actual']}")
    else:
        print(f"\n  Nutrition Sheet: no deviations logged")

    # --- PHASE 2: LEARN ---
    cdc_log = load_cdc_log()
    suggestions = learn_preferences(cdc_log)

    print(f"\n{'-'*60}")
    print("  PHASE 2: LEARN")
    print(f"{'-'*60}")

    if suggestions:
        for s in suggestions:
            if s["type"] == "time_preference":
                print(f"\n  SUGGESTION: Change default {s['category'].replace('_', ' ')} to {s['suggested_time']}")
                print(f"    Evidence: {s['evidence_count']} manual moves")
            elif s["type"] == "event_unwanted":
                print(f"\n  SUGGESTION: Remove \"{s['title']}\" from schedule")
                print(f"    Evidence: deleted {s['delete_count']} times")
    else:
        total_changes = len(cdc_log.get("changes", []))
        print(f"\n  CDC log has {total_changes} change(s) — need 3+ same-direction moves to suggest adjustments")

    if workout_cdc["insights"]:
        pain_reports = [i for i in workout_cdc["insights"] if i["type"] == "pain_reported"]
        rpe_issues = [i for i in workout_cdc["insights"] if i["type"] == "rpe_too_high"]
        skipped = [i for i in workout_cdc["insights"] if i["type"] == "exercise_skipped"]
        added = [i for i in workout_cdc["insights"] if i["type"] == "exercise_added_by_user"]

        if pain_reports:
            print(f"\n  ALERT: {len(pain_reports)} pain report(s) — review ailments.md")
        if rpe_issues:
            print(f"  ALERT: {len(rpe_issues)} exercise(s) at RPE 10 — consider dropping weight 10%")
        if skipped:
            exercises = set(i["exercise"] for i in skipped)
            print(f"  NOTE: Consistently skipped: {', '.join(exercises)} — consider removing or replacing")
        if added:
            exercises = set(i["exercise"] for i in added)
            print(f"  NOTE: Roman added: {', '.join(exercises)} — consider adding to program")

    # --- PHASE 3: SYNC ---
    print(f"\n{'-'*60}")
    print("  PHASE 3: SYNC")
    print(f"{'-'*60}\n")

    total_created = 0
    total_deleted = 0
    total_preserved = 0
    all_skipped = []
    all_conflicts = []
    all_cdc = []
    new_snapshot = load_snapshot() if not commit else {}

    for target_date in dates:
        report = sync_day(
            cal, target_date, fitness, food, profile,
            travel_blackouts, tracker, overrides=overrides, commit=commit,
        )

        total_created += report["created"]
        total_deleted += report["deleted"]
        total_preserved += report["preserved"]

        # Collect CDC changes
        cdc_changes = report.get("cdc_changes", [])
        all_cdc.extend(cdc_changes)

        # Save snapshot for this date
        if commit and report.get("_snapshot_events"):
            new_snapshot[report["date"]] = report["_snapshot_events"]

        has_output = report["created"] or report["skipped"] or report["conflicts"] or cdc_changes
        if has_output:
            print(f"{report['date']} ({report['day']}):")

            # Print CDC changes first
            for ch in cdc_changes:
                if ch["type"] == "time_moved":
                    old_t = ch["original_start"].split("T")[1][:5]
                    new_t = ch["new_start"].split("T")[1][:5]
                    print(f"  CDC: \"{ch['title']}\" moved {old_t} -> {new_t}")
                elif ch["type"] == "deleted":
                    print(f"  CDC: \"{ch['title']}\" was deleted by user")
                elif ch["type"] == "title_edited":
                    print(f"  CDC: title changed \"{ch['original_title']}\" -> \"{ch['new_title']}\"")

            if report["created"]:
                print(f"  + {report['created']} events {'created' if commit else 'to create'}")
            if report["preserved"]:
                print(f"  = {report['preserved']} events preserved (manual edits kept)")
            if report["deleted"]:
                print(f"  - {report['deleted']} events deleted (rebuild)")
            for s in report["skipped"]:
                print(f"  ! SKIPPED: {s}")
            for c in report["conflicts"]:
                print(f"  x CONFLICT: {c}")
            print()

        all_skipped.extend(report["skipped"])
        all_conflicts.extend(report["conflicts"])

    # Save snapshot after commit
    if commit:
        save_snapshot(new_snapshot)

    print(f"{'='*50}")
    print(f"  SUMMARY")
    print(f"  Events {'created' if commit else 'to create'}: {total_created}")
    print(f"  Events preserved: {total_preserved}")
    print(f"  Events deleted: {total_deleted}")
    if all_cdc:
        print(f"  Manual changes detected: {len(all_cdc)}")
    if all_skipped:
        print(f"  Skipped: {len(all_skipped)}")
    if all_conflicts:
        print(f"  Conflicts resolved: {len(all_conflicts)}")
    if not commit:
        print(f"\n  Run with --commit to push to Google Calendar")
    print(f"{'='*50}\n")


def main():
    parser = argparse.ArgumentParser(description="Sync second_brain to Google Calendar")
    parser.add_argument("--commit", action="store_true", help="Push changes to calendar (default: preview)")
    parser.add_argument("--days", type=int, default=14, help="Number of days to sync (default: 14)")
    parser.add_argument("--date", type=str, help="Sync a specific date (YYYY-MM-DD)")
    args = parser.parse_args()

    specific = date.fromisoformat(args.date) if args.date else None
    sync(days=args.days, commit=args.commit, specific_date=specific)


if __name__ == "__main__":
    main()
