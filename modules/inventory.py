"""Food inventory module - tracks what's in the fridge, pantry, and freezer."""

import json
from datetime import date, datetime
from pathlib import Path
from typing import Optional

INVENTORY_PATH = Path("data/inventory.json")


def load_inventory() -> dict:
    """Load the current inventory."""
    if INVENTORY_PATH.exists():
        return json.loads(INVENTORY_PATH.read_text())
    return {"fridge": [], "pantry": [], "freezer": [], "log": [], "last_updated": None}


def save_inventory(inv: dict) -> None:
    """Save inventory to disk."""
    inv["last_updated"] = datetime.now().isoformat()
    INVENTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    INVENTORY_PATH.write_text(json.dumps(inv, indent=2))


def add_item(
    location: str,
    item: str,
    quantity: float,
    unit: str,
    weight_lbs: float = None,
    notes: str = "",
    source: str = "",
    use_by: str = None,
) -> dict:
    """Add an item to inventory."""
    inv = load_inventory()

    entry = {
        "item": item,
        "quantity": quantity,
        "unit": unit,
        "purchased": date.today().isoformat(),
        "source": source,
    }
    if weight_lbs:
        entry["weight_lbs"] = weight_lbs
    if notes:
        entry["notes"] = notes
    if use_by:
        entry["use_by"] = use_by

    inv.setdefault(location, []).append(entry)
    save_inventory(inv)
    return entry


def consume_item(item_name: str, quantity: float = None, location: str = None) -> Optional[dict]:
    """
    Consume (use up) an item or reduce its quantity.
    If quantity is None, removes the item entirely.
    Returns the consumed/updated item or None if not found.
    """
    inv = load_inventory()

    locations = [location] if location else ["fridge", "freezer", "pantry"]

    for loc in locations:
        items = inv.get(loc, [])
        for i, entry in enumerate(items):
            if entry["item"] == item_name:
                if quantity is None or entry["quantity"] <= quantity:
                    # Remove entirely
                    removed = items.pop(i)
                    inv["log"].append({
                        "date": date.today().isoformat(),
                        "action": "consumed",
                        "item": item_name,
                        "quantity": removed["quantity"],
                        "unit": removed.get("unit", ""),
                    })
                    save_inventory(inv)
                    return removed
                else:
                    # Reduce quantity
                    entry["quantity"] -= quantity
                    inv["log"].append({
                        "date": date.today().isoformat(),
                        "action": "consumed_partial",
                        "item": item_name,
                        "quantity_used": quantity,
                        "remaining": entry["quantity"],
                        "unit": entry.get("unit", ""),
                    })
                    save_inventory(inv)
                    return entry

    return None


def move_item(item_name: str, from_loc: str, to_loc: str) -> Optional[dict]:
    """Move an item between locations (e.g., fridge -> freezer)."""
    inv = load_inventory()
    items = inv.get(from_loc, [])

    for i, entry in enumerate(items):
        if entry["item"] == item_name:
            moved = items.pop(i)
            inv.setdefault(to_loc, []).append(moved)
            inv["log"].append({
                "date": date.today().isoformat(),
                "action": "moved",
                "item": item_name,
                "from": from_loc,
                "to": to_loc,
            })
            save_inventory(inv)
            return moved

    return None


def get_expiring_soon(days: int = 3) -> list[dict]:
    """Get items expiring within N days."""
    inv = load_inventory()
    today = date.today()
    expiring = []

    for loc in ["fridge", "freezer"]:
        for item in inv.get(loc, []):
            use_by = item.get("use_by")
            if use_by:
                exp_date = date.fromisoformat(use_by)
                days_left = (exp_date - today).days
                if days_left <= days:
                    expiring.append({
                        **item,
                        "location": loc,
                        "days_left": days_left,
                    })

    return sorted(expiring, key=lambda x: x["days_left"])


def get_available_proteins() -> list[dict]:
    """Get all protein items across fridge and freezer."""
    inv = load_inventory()
    proteins = {"ground_beef", "chicken_breast", "chicken_thigh", "salmon",
                "turkey_deli", "steak", "pork", "shrimp", "tuna", "eggs"}
    available = []
    for loc in ["fridge", "freezer"]:
        for item in inv.get(loc, []):
            if item["item"] in proteins or any(p in item["item"] for p in proteins):
                available.append({**item, "location": loc})
    return available


def inventory_summary() -> str:
    """Human-readable inventory summary."""
    inv = load_inventory()
    lines = [f"Food Inventory (updated {inv.get('last_updated', 'never')})", ""]

    for loc in ["fridge", "freezer", "pantry"]:
        items = inv.get(loc, [])
        if not items:
            continue
        lines.append(f"{loc.upper()} ({len(items)} items):")
        for item in items:
            name = item["item"].replace("_", " ").title()
            qty = f"{item['quantity']} {item.get('unit', '')}"
            use_by = item.get("use_by", "")
            exp_str = f" (use by {use_by})" if use_by else ""
            notes = f" — {item['notes']}" if item.get("notes") else ""
            lines.append(f"  {name}: {qty}{exp_str}{notes}")
        lines.append("")

    expiring = get_expiring_soon(3)
    if expiring:
        lines.append("EXPIRING SOON:")
        for item in expiring:
            name = item["item"].replace("_", " ").title()
            lines.append(f"  {name}: {item['days_left']} days left ({item['location']})")

    return "\n".join(lines)


def ingest_receipt(items: list[dict], source: str = "", total: float = 0) -> None:
    """
    Bulk add items from a receipt scan.
    Each item dict: {item, quantity, unit, location, weight_lbs?, notes?, use_by?}
    """
    inv = load_inventory()

    for entry in items:
        loc = entry.pop("location", "fridge")
        entry["purchased"] = date.today().isoformat()
        entry["source"] = source
        inv.setdefault(loc, []).append(entry)

    if total > 0:
        inv["log"].append({
            "date": date.today().isoformat(),
            "action": "purchased",
            "source": source,
            "total": total,
            "items_count": len(items),
        })

    save_inventory(inv)
