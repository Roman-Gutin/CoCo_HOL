"""Journal module - daily entry generation combining all life data."""

import json
from datetime import date
from pathlib import Path

from core.models import JournalEntry, DailyPnL
from modules.entrepreneurship import pull_daily_pnl


def create_entry(
    target_date: date,
    profile: dict,
    accomplishments: list[str] | None = None,
    workouts_completed: list[str] | None = None,
    meals_cooked: list[str] | None = None,
    chores_done: list[str] | None = None,
    reflections: str = "",
    tomorrow_priorities: list[str] | None = None,
) -> JournalEntry:
    """Create a journal entry for the given date."""
    pnl = pull_daily_pnl(target_date, profile)

    entry = JournalEntry(
        date=target_date.isoformat(),
        pnl=pnl,
        accomplishments=accomplishments or [],
        workouts_completed=workouts_completed or [],
        meals_cooked=meals_cooked or [],
        chores_done=chores_done or [],
        reflections=reflections,
        tomorrow_priorities=tomorrow_priorities or [],
    )

    save_entry(entry)
    return entry


def save_entry(entry: JournalEntry) -> Path:
    """Save a journal entry to disk."""
    out_dir = Path("data/journal")
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{entry.date}.json"
    path.write_text(entry.model_dump_json(indent=2))
    return path


def load_entry(target_date: date) -> JournalEntry | None:
    """Load a journal entry from disk."""
    path = Path(f"data/journal/{target_date.isoformat()}.json")
    if path.exists():
        return JournalEntry.model_validate_json(path.read_text())
    return None


def list_entries(limit: int = 30) -> list[JournalEntry]:
    """List recent journal entries."""
    journal_dir = Path("data/journal")
    if not journal_dir.exists():
        return []

    files = sorted(journal_dir.glob("*.json"), reverse=True)[:limit]
    entries = []
    for f in files:
        entries.append(JournalEntry.model_validate_json(f.read_text()))
    return entries
