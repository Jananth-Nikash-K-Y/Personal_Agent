"""
Communication tools — Gmail, Google Calendar, and Contacts CRM.
"""
import os
import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

def _get_gmail_service(scopes=None):
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from config import DATA_DIR
    if scopes is None:
        scopes = ["https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/gmail.send"]
    token_path = os.path.join(DATA_DIR, "token.json")
    if not os.path.exists(token_path):
        raise FileNotFoundError("Not authenticated with Gmail. Run scripts/auth_gmail.py first.")
    creds = Credentials.from_authorized_user_file(token_path, scopes)
    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            with open(token_path, "w") as f: f.write(creds.to_json())
        except Exception as e: raise RuntimeError(f"Gmail token refresh failed: {e}")
    return build("gmail", "v1", credentials=creds)

async def get_unread_emails(limit: int = 5, only_important: bool = False) -> str:
    """Fetch unread emails from the Gmail Inbox."""
    try:
        service = _get_gmail_service()
        query = "is:unread in:inbox"
        if only_important: query += " label:important"
        results = service.users().messages().list(userId="me", q=query, maxResults=limit).execute()
        messages = results.get("messages", [])
        emails = []
        for msg in messages:
            msg_data = service.users().messages().get(userId="me", id=msg["id"], format="full").execute()
            headers = msg_data.get("payload", {}).get("headers", [])
            subject = sender = date = "Unknown"
            for h in headers:
                if h["name"] == "Subject": subject = h["value"]
                elif h["name"] == "From": sender = h["value"]
                elif h["name"] == "Date": date = h["value"]
            emails.append({"subject": subject, "sender": sender, "received": date, "body_snippet": msg_data.get("snippet", "")})
        return json.dumps({"status": "success", "count": len(emails), "emails": emails})
    except Exception as e: return json.dumps({"status": "error", "message": str(e)})

async def send_email(to: str, subject: str, body: str, attachment_path: str = "") -> str:
    """Send an email using Gmail."""
    try:
        import email.mime.multipart
        import email.mime.text
        import email.mime.base
        import email.encoders
        import base64
        service = _get_gmail_service()
        profile = service.users().getProfile(userId="me").execute()
        sender_email = profile.get("emailAddress", "me")
        message = email.mime.multipart.MIMEMultipart()
        message["To"] = to
        message["From"] = sender_email
        message["Subject"] = subject
        message.attach(email.mime.text.MIMEText(body, "plain"))
        if attachment_path:
            path = os.path.expanduser(attachment_path)
            if os.path.isfile(path):
                with open(path, "rb") as f:
                    part = email.mime.base.MIMEBase("application", "octet-stream")
                    part.set_payload(f.read())
                    email.encoders.encode_base64(part)
                    part.add_header("Content-Disposition", f'attachment; filename="{os.path.basename(path)}"')
                    message.attach(part)
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        service.users().messages().send(userId="me", body={"raw": raw}).execute()
        return json.dumps({"status": "success", "to": to, "subject": subject})
    except Exception as e: return json.dumps({"status": "error", "message": str(e)})

def _get_calendar_service():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from config import DATA_DIR
    token_path = os.path.join(DATA_DIR, "token_calendar.json")
    if not os.path.exists(token_path):
        token_path = os.path.join(DATA_DIR, "token.json") # Fallback to Gmail token if same scopes
    if not os.path.exists(token_path):
        raise FileNotFoundError("Calendar authentication missing.")
    creds = Credentials.from_authorized_user_file(token_path, ["https://www.googleapis.com/auth/calendar"])
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build("calendar", "v3", credentials=creds)

async def get_calendar_events(limit: int = 10) -> str:
    """Get upcoming calendar events."""
    try:
        service = _get_calendar_service()
        now = datetime.utcnow().isoformat() + "Z"
        events_result = service.events().list(calendarId="primary", timeMin=now, maxResults=limit, singleEvents=True, orderBy="startTime").execute()
        events = events_result.get("items", [])
        formatted = [{"summary": e.get("summary"), "start": e.get("start", {}).get("dateTime", e.get("start", {}).get("date")), "location": e.get("location")} for e in events]
        return json.dumps({"status": "success", "events": formatted})
    except Exception as e: return json.dumps({"status": "error", "message": str(e)})

async def add_calendar_event(summary: str, start_time: str, end_time: str, location: str = "", description: str = "") -> str:
    """Add an event to Google Calendar."""
    try:
        service = _get_calendar_service()
        event = {"summary": summary, "location": location, "description": description, "start": {"dateTime": start_time, "timeZone": "Asia/Kolkata"}, "end": {"dateTime": end_time, "timeZone": "Asia/Kolkata"}}
        event = service.events().insert(calendarId="primary", body=event).execute()
        return json.dumps({"status": "success", "event_id": event.get("id"), "url": event.get("htmlLink")})
    except Exception as e: return json.dumps({"status": "error", "message": str(e)})

async def set_reminder(title: str, due_date: str) -> str:
    """Set a reminder as a high-priority task."""
    from core.history import history
    try:
        task_id = history.add_task(title, description="Auto-generated reminder", priority="High", due_date=due_date)
        return json.dumps({"status": "success", "message": f"Reminder set: {title} on {due_date}", "task_id": task_id})
    except Exception as e: return json.dumps({"status": "error", "message": str(e)})

async def add_contact(name: str, email: str = None, phone: str = None, relationship: str = "Friend", notes: str = None) -> str:
    """Add a contact to the internal CRM."""
    from core.history import history
    try:
        contact_id = history.add_contact(name, email=email, phone=phone, relationship=relationship, notes=notes)
        return json.dumps({"status": "success", "message": f"Contact added: {name} (ID {contact_id})"})
    except Exception as e: return json.dumps({"status": "error", "message": str(e)})

async def search_contacts(query: str) -> str:
    """Search for contacts by name or tags."""
    from core.history import history
    try:
        results = history.search_contacts(query)
        return json.dumps({"status": "success", "count": len(results), "contacts": results})
    except Exception as e: return json.dumps({"status": "error", "message": str(e)})
