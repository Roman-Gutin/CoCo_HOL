"""Gmail API client for sending and reading emails."""

import base64
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Optional

from core.auth import ALL_SCOPES

SCOPES = ALL_SCOPES

LABEL_PROCESSED = "second_brain_processed"


class EmailClient:
    """Gmail API wrapper for the second brain system."""

    def __init__(self, credentials_path: str, token_path: str):
        self.credentials_path = Path(credentials_path).expanduser()
        self.token_path = Path(token_path).expanduser()
        self.service = None
        self.user_email = None

    def authenticate(self) -> None:
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
                # Need to re-auth with expanded scopes
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path), SCOPES
                )
                creds = flow.run_local_server(port=0)

            self.token_path.parent.mkdir(parents=True, exist_ok=True)
            self.token_path.write_text(creds.to_json())

        self.service = build("gmail", "v1", credentials=creds)

        # Also rebuild calendar service with new creds for CalendarClient
        # Get user's email
        profile = self.service.users().getProfile(userId="me").execute()
        self.user_email = profile["emailAddress"]

    def _ensure_service(self):
        if not self.service:
            self.authenticate()

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html: bool = False,
        thread_id: Optional[str] = None,
        message_id: Optional[str] = None,
    ) -> dict:
        """Send an email. Returns the sent message metadata."""
        self._ensure_service()

        msg = MIMEMultipart("alternative") if html else MIMEText(body)
        if html:
            msg.attach(MIMEText(body, "plain"))
            msg.attach(MIMEText(body, "html"))

        msg["to"] = to
        msg["from"] = self.user_email
        msg["subject"] = subject

        # Thread replies together
        if message_id:
            msg["In-Reply-To"] = message_id
            msg["References"] = message_id

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        send_body = {"raw": raw}
        if thread_id:
            send_body["threadId"] = thread_id

        result = self.service.users().messages().send(
            userId="me", body=send_body
        ).execute()

        return result

    def find_replies(self, subject_contains: str, after_date: str = None) -> list[dict]:
        """
        Find reply emails matching a subject pattern.

        Args:
            subject_contains: String to search in subject
            after_date: Only find emails after this date (YYYY/MM/DD)

        Returns:
            List of message dicts with id, threadId, subject, body, date
        """
        self._ensure_service()

        query = f"subject:({subject_contains}) is:inbox"
        if after_date:
            query += f" after:{after_date}"

        result = self.service.users().messages().list(
            userId="me", q=query, maxResults=10
        ).execute()

        messages = result.get("messages", [])
        replies = []

        for msg_meta in messages:
            msg = self.service.users().messages().get(
                userId="me", id=msg_meta["id"], format="full"
            ).execute()

            headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}

            # Skip if this is our own sent message (not a reply)
            if "SENT" in msg.get("labelIds", []) and "INBOX" not in msg.get("labelIds", []):
                continue

            # Extract body
            body = self._extract_body(msg["payload"])

            replies.append({
                "id": msg["id"],
                "threadId": msg["threadId"],
                "subject": headers.get("Subject", ""),
                "from": headers.get("From", ""),
                "date": headers.get("Date", ""),
                "body": body,
                "message_id": headers.get("Message-ID", ""),
            })

        return replies

    def _extract_body(self, payload: dict) -> str:
        """Extract plain text body from a message payload."""
        if payload.get("mimeType") == "text/plain":
            data = payload.get("body", {}).get("data", "")
            if data:
                return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

        parts = payload.get("parts", [])
        for part in parts:
            if part.get("mimeType") == "text/plain":
                data = part.get("body", {}).get("data", "")
                if data:
                    return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
            # Recurse into nested parts
            if part.get("parts"):
                result = self._extract_body(part)
                if result:
                    return result

        return ""

    def mark_as_read(self, message_id: str) -> None:
        """Mark a message as read."""
        self._ensure_service()
        self.service.users().messages().modify(
            userId="me",
            id=message_id,
            body={"removeLabelIds": ["UNREAD"]},
        ).execute()

    def add_label(self, message_id: str, label: str) -> None:
        """Add a label to a message (creates label if needed)."""
        self._ensure_service()
        label_id = self._get_or_create_label(label)
        self.service.users().messages().modify(
            userId="me",
            id=message_id,
            body={"addLabelIds": [label_id]},
        ).execute()

    def _get_or_create_label(self, label_name: str) -> str:
        """Get label ID by name, creating it if it doesn't exist."""
        labels = self.service.users().labels().list(userId="me").execute()
        for label in labels.get("labels", []):
            if label["name"] == label_name:
                return label["id"]

        result = self.service.users().labels().create(
            userId="me",
            body={
                "name": label_name,
                "labelListVisibility": "labelShow",
                "messageListVisibility": "show",
            },
        ).execute()
        return result["id"]
