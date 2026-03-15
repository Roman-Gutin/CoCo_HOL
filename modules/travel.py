"""Travel module - packing, airport commute, and trip prep blocks."""

from datetime import date, time, timedelta

import yaml

from core.models import TimeBlockRequest, BlockCategory

COLOR_TRAVEL = "5"  # banana


def load_travel_config(path: str = "config/travel.yaml") -> dict:
    try:
        with open(path) as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}


def generate_requests(target_date: date, profile: dict) -> list[TimeBlockRequest]:
    """Generate travel prep blocks (packing night before, airport commute)."""
    config = load_travel_config()
    requests = []
    trips = config.get("trips", [])

    for trip in trips:
        depart_date = date.fromisoformat(trip["depart_date"])
        pack_night = depart_date - timedelta(days=1)

        # Pack the night before
        if target_date == pack_night and trip.get("pack_night_before", True):
            pack_mins = trip.get("pack_duration_minutes", 30)
            requests.append(
                TimeBlockRequest(
                    category=BlockCategory.CHORE,
                    title=f"Pack for {trip['name']}",
                    duration_minutes=pack_mins,
                    earliest=time(19, 0),
                    latest=time(22, 0),
                    priority=2,
                    description=f"Pack for {trip['name']} trip. Flight: {trip.get('depart_flight', 'TBD')}",
                    color_id=COLOR_TRAVEL,
                )
            )

    return requests
