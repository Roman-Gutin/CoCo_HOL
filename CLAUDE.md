# Second Brain - Roman's Personal Life Management System

## Purpose
Ambient system to manage Roman's physical-world life: fitness, food, chores, entrepreneurship (RG_Capital), and social time. Dynamically schedules around work hours (8:30 AM - 5:00 PM PST).

## Architecture
- **config/**: YAML configs for profile, fitness, food, chores
- **core/**: Calendar client (Google API), scheduler engine, Pydantic models
- **modules/**: Domain modules (fitness, food, entrepreneurship, journal) - each generates `TimeBlockRequest` objects
- **flows/**: Entry points (morning_plan, evening_review, weekly_prep)
- **data/**: Journal entries, meal plans, grocery lists (JSON artifacts)

## Key Patterns
- Modules produce `TimeBlockRequest` objects; the central `Scheduler` resolves conflicts and commits to Google Calendar
- All second_brain calendar events are tagged with `managed_by: second_brain` extended property so they can be identified and replaced
- Config-driven: change behavior via YAML, not code
- RG_Capital integration reads from `/home/roman/RG_Capital/` artifacts (read-only)

## Constraints
- Roman lives in Las Vegas
- Works 8:30 AM - 5:00 PM PST weekdays
- Gym is 20 min drive each way
- Training: 3 days/week (Mon, Wed, Fri): Chest/Tri, Back/Shoulder/Bicep, Legs
- Non-lifting days: prehab mornings (15 min) + cardio on Tue/Thu (25 min)
- No running until ankle/knee/hip mobility confirmed — pool/bike/incline walk only

## Running
```bash
# Sync calendar (preview)
python flows/sync_calendar.py

# Sync calendar (commit to Google Calendar)
python flows/sync_calendar.py --commit

# Sync specific date
python flows/sync_calendar.py --date 2026-03-10 --commit

# Preview tomorrow's schedule
python flows/morning_plan.py --date 2026-03-08

# Commit to Google Calendar
python flows/morning_plan.py --commit

# Generate weekly meal plan
python flows/weekly_prep.py

# Evening journal
python flows/evening_review.py
```

## Google Calendar Setup
1. Create a Google Cloud project, enable Calendar API
2. Create OAuth 2.0 credentials (Desktop app)
3. Download as `google_credentials.json` to `~/.config/second_brain/`
4. First run will open browser for OAuth consent
