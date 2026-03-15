"""Entrepreneurship module - RG_Capital PnL tracking and review time blocks."""

import json
from datetime import date, time
from pathlib import Path
from typing import Optional

from core.models import TimeBlockRequest, BlockCategory, DailyPnL

COLOR_RG = "6"  # tangerine


def pull_daily_pnl(target_date: date, profile: dict) -> Optional[DailyPnL]:
    """
    Pull PnL data from RG_Capital artifacts.

    Reads from fund POV JSONs and portfolio data.
    Returns None if no data is available for the date.
    """
    rg_config = profile.get("rg_capital", {})
    project_root = Path(rg_config.get("project_root", "/home/roman/RG_Capital"))

    # Try to read fund POV artifacts
    pov_dir = project_root / "org" / "artifacts" / "fund_pov"
    total_pnl = 0.0
    by_desk: dict[str, float] = {}
    found_data = False

    desks = rg_config.get("desks", [])

    for desk in desks:
        # Look for daily PnL files - adapt to actual RG_Capital output format
        desk_dir = project_root / desk
        pnl_file = desk_dir / "data" / f"pnl_{target_date.isoformat()}.json"

        if pnl_file.exists():
            found_data = True
            data = json.loads(pnl_file.read_text())
            desk_pnl = data.get("pnl", 0.0)
            by_desk[desk] = desk_pnl
            total_pnl += desk_pnl

    # Also try the portfolio-level summary
    portfolio_pnl = project_root / "portfolio_mgmt" / "data" / f"daily_pnl_{target_date.isoformat()}.json"
    if portfolio_pnl.exists():
        found_data = True
        data = json.loads(portfolio_pnl.read_text())
        total_pnl = data.get("total_pnl", total_pnl)
        by_desk = data.get("by_desk", by_desk)

    if not found_data:
        return None

    return DailyPnL(
        date=target_date.isoformat(),
        total_pnl=total_pnl,
        by_desk=by_desk,
    )


def generate_requests(target_date: date, profile: dict) -> list[TimeBlockRequest]:
    """Generate time blocks for RG_Capital review."""
    requests = []
    day_name = target_date.strftime("%a").lower()

    # Only on weekdays (markets are open)
    if day_name not in profile["work"]["days"]:
        return requests

    rg_config = profile.get("rg_capital", {})
    review_duration = rg_config.get("review_duration_minutes", 30)
    review_time = time.fromisoformat(rg_config.get("preferred_review_time", "21:00"))

    requests.append(
        TimeBlockRequest(
            category=BlockCategory.RG_REVIEW,
            title="RG Capital: Daily Review",
            duration_minutes=review_duration,
            earliest=time(20, 0),
            latest=time(22, 0),
            priority=3,
            description=(
                "Review today's trading performance:\n"
                "- Check PnL by desk\n"
                "- Review strategy execution\n"
                "- Note any anomalies or opportunities\n"
                "- Update journal"
            ),
            color_id=COLOR_RG,
        )
    )

    return requests
