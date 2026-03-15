"""
Workout tracker - Google Sheets integration for logging sets/reps/weight,
tracking progress over time, and generating coaching insights.

Creates one master spreadsheet with tabs:
- Log: date, workout, exercise, sets, reps, weight, rpe, notes
- Progress: weekly volume/PR tracking per exercise
- Coach: auto-generated insights and recommendations
"""

import json
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import gspread
from google.oauth2.credentials import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

TRACKER_CONFIG = Path("data/workout_tracker.json")

# Exercise database with target progressions
EXERCISES = {
    "Bench Press": {"type": "compound", "muscle": "chest", "progression": "weight"},
    "OHP": {"type": "compound", "muscle": "shoulders", "progression": "weight"},
    "Incline DB Press": {"type": "compound", "muscle": "chest", "progression": "weight"},
    "Lateral Raises": {"type": "isolation", "muscle": "shoulders", "progression": "reps"},
    "Tricep Pushdowns": {"type": "isolation", "muscle": "triceps", "progression": "reps"},
    "Deadlift": {"type": "compound", "muscle": "back", "progression": "weight"},
    "Pull-ups": {"type": "compound", "muscle": "back", "progression": "reps"},
    "Barbell Rows": {"type": "compound", "muscle": "back", "progression": "weight"},
    "Face Pulls": {"type": "isolation", "muscle": "rear_delts", "progression": "reps"},
    "Barbell Curls": {"type": "isolation", "muscle": "biceps", "progression": "reps"},
    "Squats": {"type": "compound", "muscle": "quads", "progression": "weight"},
    "Romanian DL": {"type": "compound", "muscle": "hamstrings", "progression": "weight"},
    "Leg Press": {"type": "compound", "muscle": "quads", "progression": "weight"},
    "Leg Curls": {"type": "isolation", "muscle": "hamstrings", "progression": "reps"},
    "Calf Raises": {"type": "isolation", "muscle": "calves", "progression": "reps"},
    "Weighted Pull-ups": {"type": "compound", "muscle": "back", "progression": "weight"},
    "DB Bench": {"type": "compound", "muscle": "chest", "progression": "weight"},
    "Cable Rows": {"type": "compound", "muscle": "back", "progression": "weight"},
}


def _get_gspread_client() -> gspread.Client:
    """Authenticate with Google Sheets using existing OAuth token."""
    token_path = Path("~/.config/second_brain/token.json").expanduser()
    creds = Credentials.from_authorized_user_file(
        str(token_path),
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.file",
        ],
    )
    return gspread.authorize(creds)


def _load_tracker_config() -> dict:
    if TRACKER_CONFIG.exists():
        return json.loads(TRACKER_CONFIG.read_text())
    return {}


def _save_tracker_config(config: dict):
    TRACKER_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    TRACKER_CONFIG.write_text(json.dumps(config, indent=2))


def create_spreadsheet() -> str:
    """Create the workout tracker spreadsheet. Returns the spreadsheet URL."""
    gc = _get_gspread_client()

    sh = gc.create("RG Fitness Tracker")

    # --- LOG tab ---
    log_ws = sh.sheet1
    log_ws.update_title("Log")
    log_ws.update("A1:I1", [[
        "Date", "Workout", "Exercise", "Set", "Reps", "Weight (lbs)",
        "RPE", "Notes", "Volume (reps × lbs)"
    ]])
    # Bold header, freeze row 1
    log_ws.format("A1:I1", {"textFormat": {"bold": True}})
    log_ws.freeze(rows=1)
    # Set column widths
    log_ws.update("I2", [["=IF(E2*F2>0,E2*F2,\"\")"]])  # volume formula template

    # --- PROGRESS tab ---
    progress_ws = sh.add_worksheet("Progress", rows=200, cols=10)
    progress_ws.update("A1:F1", [[
        "Week", "Exercise", "Total Volume", "Max Weight", "Total Sets", "Trend"
    ]])
    progress_ws.format("A1:F1", {"textFormat": {"bold": True}})
    progress_ws.freeze(rows=1)

    # --- PRs tab ---
    pr_ws = sh.add_worksheet("PRs", rows=50, cols=6)
    pr_ws.update("A1:F1", [[
        "Exercise", "1RM Est", "Best Set (Weight × Reps)", "Date Achieved", "Previous PR", "Improvement"
    ]])
    pr_ws.format("A1:F1", {"textFormat": {"bold": True}})
    pr_ws.freeze(rows=1)

    # Seed PR rows with exercises
    pr_rows = [[ex, "", "", "", "", ""] for ex in EXERCISES.keys()]
    if pr_rows:
        pr_ws.update(f"A2:F{len(pr_rows)+1}", pr_rows)

    # --- Coach tab ---
    coach_ws = sh.add_worksheet("Coach", rows=50, cols=3)
    coach_ws.update("A1:C1", [["Date", "Insight", "Action"]])
    coach_ws.format("A1:C1", {"textFormat": {"bold": True}})
    coach_ws.freeze(rows=1)

    # --- Body tab ---
    body_ws = sh.add_worksheet("Body", rows=200, cols=5)
    body_ws.update("A1:E1", [["Date", "Weight (lbs)", "Sleep (hrs)", "Energy (1-10)", "Notes"]])
    body_ws.format("A1:E1", {"textFormat": {"bold": True}})
    body_ws.freeze(rows=1)

    url = sh.url
    sheet_id = sh.id

    # Save config
    config = _load_tracker_config()
    config["spreadsheet_id"] = sheet_id
    config["spreadsheet_url"] = url
    config["created_at"] = datetime.now().isoformat()
    _save_tracker_config(config)

    return url


def get_spreadsheet_url() -> Optional[str]:
    """Get the tracker spreadsheet URL."""
    config = _load_tracker_config()
    return config.get("spreadsheet_url")


def log_workout(
    workout_name: str,
    exercises: list[dict],
    workout_date: date = None,
) -> str:
    """
    Log a workout to the spreadsheet.

    exercises: list of dicts with keys:
        exercise, sets (list of {reps, weight, rpe?, notes?})
    """
    if workout_date is None:
        workout_date = date.today()

    config = _load_tracker_config()
    sheet_id = config.get("spreadsheet_id")
    if not sheet_id:
        raise RuntimeError("Tracker not created yet. Run create_spreadsheet() first.")

    gc = _get_gspread_client()
    sh = gc.open_by_key(sheet_id)
    log_ws = sh.worksheet("Log")

    rows = []
    for ex in exercises:
        ex_name = ex["exercise"]
        for i, s in enumerate(ex.get("sets", []), 1):
            reps = s.get("reps", 0)
            weight = s.get("weight", 0)
            rpe = s.get("rpe", "")
            notes = s.get("notes", "")
            volume = reps * weight if weight > 0 else ""
            rows.append([
                workout_date.isoformat(),
                workout_name,
                ex_name,
                i,
                reps,
                weight,
                rpe,
                notes,
                volume,
            ])

    if rows:
        log_ws.append_rows(rows, value_input_option="USER_ENTERED")

    return f"Logged {len(rows)} sets for {workout_name} on {workout_date}"


def prepopulate_workout(workout_name: str, exercises: list[dict], workout_date: date = None) -> str:
    """
    Pre-populate the Log tab with empty rows for a planned workout.
    Roman just fills in weight/reps/RPE at the gym.

    exercises: list of dicts from fitness.yaml with keys: name, sets, reps
    """
    if workout_date is None:
        workout_date = date.today()

    config = _load_tracker_config()
    sheet_id = config.get("spreadsheet_id")
    if not sheet_id:
        return "No tracker spreadsheet yet"

    gc = _get_gspread_client()
    sh = gc.open_by_key(sheet_id)
    log_ws = sh.worksheet("Log")

    # Check if already populated for this date + workout
    existing = log_ws.get_all_values()
    date_str = workout_date.isoformat()
    already_done = any(
        row[0] == date_str and row[1] == workout_name
        for row in existing[1:]  # skip header
    )
    if already_done:
        return f"Already populated for {workout_name} on {date_str}"

    rows = []
    for ex in exercises:
        name = ex.get("name", ex) if isinstance(ex, dict) else ex
        num_sets = ex.get("sets", 3) if isinstance(ex, dict) else 3
        target_reps = ex.get("reps", "") if isinstance(ex, dict) else ""

        for s in range(1, num_sets + 1):
            rows.append([
                date_str,
                workout_name,
                name,
                s,
                "",  # reps (fill at gym)
                "",  # weight (fill at gym)
                "",  # RPE (fill at gym)
                f"Target: {target_reps}" if target_reps else "",
                "",  # volume (auto-calc later)
            ])

    if rows:
        log_ws.append_rows(rows, value_input_option="USER_ENTERED")

    return f"Pre-populated {len(rows)} sets for {workout_name} on {date_str}"


def get_calendar_link() -> str:
    """Get the link to embed in calendar events."""
    url = get_spreadsheet_url()
    if url:
        return f"\nTrack your workout: {url}\n"
    return ""


def generate_coaching_insights() -> list[dict]:
    """
    Analyze workout log and generate coaching insights.
    Returns list of {insight, action} dicts.
    """
    config = _load_tracker_config()
    sheet_id = config.get("spreadsheet_id")
    if not sheet_id:
        return []

    gc = _get_gspread_client()
    sh = gc.open_by_key(sheet_id)
    log_ws = sh.worksheet("Log")

    records = log_ws.get_all_records()
    if not records:
        return [{"insight": "No workouts logged yet", "action": "Log your first workout!"}]

    insights = []

    # Volume by exercise
    exercise_volume: dict[str, list[float]] = {}
    exercise_max: dict[str, float] = {}
    for r in records:
        ex = r.get("Exercise", "")
        vol = r.get("Volume (reps × lbs)", 0)
        weight = r.get("Weight (lbs)", 0)
        if ex:
            exercise_volume.setdefault(ex, []).append(float(vol) if vol else 0)
            if weight:
                exercise_max[ex] = max(exercise_max.get(ex, 0), float(weight))

    # Find exercises with no recent progress
    for ex, volumes in exercise_volume.items():
        if len(volumes) >= 6:
            recent_avg = sum(volumes[-3:]) / 3
            older_avg = sum(volumes[-6:-3]) / 3
            if older_avg > 0 and recent_avg <= older_avg:
                insights.append({
                    "insight": f"{ex}: volume has plateaued ({recent_avg:.0f} vs {older_avg:.0f})",
                    "action": f"Try increasing weight by 5 lbs or adding a set to {ex}",
                })

    # Workout frequency check
    dates = set(r.get("Date", "") for r in records)
    if len(dates) >= 2:
        sorted_dates = sorted(dates)
        recent = sorted_dates[-7:]  # last 7 sessions
        if len(recent) < 3:
            insights.append({
                "insight": "Frequency is low — fewer than 3 sessions in the last recorded week",
                "action": "Aim for 4 sessions/week minimum for your PPL+Upper split",
            })

    return insights


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Workout tracker")
    parser.add_argument("action", choices=["create", "url", "coach"])
    args = parser.parse_args()

    if args.action == "create":
        url = create_spreadsheet()
        print(f"Spreadsheet created: {url}")
    elif args.action == "url":
        url = get_spreadsheet_url()
        print(url or "No tracker created yet")
    elif args.action == "coach":
        insights = generate_coaching_insights()
        for i in insights:
            print(f"- {i['insight']}")
            print(f"  Action: {i['action']}")


if __name__ == "__main__":
    main()
