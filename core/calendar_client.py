"""Google Calendar API client for the second brain system."""

import os
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional

# Lazy imports - only needed when actually connecting to Google
# from google.auth.transport.requests import Request
# from google.oauth2.credentials import Credentials
# from google_auth_oauthlib.flow import InstalledAppFlow
# from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]
MANAGED_TAG = "second_brain"


class CalendarClient:
    """Thin wrapper around the Google Calendar API."""

    def __init__(self, credentials_path: str, token_path: str, calendar_id: str = "primary"):
        self.credentials_path = Path(credentials_path).expanduser()
        self.token_path = Path(token_path).expanduser()
        self.calendar_id = calendar_id
        self.service = None

    def authenticate(self) -> None:
        """Authenticate with Google Calendar API using OAuth2."""
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build

        creds = None

        if self.token_path.exists():
            creds = Credentials.from_authorized_user_file(str(self.token_path), SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not self.credentials_path.exists():
                    raise FileNotFoundError(
                        f"Google credentials not found at {self.credentials_path}. "
                        "Download OAuth 2.0 credentials from Google Cloud Console "
                        "and save them there."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path), SCOPES
                )
                creds = flow.run_local_server(port=0)

            self.token_path.parent.mkdir(parents=True, exist_ok=True)
            self.token_path.write_text(creds.to_json())

        self.service = build("calendar", "v3", credentials=creds)

    def _ensure_service(self):
        if not self.service:
            self.authenticate()

    def list_events(self, target_date: date) -> list[dict]:
        """List all events for a given date."""
        self._ensure_service()
        from zoneinfo import ZoneInfo

        tz = ZoneInfo("America/Los_Angeles")
        start = datetime.combine(target_date, datetime.min.time(), tzinfo=tz).isoformat()
        end = datetime.combine(target_date + timedelta(days=1), datetime.min.time(), tzinfo=tz).isoformat()

        result = self.service.events().list(
            calendarId=self.calendar_id,
            timeMin=start,
            timeMax=end,
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        return result.get("items", [])

    def list_managed_events(self, target_date: date) -> list[dict]:
        """List only events created by second_brain for a given date."""
        events = self.list_events(target_date)
        return [
            e for e in events
            if e.get("extendedProperties", {}).get("private", {}).get("managed_by") == MANAGED_TAG
        ]

    def create_event(
        self,
        title: str,
        start: datetime,
        end: datetime,
        description: str = "",
        category: str = "",
        color_id: Optional[str] = None,
    ) -> str:
        """Create a calendar event. Returns the event ID."""
        self._ensure_service()

        event_body = {
            "summary": title,
            "description": description,
            "start": {"dateTime": start.isoformat(), "timeZone": "America/Los_Angeles"},
            "end": {"dateTime": end.isoformat(), "timeZone": "America/Los_Angeles"},
            "extendedProperties": {
                "private": {
                    "managed_by": MANAGED_TAG,
                    "category": category,
                }
            },
        }

        if color_id:
            event_body["colorId"] = color_id

        result = self.service.events().insert(
            calendarId=self.calendar_id, body=event_body
        ).execute()

        return result["id"]

    def delete_event(self, event_id: str) -> None:
        """Delete a calendar event by ID."""
        self._ensure_service()
        self.service.events().delete(
            calendarId=self.calendar_id, eventId=event_id
        ).execute()

    def clear_managed_events(self, target_date: date) -> int:
        """Delete all second_brain-managed events for a given date. Returns count deleted."""
        managed = self.list_managed_events(target_date)
        for event in managed:
            self.delete_event(event["id"])
        return len(managed)
