"""
System tools that Lee can use to interact with the local machine.
"""
import os
import json
import subprocess
import platform
import logging
from datetime import datetime, timezone

import psutil
import pyperclip
import mss
import base64

logger = logging.getLogger(__name__)


async def get_system_info() -> str:
    """Get system information including CPU, memory, disk, and battery."""
    info = {
        "platform": platform.platform(),
        "processor": platform.processor(),
        "cpu_count": psutil.cpu_count(),
        "cpu_usage_percent": psutil.cpu_percent(interval=0.5),
        "memory": {
            "total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "used_gb": round(psutil.virtual_memory().used / (1024**3), 2),
            "available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
            "percent_used": psutil.virtual_memory().percent,
        },
        "disk": {
            "total_gb": round(psutil.disk_usage("/").total / (1024**3), 2),
            "used_gb": round(psutil.disk_usage("/").used / (1024**3), 2),
            "free_gb": round(psutil.disk_usage("/").free / (1024**3), 2),
            "percent_used": psutil.disk_usage("/").percent,
        },
    }

    # Battery info (may not exist on desktops)
    battery = psutil.sensors_battery()
    if battery:
        info["battery"] = {
            "percent": battery.percent,
            "plugged_in": battery.power_plugged,
            "time_left_minutes": round(battery.secsleft / 60, 1) if battery.secsleft > 0 else "Charging/Full",
        }

    # Uptime
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.now() - boot_time
    hours, remainder = divmod(int(uptime.total_seconds()), 3600)
    minutes, _ = divmod(remainder, 60)
    info["uptime"] = f"{hours}h {minutes}m"

    return json.dumps(info, indent=2)


async def get_datetime() -> str:
    """Get the current date, time, and timezone (timezone-aware)."""
    now = datetime.now(tz=timezone.utc).astimezone()
    return json.dumps({
        "date": now.strftime("%A, %B %d, %Y"),
        "time": now.strftime("%I:%M:%S %p"),
        "timezone": now.strftime("%Z"),
        "utc_offset": now.strftime("%z"),
        "iso": now.isoformat(),
    })


async def open_application(app_name: str) -> str:
    """Open a macOS application by name."""
    try:
        subprocess.Popen(["open", "-a", app_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return json.dumps({"status": "success", "message": f"Opened {app_name}"})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


async def open_url(url: str) -> str:
    """Open a URL in the default web browser on macOS."""
    try:
        import urllib.parse
        parsed = urllib.parse.urlparse(url)
        # Only allow http and https — block file://, app://, custom schemes etc.
        if parsed.scheme not in ("http", "https"):
            if parsed.scheme == "":
                url = "https://" + url
                parsed = urllib.parse.urlparse(url)
            else:
                return json.dumps({"status": "error", "message": f"Blocked: URL scheme '{parsed.scheme}' is not allowed. Only http/https URLs are permitted."})
        # Ensure URL has a valid netloc (hostname)
        if not parsed.netloc:
            return json.dumps({"status": "error", "message": "Invalid URL: no hostname found."})
        subprocess.Popen(["open", url], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return json.dumps({"status": "success", "message": f"Opened URL: {url}"})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


# Expanded danger blocklist for run_shell_command
_DANGEROUS_PATTERNS = [
    "rm -rf /",
    "rm -rf ~",
    "rm -rf .",
    "mkfs",
    "dd if=",
    ":(){",
    "fork bomb",
    "sudo rm",
    "> /dev/sda",
    "> /dev/disk",
    "shutdown",
    "reboot",
    "halt",
    "pkill -9",
    "killall",
    "chmod -r 777 /",
    "chmod 777 /",
    "chmod -r 777 ~",
    ":() { :|:& };:",
]

# Regex patterns that catch obfuscated bypass attempts
import re as _re
_DANGEROUS_REGEX = [
    _re.compile(r"r[\\\s]*m\s+-[\w]*r[\w]*\s+-[\w]*f", _re.I),  # r m -rf variants with spaces
    _re.compile(r"sudo\s+", _re.I),                              # any sudo usage
    _re.compile(r":\s*\(\s*\)", _re.I),                         # fork bomb variants
    _re.compile(r"\$IFS"),                                       # $IFS shell bypass
    _re.compile(r"base64\s+-d"),                                 # base64 decode execution
    _re.compile(r"curl.+\|.+sh"),                                # curl | sh pipe download-exec
    _re.compile(r"wget.+\|.+sh"),                                # wget | sh pipe download-exec
    _re.compile(r"eval\s*\("),                                   # eval execution
    _re.compile(r"exec\s*\("),                                   # exec execution
]


async def run_shell_command(command: str) -> str:
    """Execute a shell command and return output."""
    cmd_lower = command.lower()
    # Plain string pattern check
    for pattern in _DANGEROUS_PATTERNS:
        if pattern in cmd_lower:
            return json.dumps({"status": "blocked", "message": f"Command blocked for safety: contains '{pattern}'"})
    # Regex-based obfuscation bypass detection
    for pattern in _DANGEROUS_REGEX:
        if pattern.search(command):
            return json.dumps({"status": "blocked", "message": f"Command blocked for safety: matches dangerous pattern '{pattern.pattern}'"})

    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=30
        )
        output = result.stdout if result.stdout else result.stderr
        # Truncate very long outputs
        if len(output) > 5000:
            output = output[:5000] + "\n... (output truncated)"
        return json.dumps({
            "status": "success",
            "return_code": result.returncode,
            "output": output.strip(),
        })
    except subprocess.TimeoutExpired:
        return json.dumps({"status": "error", "message": "Command timed out after 30 seconds"})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


async def read_file(file_path: str) -> str:
    """Read the contents of a file."""
    try:
        path = os.path.expanduser(file_path)
        if not os.path.exists(path):
            return json.dumps({"status": "error", "message": f"File not found: {path}"})

        size = os.path.getsize(path)
        if size > 1_000_000:  # 1MB limit
            return json.dumps({"status": "error", "message": f"File too large ({size} bytes). Max 1MB."})

        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        return json.dumps({
            "status": "success",
            "path": path,
            "size_bytes": size,
            "content": content,
        })
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


async def write_file(file_path: str, content: str) -> str:
    """Write content to a file."""
    try:
        path = os.path.expanduser(file_path)
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return json.dumps({
            "status": "success",
            "path": path,
            "bytes_written": len(content),
        })
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


async def append_file(file_path: str, content: str) -> str:
    """Append content to a file without overwriting it."""
    try:
        path = os.path.expanduser(file_path)
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(content)
        return json.dumps({
            "status": "success",
            "path": path,
            "bytes_appended": len(content),
        })
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


async def list_directory(path: str = "~") -> str:
    """List files and folders in a directory."""
    try:
        dir_path = os.path.expanduser(path)
        if not os.path.isdir(dir_path):
            return json.dumps({"status": "error", "message": f"Not a directory: {dir_path}"})

        entries = []
        for entry in sorted(os.listdir(dir_path)):
            full_path = os.path.join(dir_path, entry)
            try:
                stat = os.stat(full_path)
                entries.append({
                    "name": entry,
                    "type": "directory" if os.path.isdir(full_path) else "file",
                    "size_bytes": stat.st_size if os.path.isfile(full_path) else None,
                    "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                })
            except PermissionError:
                entries.append({"name": entry, "type": "unknown", "error": "permission denied"})

        # Limit to 100 entries
        total = len(entries)
        if total > 100:
            entries = entries[:100]

        return json.dumps({
            "status": "success",
            "path": dir_path,
            "total_entries": total,
            "entries": entries,
        })
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


async def get_clipboard() -> str:
    """Get clipboard contents."""
    try:
        content = pyperclip.paste()
        return json.dumps({
            "status": "success",
            "content": content[:5000] if content else "(clipboard is empty)",
        })
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


async def set_clipboard(text: str) -> str:
    """Set clipboard contents."""
    try:
        pyperclip.copy(text)
        return json.dumps({"status": "success", "message": "Text copied to clipboard", "length": len(text)})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


async def take_screenshot() -> str:
    """Take a screenshot and save it."""
    try:
        from config import DATA_DIR
        screenshot_path = os.path.join(DATA_DIR, f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        with mss.mss() as sct:
            sct.shot(output=screenshot_path)

        return json.dumps({
            "status": "success",
            "path": screenshot_path,
            "message": f"Screenshot saved to {screenshot_path}",
        })
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


async def web_search(query: str) -> str:
    """Search the web using Tavily or fallback to DuckDuckGo."""
    from config import TAVILY_API_KEY

    if TAVILY_API_KEY:
        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=TAVILY_API_KEY)
            results = client.search(query, max_results=5)
            return json.dumps({
                "status": "success",
                "query": query,
                "results": [
                    {"title": r.get("title", ""), "url": r.get("url", ""), "snippet": r.get("content", "")[:300]}
                    for r in results.get("results", [])
                ]
            })
        except Exception:
            pass  # Fall through to DuckDuckGo

    # Fallback: use jina.ai reader with DuckDuckGo
    try:
        import urllib.parse
        encoded = urllib.parse.quote_plus(query)
        result = subprocess.run(
            ["curl", "-s", f"https://r.jina.ai/https://lite.duckduckgo.com/lite/?q={encoded}"],
            capture_output=True, text=True, timeout=15
        )
        text = result.stdout.strip()[:3000]
        return json.dumps({
            "status": "success",
            "query": query,
            "source": "jina-duckduckgo",
            "raw_text": text,
        })
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


async def get_weather(location: str) -> str:
    """Get weather information using wttr.in."""
    try:
        import urllib.parse
        encoded = urllib.parse.quote(location)
        result = subprocess.run(
            ["curl", "-s", f"https://wttr.in/{encoded}?format=j1"],
            capture_output=True, text=True, timeout=10
        )
        data = json.loads(result.stdout)
        current = data.get("current_condition", [{}])[0]
        return json.dumps({
            "status": "success",
            "location": location,
            "temperature_c": current.get("temp_C"),
            "temperature_f": current.get("temp_F"),
            "feels_like_c": current.get("FeelsLikeC"),
            "humidity": current.get("humidity"),
            "description": current.get("weatherDesc", [{}])[0].get("value", ""),
            "wind_speed_kmph": current.get("windspeedKmph"),
            "wind_direction": current.get("winddir16Point"),
            "visibility_km": current.get("visibility"),
            "uv_index": current.get("uvIndex"),
        })
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


def _get_gmail_service(scopes=None):
    """Build a Gmail API service with auto token refresh."""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from config import DATA_DIR

    if scopes is None:
        scopes = [
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.send",
        ]

    token_path = os.path.join(DATA_DIR, "token.json")
    creds_path = os.path.join(DATA_DIR, "credentials.json")

    if not os.path.exists(token_path):
        raise FileNotFoundError("Not authenticated with Gmail. Please run scripts/auth_gmail.py first.")

    creds = Credentials.from_authorized_user_file(token_path, scopes)

    # Auto-refresh if expired
    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            # Atomic write: write to temp file then replace original to avoid corruption on crash
            import tempfile
            token_dir = os.path.dirname(token_path)
            with tempfile.NamedTemporaryFile("w", dir=token_dir, delete=False, suffix=".tmp") as tmp:
                tmp.write(creds.to_json())
                tmp_path = tmp.name
            os.replace(tmp_path, token_path)
            logger.info("Gmail token refreshed and saved atomically.")
        except Exception as e:
            raise RuntimeError(f"Gmail token refresh failed: {e}. Please re-run scripts/auth_gmail.py.")

    return build("gmail", "v1", credentials=creds)


async def get_unread_emails(limit: int = 5) -> str:
    """Fetch unread emails from the Gmail Inbox."""
    try:
        service = _get_gmail_service()

        results = service.users().messages().list(userId="me", q="is:unread in:inbox", maxResults=limit).execute()
        messages = results.get("messages", [])

        emails = []
        for msg in messages:
            msg_data = service.users().messages().get(userId="me", id=msg["id"], format="full").execute()
            headers = msg_data.get("payload", {}).get("headers", [])

            subject = sender = date = "Unknown"
            for header in headers:
                if header["name"] == "Subject":
                    subject = header["value"]
                elif header["name"] == "From":
                    sender = header["value"]
                elif header["name"] == "Date":
                    date = header["value"]

            emails.append({
                "subject": subject,
                "sender": sender,
                "received": date,
                "body_snippet": msg_data.get("snippet", ""),
            })

        return json.dumps({"status": "success", "count": len(emails), "emails": emails})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


async def send_email(to: str, subject: str, body: str) -> str:
    """Send an email using Gmail."""
    try:
        from email.message import EmailMessage

        service = _get_gmail_service()

        # Get the authenticated user's email address for the From header
        profile = service.users().getProfile(userId="me").execute()
        sender_email = profile.get("emailAddress", "me")

        message = EmailMessage()
        message.set_content(body)
        message["To"] = to
        message["From"] = sender_email
        message["Subject"] = subject

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        send_message = service.users().messages().send(
            userId="me", body={"raw": encoded_message}
        ).execute()

        return json.dumps({
            "status": "success",
            "message": f"Email successfully sent to {to}",
            "from": sender_email,
            "id": send_message.get("id"),
        })
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


def _applescript_escape(s: str) -> str:
    """Escape a string for safe embedding inside an AppleScript double-quoted string."""
    # Escape backslashes first, then double quotes to prevent injection
    return s.replace("\\", "\\\\").replace('"', '\\"')


async def set_reminder(title: str, notes: str = "", due_date: str = "") -> str:
    """Create a reminder in macOS Reminders app using AppleScript."""
    try:
        # Sanitize all user inputs to prevent AppleScript injection
        safe_title = _applescript_escape(title)
        safe_notes = _applescript_escape(notes)
        safe_due_date = _applescript_escape(due_date)

        # Build AppleScript
        notes_line = f'set the note of newReminder to "{safe_notes}"' if notes else ""
        date_line = ""
        if due_date:
            date_line = f'set the due date of newReminder to date "{safe_due_date}"'

        script = f"""
tell application "Reminders"
    set newReminder to make new reminder with properties {{name:"{safe_title}"}}
    {notes_line}
    {date_line}
end tell
"""
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            return json.dumps({"status": "error", "message": result.stderr.strip()})

        return json.dumps({
            "status": "success",
            "message": f"Reminder '{title}' created in macOS Reminders.",
            "due_date": due_date or "No due date set",
        })
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


async def remember(fact: str) -> str:
    """Save a fact to long-term memory."""
    from core.history import history
    success = history.add_memory(fact)
    if success:
        return json.dumps({"status": "success", "message": f"Memory saved: '{fact}'"})
    else:
        return json.dumps({"status": "warning", "message": f"I already remember this fact."})


async def forget(fact_id: int) -> str:
    """Delete a fact from long-term memory by ID."""
    from core.history import history
    success = history.remove_memory(fact_id)
    if success:
        return json.dumps({"status": "success", "message": f"Memory deleted: ID {fact_id}"})
    else:
        return json.dumps({"status": "error", "message": f"No memory found with ID {fact_id}."})


async def share_file_to_chat(file_path: str) -> str:
    """Share a local file directly into the user's chat."""
    try:
        path = os.path.expanduser(file_path)
        if not os.path.exists(path):
            return json.dumps({"status": "error", "message": f"File not found: {path}"})
        if not os.path.isfile(path):
            return json.dumps({"status": "error", "message": f"Path is a directory, not a file: {path}"})
        
        return json.dumps({
            "status": "file_sharing_queued", 
            "path": path, 
            "message": f"File {path} has been successfully queued to be sent to the user in the chat."
        })
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


# ── Tool Registry ─────────────────────────────────────────────────────────────
TOOL_FUNCTIONS = {
    "get_system_info": get_system_info,
    "get_datetime": get_datetime,
    "open_application": open_application,
    "open_url": open_url,
    "run_shell_command": run_shell_command,
    "read_file": read_file,
    "write_file": write_file,
    "append_file": append_file,
    "list_directory": list_directory,
    "remember": remember,
    "forget": forget,
    "get_clipboard": get_clipboard,
    "set_clipboard": set_clipboard,
    "take_screenshot": take_screenshot,
    "web_search": web_search,
    "get_weather": get_weather,
    "get_unread_emails": get_unread_emails,
    "send_email": send_email,
    "set_reminder": set_reminder,
    "share_file_to_chat": share_file_to_chat,
}
