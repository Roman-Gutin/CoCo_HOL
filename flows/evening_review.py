"""Evening review flow - generates journal entry and reviews the day."""

import sys
from datetime import date
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.journal import create_entry, load_entry
from modules.entrepreneurship import pull_daily_pnl


def load_profile() -> dict:
    with open("config/profile.yaml") as f:
        return yaml.safe_load(f)


def evening_review(target_date: date | None = None) -> str:
    """Run the evening review and generate/update journal entry."""
    if target_date is None:
        target_date = date.today()

    profile = load_profile()

    # Check if entry already exists
    existing = load_entry(target_date)

    # Pull trading PnL
    pnl = pull_daily_pnl(target_date, profile)

    pnl_summary = "No trading data available."
    if pnl:
        pnl_summary = f"Total PnL: ${pnl.total_pnl:,.2f}"
        if pnl.by_desk:
            desk_lines = [f"  {desk}: ${val:,.2f}" for desk, val in pnl.by_desk.items()]
            pnl_summary += "\n" + "\n".join(desk_lines)

    if existing:
        # Update with PnL if we have it
        if pnl:
            existing.pnl = pnl
        from modules.journal import save_entry
        save_entry(existing)
        return f"Updated journal for {target_date}\n{pnl_summary}"
    else:
        entry = create_entry(target_date, profile)
        return f"Created journal for {target_date}\n{pnl_summary}"


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Evening review")
    parser.add_argument("--date", type=str, help="Date (YYYY-MM-DD)")
    args = parser.parse_args()

    target = date.fromisoformat(args.date) if args.date else None
    result = evening_review(target)
    print(result)


if __name__ == "__main__":
    main()
