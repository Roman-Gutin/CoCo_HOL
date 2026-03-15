"""Central scheduling engine that places time blocks around existing calendar events."""

import uuid
from datetime import datetime, date, time, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

import yaml

from core.models import TimeBlock, TimeBlockRequest, BlockCategory
from core.calendar_client import CalendarClient

TZ = ZoneInfo("America/Los_Angeles")


class Scheduler:
    """Greedy time-block scheduler that respects existing calendar events and constraints."""

    def __init__(self, profile_path: str, calendar_client: CalendarClient):
        with open(profile_path) as f:
            self.profile = yaml.safe_load(f)
        self.cal = calendar_client
        self.modules: list = []

    def register_module(self, module):
        """Register a module that can generate TimeBlockRequests."""
        self.modules.append(module)

    def get_busy_slots(self, target_date: date) -> list[tuple[datetime, datetime]]:
        """Get all busy time slots from Google Calendar for a given date."""
        events = self.cal.list_events(target_date)
        slots = []
        for event in events:
            start_str = event.get("start", {}).get("dateTime")
            end_str = event.get("end", {}).get("dateTime")
            if start_str and end_str:
                start = datetime.fromisoformat(start_str)
                end = datetime.fromisoformat(end_str)
                slots.append((start, end))
        return sorted(slots, key=lambda x: x[0])

    def get_work_block(self, target_date: date) -> Optional[tuple[datetime, datetime]]:
        """Return work hours as a busy block (weekdays only)."""
        day_name = target_date.strftime("%a").lower()
        work_days = self.profile["work"]["days"]
        if day_name not in work_days:
            return None

        work_start = time.fromisoformat(self.profile["work"]["start"])
        work_end = time.fromisoformat(self.profile["work"]["end"])
        return (
            datetime.combine(target_date, work_start, tzinfo=TZ),
            datetime.combine(target_date, work_end, tzinfo=TZ),
        )

    def collect_requests(self, target_date: date) -> list[TimeBlockRequest]:
        """Collect time block requests from all registered modules."""
        all_requests = []
        for module in self.modules:
            requests = module.generate_requests(target_date, self.profile)
            all_requests.extend(requests)
        return all_requests

    def _is_slot_free(
        self,
        start: datetime,
        end: datetime,
        busy: list[tuple[datetime, datetime]],
        placed: list[TimeBlock],
    ) -> bool:
        """Check if a time slot is free (no overlap with busy slots or placed blocks)."""
        for bs, be in busy:
            if start < be and end > bs:
                return False
        for block in placed:
            if start < block.end and end > block.start:
                return False
        return True

    def _find_slot(
        self,
        request: TimeBlockRequest,
        target_date: date,
        busy: list[tuple[datetime, datetime]],
        placed: list[TimeBlock],
        step_minutes: int = 15,
    ) -> Optional[datetime]:
        """Find the earliest available slot for a request."""
        earliest = datetime.combine(target_date, request.earliest, tzinfo=TZ)
        latest = datetime.combine(target_date, request.latest, tzinfo=TZ)
        duration = timedelta(minutes=request.duration_minutes)
        step = timedelta(minutes=step_minutes)

        current = earliest
        while current + duration <= latest + duration:
            end = current + duration
            if self._is_slot_free(current, end, busy, placed):
                return current
            current += step

        return None

    def solve(self, target_date: date) -> list[TimeBlock]:
        """Solve the scheduling problem for a given date."""
        busy = self.get_busy_slots(target_date)

        # Add work hours as busy
        work_block = self.get_work_block(target_date)
        if work_block:
            busy.append(work_block)
            busy.sort(key=lambda x: x[0])

        requests = self.collect_requests(target_date)

        # Separate into anchors (non-flexible), grouped, and flexible singles
        groups: dict[str, list[TimeBlockRequest]] = {}
        anchors: list[TimeBlockRequest] = []
        singles: list[TimeBlockRequest] = []
        for req in requests:
            if req.group_id:
                groups.setdefault(req.group_id, []).append(req)
            elif not req.flexible:
                anchors.append(req)
            else:
                singles.append(req)

        # Sort by priority
        anchors.sort(key=lambda r: r.priority)
        singles.sort(key=lambda r: r.priority)

        placed: list[TimeBlock] = []

        # 1. Place anchors first (non-flexible like dinner)
        for req in anchors:
            slot_start = self._find_slot(req, target_date, busy, placed)
            if slot_start is None:
                continue
            end = slot_start + timedelta(minutes=req.duration_minutes)
            block = TimeBlock(
                id=str(uuid.uuid4()),
                request=req,
                date=target_date,
                start=slot_start,
                end=end,
            )
            placed.append(block)

        # 2. Place grouped blocks (e.g., commute + gym + commute) — they schedule around anchors
        for group_id, group_reqs in groups.items():
            group_reqs.sort(key=lambda r: r.group_order)
            total_duration = sum(r.duration_minutes for r in group_reqs)

            # Find a contiguous slot for the whole group
            earliest = min(r.earliest for r in group_reqs)
            latest = max(r.latest for r in group_reqs)

            anchor_req = TimeBlockRequest(
                category=group_reqs[0].category,
                title="group_anchor",
                duration_minutes=total_duration,
                earliest=earliest,
                latest=latest,
                priority=min(r.priority for r in group_reqs),
            )

            slot_start = self._find_slot(anchor_req, target_date, busy, placed)
            if slot_start is None:
                continue

            # Place each block in the group contiguously
            current = slot_start
            for req in group_reqs:
                end = current + timedelta(minutes=req.duration_minutes)
                block = TimeBlock(
                    id=str(uuid.uuid4()),
                    request=req,
                    date=target_date,
                    start=current,
                    end=end,
                )
                placed.append(block)
                current = end

        # Place singles
        for req in singles:
            slot_start = self._find_slot(req, target_date, busy, placed)
            if slot_start is None:
                continue
            end = slot_start + timedelta(minutes=req.duration_minutes)
            block = TimeBlock(
                id=str(uuid.uuid4()),
                request=req,
                date=target_date,
                start=slot_start,
                end=end,
            )
            placed.append(block)

        return sorted(placed, key=lambda b: b.start)

    def commit(self, blocks: list[TimeBlock]) -> list[TimeBlock]:
        """Write placed blocks to Google Calendar."""
        if not blocks:
            return blocks

        # Clear previous managed events for this date
        self.cal.clear_managed_events(blocks[0].date)

        for block in blocks:
            event_id = self.cal.create_event(
                title=block.request.title,
                start=block.start,
                end=block.end,
                description=block.request.description,
                category=block.request.category.value,
                color_id=block.request.color_id,
            )
            block.gcal_event_id = event_id

        return blocks

    def preview(self, blocks: list[TimeBlock]) -> str:
        """Return a human-readable preview of the schedule."""
        if not blocks:
            return "No blocks scheduled."

        lines = [f"Schedule for {blocks[0].date}:", ""]
        for b in blocks:
            start = b.start.strftime("%I:%M %p")
            end = b.end.strftime("%I:%M %p")
            lines.append(f"  {start} - {end}  [{b.request.category.value}] {b.request.title}")
        return "\n".join(lines)
