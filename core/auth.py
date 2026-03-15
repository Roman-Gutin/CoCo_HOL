"""Centralized Google OAuth for all second_brain services."""

from pathlib import Path

ALL_SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/tasks",
    "https://www.googleapis.com/auth/presentations",
]


def authenticate(credentials_path: str = None, token_path: str = None):
    """
    Authenticate with all Google APIs.
    Uses InstalledAppFlow.run_local_server() for automatic browser-based auth.
    Returns credentials object.
    """
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    if credentials_path is None:
        credentials_path = "~/.config/second_brain/google_credentials.json"
    if token_path is None:
        token_path = "~/.config/second_brain/token.json"

    creds_path = Path(credentials_path).expanduser()
    tok_path = Path(token_path).expanduser()

    creds = None
    if tok_path.exists():
        creds = Credentials.from_authorized_user_file(str(tok_path), ALL_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(creds_path), ALL_SCOPES
            )
            creds = flow.run_local_server(port=8090, open_browser=True)

        tok_path.parent.mkdir(parents=True, exist_ok=True)
        tok_path.write_text(creds.to_json())

    return creds


if __name__ == "__main__":
    creds = authenticate()
    print(f"Authenticated with scopes: {creds.scopes}")
