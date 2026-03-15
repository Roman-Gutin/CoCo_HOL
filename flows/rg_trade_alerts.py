"""
RG_Capital Trade Alert Calendar Events.

Creates 5-minute calendar events for trade checkups, position reviews,
and strategy-specific monitoring tasks.

Google Calendar color IDs:
  1=Lavender, 2=Sage, 3=Grape, 4=Flamingo, 5=Banana,
  6=Tangerine, 7=Peacock, 8=Graphite, 9=Blueberry, 10=Basil, 11=Tomato

Usage:
    python flows/rg_trade_alerts.py                    # Preview
    python flows/rg_trade_alerts.py --commit           # Push to Google Calendar
    python flows/rg_trade_alerts.py --clear-date 2026-03-10  # Remove trade alerts for a date
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
TRADE_COLOR = "9"  # Blueberry — distinct from tangerine (RG review) and tomato (gym)
TRADE_CATEGORY = "rg_trade_alert"
MANAGED_TAG = "second_brain"


def load_profile():
    config_path = Path(__file__).resolve().parent.parent / "config" / "profile.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


def get_calendar_client(profile):
    cal = CalendarClient(
        str(Path(profile["google"]["credentials_path"]).expanduser()),
        str(Path(profile["google"]["token_path"]).expanduser()),
        profile["google"]["calendar_id"],
    )
    cal.authenticate()
    return cal


def create_trade_event(cal, target_date, hour, minute, title, description, commit=False, color_id=TRADE_COLOR):
    """Create a 5-minute trade alert event."""
    start = datetime(target_date.year, target_date.month, target_date.day,
                     hour, minute, tzinfo=TZ)
    end = start + timedelta(minutes=5)

    if commit:
        event_id = cal.create_event(
            title=f"📊 {title}",
            start=start,
            end=end,
            description=description,
            category=TRADE_CATEGORY,
            color_id=color_id,
        )
        return {"event_id": event_id, "title": title, "start": start.isoformat(), "end": end.isoformat()}
    else:
        return {"event_id": "preview", "title": title, "start": start.isoformat(), "end": end.isoformat()}


def clear_trade_alerts(cal, target_date, commit=False):
    """Remove all trade alert events for a date."""
    managed = cal.list_managed_events(target_date)
    trade_events = [
        e for e in managed
        if e.get("extendedProperties", {}).get("private", {}).get("category") == TRADE_CATEGORY
    ]
    count = 0
    for e in trade_events:
        if commit:
            cal.delete_event(e["id"])
        count += 1
    return count


# --- SCHEDULE DEFINITIONS ---

def weekday_schedule(target_date):
    """Standard weekday trade monitoring schedule."""
    events = []
    day_name = target_date.strftime("%a")

    # Pre-market scan (6:25 AM PT = before 6:30 AM market open)
    events.append({
        "hour": 6, "minute": 25,
        "title": "Pre-Market: Check Overnight Gaps",
        "description": (
            "LETF Arb: Check cross-issuer pair spreads (ETHA/ETHE, IBIT/ARKB, etc.)\n"
            "Delta One: Check IBIT-BTC basis z-score (signal starts 4AM ET / 1AM PT)\n"
            "Vol Fund: Check any CCS positions — verify no gap through strikes\n\n"
            "Action: Note any z-scores > 2.0 for intraday monitoring"
        ),
    })

    # Market open check (6:33 AM PT = 9:33 AM ET)
    events.append({
        "hour": 6, "minute": 33,
        "title": "Market Open: Position Check",
        "description": (
            "LETF Arb: Confirm pair positions opened correctly (paper acct)\n"
            "Vol Fund: CCS positions — check delta, current P&L vs PT/SL\n"
            "LS Fund: Check overnight moves on short book\n\n"
            "Alpaca paper dashboard: https://app.alpaca.markets"
        ),
    })

    # Mid-morning (7:00 AM PT = 10:00 AM ET — basis signal peak)
    events.append({
        "hour": 7, "minute": 0,
        "title": "Delta One: Basis Signal Peak Window",
        "description": (
            "IBIT-BTC basis signal peaks at 9:30-10:00 AM ET\n"
            "Check basis_zscore_12 — if |z| > 2.0, note direction\n"
            "74.5% accuracy at conviction > 0.15\n\n"
            "This is the highest-probability window for intraday signal"
        ),
    })

    # Midday (10:00 AM PT = 1:00 PM ET)
    events.append({
        "hour": 10, "minute": 0,
        "title": "Midday: LETF Arb Pair Spreads",
        "description": (
            "Check z-scores on all 7 promoted pairs\n"
            "If any pair hit entry threshold, verify paper order filled\n"
            "Monitor for mean-reversion progress on open positions\n\n"
            "Pairs: ETHA/ETHE, ETHE/FETH, ETHA/FETH, IBIT/ARKB, ARKB/FBTC, IBIT/FBTC, IBIT/GBTC"
        ),
    })

    # Afternoon (12:30 PM PT = 3:30 PM ET — rebalance hour)
    events.append({
        "hour": 12, "minute": 30,
        "title": "Pre-Close: Rebalance Hour Monitor",
        "description": (
            "LETF rebalance flow starts ~3:30 PM ET\n"
            "Check LETF Arb positions for rebalance-driven spread moves\n"
            "Vol Fund CCS: Final P&L check — close any at PT target?\n"
            "Delta One: Basis signal fades after 6 PM ET — note EOD basis for overnight signal\n\n"
            "If IBIT at EOD discount (bottom 10%): overnight long candidate (68% hit)"
        ),
    })

    return events


def generate_events(target_date):
    """Generate all trade alert events for a date."""
    day_name = target_date.strftime("%a").lower()

    # No market events on weekends
    if day_name in ("sat", "sun"):
        return []

    return weekday_schedule(target_date)


def main():
    parser = argparse.ArgumentParser(description="RG_Capital trade alert calendar events")
    parser.add_argument("--commit", action="store_true", help="Push to Google Calendar")
    parser.add_argument("--days", type=int, default=5, help="Number of days to schedule (default: 5, weekdays only)")
    parser.add_argument("--date", type=str, help="Schedule for a specific date (YYYY-MM-DD)")
    parser.add_argument("--clear-date", type=str, help="Clear trade alerts for a date (YYYY-MM-DD)")
    args = parser.parse_args()

    profile = load_profile()
    cal = get_calendar_client(profile)

    # Clear mode
    if args.clear_date:
        target = date.fromisoformat(args.clear_date)
        count = clear_trade_alerts(cal, target, commit=args.commit)
        action = "deleted" if args.commit else "would delete"
        print(f"{action} {count} trade alert(s) for {target}")
        return

    # Schedule mode
    if args.date:
        dates = [date.fromisoformat(args.date)]
    else:
        today = date.today()
        dates = []
        d = today
        while len(dates) < args.days:
            if d.strftime("%a").lower() not in ("sat", "sun"):
                dates.append(d)
            d += timedelta(days=1)

    mode = "COMMIT" if args.commit else "PREVIEW"
    print(f"\n{'='*60}")
    print(f"  RG_Capital Trade Alerts — {mode}")
    print(f"  Color: Blueberry (9) — 5-min events")
    print(f"{'='*60}\n")

    total = 0
    for target_date in dates:
        events = generate_events(target_date)
        if not events:
            continue

        print(f"{target_date} ({target_date.strftime('%A')}):")
        for ev in events:
            result = create_trade_event(
                cal, target_date,
                ev["hour"], ev["minute"],
                ev["title"], ev["description"],
                commit=args.commit,
            )
            status = "CREATED" if args.commit else "preview"
            t = datetime(target_date.year, target_date.month, target_date.day,
                         ev["hour"], ev["minute"], tzinfo=TZ)
            print(f"  {t.strftime('%I:%M %p')} — {ev['title']} [{status}]")
            total += 1
        print()

    print(f"{'='*60}")
    print(f"  Total: {total} events {'created' if args.commit else 'to create'}")
    if not args.commit:
        print(f"  Run with --commit to push to Google Calendar")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
