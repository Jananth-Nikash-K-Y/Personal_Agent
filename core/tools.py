"""
System tools that Lee can use to interact with the local machine.
"""
import os
import json
import subprocess
import platform
from datetime import datetime

import psutil
import pyperclip
import mss
import base64


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
    """Get the current date, time, and timezone."""
    now = datetime.now()
    return json.dumps({
        "date": now.strftime("%A, %B %d, %Y"),
        "time": now.strftime("%I:%M:%S %p"),
        "timezone": datetime.now().astimezone().tzname(),
        "iso": now.isoformat(),
    })


async def open_application(app_name: str) -> str:
    """Open a macOS application by name."""
    try:
        subprocess.Popen(["open", "-a", app_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return json.dumps({"status": "success", "message": f"Opened {app_name}"})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


async def run_shell_command(command: str) -> str:
    """Execute a shell command and return output."""
    # Block dangerous patterns
    dangerous = ["rm -rf /", "mkfs", "dd if=", ":(){", "fork bomb"]
    for pattern in dangerous:
        if pattern in command.lower():
            return json.dumps({"status": "blocked", "message": f"Command blocked for safety: contains '{pattern}'"})

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
            "message": "Screenshot saved",
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
        except Exception as e:
            pass  # Fall through to DuckDuckGo

    # Fallback: use DuckDuckGo lite via curl
    try:
        import urllib.parse
        encoded = urllib.parse.quote_plus(query)
        result = subprocess.run(
            ["curl", "-s", f"https://lite.duckduckgo.com/lite/?q={encoded}"],
            capture_output=True, text=True, timeout=10
        )
        # Extract some text from the response
        import re
        text = re.sub(r"<[^>]+>", " ", result.stdout)
        text = re.sub(r"\s+", " ", text).strip()[:3000]
        return json.dumps({
            "status": "success",
            "query": query,
            "source": "duckduckgo",
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


# ── Tool Registry ─────────────────────────────────────────────────────────────
TOOL_FUNCTIONS = {
    "get_system_info": get_system_info,
    "get_datetime": get_datetime,
    "open_application": open_application,
    "run_shell_command": run_shell_command,
    "read_file": read_file,
    "write_file": write_file,
    "list_directory": list_directory,
    "get_clipboard": get_clipboard,
    "set_clipboard": set_clipboard,
    "take_screenshot": take_screenshot,
    "web_search": web_search,
    "get_weather": get_weather,
}
