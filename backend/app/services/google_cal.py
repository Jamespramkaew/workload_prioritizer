import secrets
import hashlib
import base64
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request as GoogleRequest
from googleapiclient.discovery import build
from app.core.config import settings

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

_CLIENT_CONFIG = {
    "web": {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
    }
}


def _pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(48)
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).rstrip(b'=').decode()
    return verifier, challenge


def get_oauth_url(user_id: str) -> str:
    flow = Flow.from_client_config(_CLIENT_CONFIG, scopes=SCOPES)
    flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
    verifier, challenge = _pkce_pair()
    # เข้ารหัส user_id + verifier ใน state เพื่อส่งกลับมาใน callback
    state = f"{user_id}|{verifier}"
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        state=state,
        code_challenge=challenge,
        code_challenge_method="S256",
    )
    return auth_url


def exchange_code(code: str, state: str) -> tuple[str, dict]:
    parts = state.split("|", 1)
    user_id = parts[0]
    verifier = parts[1] if len(parts) > 1 else None
    flow = Flow.from_client_config(_CLIENT_CONFIG, scopes=SCOPES)
    flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
    flow.fetch_token(code=code, code_verifier=verifier)
    creds = flow.credentials
    return user_id, {
        "access_token": creds.token,
        "refresh_token": creds.refresh_token,
        "expiry": creds.expiry,
    }


def _build_service(access_token: str, refresh_token: str, expiry):
    creds = Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
    )
    # Force refresh ทุกครั้ง — ข้ามปัญหา timezone comparison ใน library
    creds.refresh(GoogleRequest())
    return build("calendar", "v3", credentials=creds)


def _color_id(subject_id: int | None) -> str:
    if subject_id is None:
        return "7"  # Peacock (ฟ้า) as default
    return str((subject_id % 11) + 1)


def create_events(access_token: str, refresh_token: str, expiry, task, slots) -> list[str]:
    service = _build_service(access_token, refresh_token, expiry)
    event_ids = []
    color_id = _color_id(task.subject_id)

    for slot in slots:
        start_hour = float(slot.start_hour)
        duration = float(slot.hours)
        end_hour = start_hour + duration

        def to_time(h: float) -> str:
            hh = int(h)
            mm = int(round((h - hh) * 60))
            return f"{hh:02d}:{mm:02d}:00"

        date_str = slot.slot_date.isoformat()
        event = {
            "summary": task.title or "Task",
            "colorId": color_id,
            "start": {"dateTime": f"{date_str}T{to_time(start_hour)}", "timeZone": "Asia/Bangkok"},
            "end": {"dateTime": f"{date_str}T{to_time(end_hour)}", "timeZone": "Asia/Bangkok"},
        }
        result = service.events().insert(calendarId="primary", body=event).execute()
        event_ids.append(result["id"])

    return event_ids


def delete_events(access_token: str, refresh_token: str, expiry, event_ids: list[str]):
    service = _build_service(access_token, refresh_token, expiry)
    for event_id in event_ids:
        try:
            service.events().delete(calendarId="primary", eventId=event_id).execute()
        except Exception:
            pass
