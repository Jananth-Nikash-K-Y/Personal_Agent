"""
System tools — hardware, shell, and OS interaction.
"""
import os
import json
import subprocess
import platform
import logging
import psutil
import pyperclip
import mss
from datetime import datetime, timezone

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

    battery = psutil.sensors_battery()
    if battery:
        info["battery"] = {
            "percent": battery.percent,
            "plugged_in": battery.power_plugged,
            "time_left_minutes": round(battery.secsleft / 60, 1) if battery.secsleft > 0 else "Charging/Full",
        }

    boot_time = datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.now() - boot_time
    hours, remainder = divmod(int(uptime.total_seconds()), 3600)
    minutes, _ = divmod(remainder, 60)
    info["uptime"] = f"{hours}h {minutes}m"

    return json.dumps(info, indent=2)

async def get_datetime() -> str:
    """Get the current date, time, and timezone."""
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
        if parsed.scheme not in ("http", "https"):
            if parsed.scheme == "":
                url = "https://" + url
                parsed = urllib.parse.urlparse(url)
            else:
                return json.dumps({"status": "error", "message": f"Blocked: URL scheme '{parsed.scheme}' is not allowed."})
        if not parsed.netloc:
            return json.dumps({"status": "error", "message": "Invalid URL: no hostname found."})
        subprocess.Popen(["open", url], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return json.dumps({"status": "success", "message": f"Opened URL: {url}"})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

_DANGEROUS_PATTERNS = [
    "rm -rf /", "rm -rf ~", "rm -rf .", "mkfs", "dd if=", ":(){", "fork bomb", "sudo rm",
    "> /dev/sda", "> /dev/disk", "shutdown", "reboot", "halt", "pkill -9", "killall",
    "chmod -r 777 /", "chmod 777 /", "chmod -r 777 ~", ":() { :|:& };:",
]

import re as _re
_DANGEROUS_REGEX = [
    _re.compile(r"r[\\\s]*m\s+-[\w]*r[\w]*\s+-[\w]*f", _re.I),
    _re.compile(r"sudo\s+", _re.I),
    _re.compile(r":\s*\(\s*\)", _re.I),
    _re.compile(r"\$IFS"),
    _re.compile(r"base64\s+-d"),
    _re.compile(r"curl.+\|.+sh"),
    _re.compile(r"wget.+\|.+sh"),
    _re.compile(r"eval\s*\("),
    _re.compile(r"exec\s*\("),
]

async def run_shell_command(command: str) -> str:
    """Execute a shell command and return output."""
    cmd_lower = command.lower()
    for pattern in _DANGEROUS_PATTERNS:
        if pattern in cmd_lower:
            return json.dumps({"status": "blocked", "message": f"Command blocked for safety: contains '{pattern}'"})
    for pattern in _DANGEROUS_REGEX:
        if pattern.search(command):
            return json.dumps({"status": "blocked", "message": f"Command blocked for safety: matches dangerous pattern '{pattern.pattern}'"})

    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        output = result.stdout if result.stdout else result.stderr
        if len(output) > 5000:
            output = output[:5000] + "\n... (output truncated)"
        return json.dumps({"status": "success", "return_code": result.returncode, "output": output.strip()})
    except subprocess.TimeoutExpired:
        return json.dumps({"status": "error", "message": "Command timed out after 30 seconds"})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

async def get_clipboard() -> str:
    """Get clipboard contents."""
    try:
        content = pyperclip.paste()
        return json.dumps({"status": "success", "content": content[:5000] if content else "(clipboard is empty)"})
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
        return json.dumps({"status": "success", "path": screenshot_path, "message": f"Screenshot saved to {screenshot_path}"})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})
