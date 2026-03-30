"""
File tools — CRUD operations and sharing.
"""
import os
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

async def read_file(file_path: str) -> str:
    """Read the contents of a file."""
    try:
        path = os.path.expanduser(file_path)
        if not os.path.exists(path):
            return json.dumps({"status": "error", "message": f"File not found: {path}"})
        size = os.path.getsize(path)
        if size > 1_000_000:
            return json.dumps({"status": "error", "message": f"File too large ({size} bytes). Max 1MB."})
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return json.dumps({"status": "success", "path": path, "size_bytes": size, "content": content})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

async def write_file(file_path: str, content: str) -> str:
    """Write content to a file."""
    try:
        path = os.path.expanduser(file_path)
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return json.dumps({"status": "success", "path": path, "bytes_written": len(content)})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

async def append_file(file_path: str, content: str) -> str:
    """Append content to a file."""
    try:
        path = os.path.expanduser(file_path)
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(content)
        return json.dumps({"status": "success", "path": path, "bytes_appended": len(content)})
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
        if len(entries) > 100: entries = entries[:100]
        return json.dumps({"status": "success", "path": dir_path, "total_entries": len(entries), "entries": entries})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

async def share_file_to_chat(file_path: str) -> str:
    """Share a local file directly into the user's chat."""
    try:
        path = os.path.expanduser(file_path)
        if not os.path.exists(path):
            return json.dumps({"status": "error", "message": f"File not found: {path}"})
        if not os.path.isfile(path):
            return json.dumps({"status": "error", "message": f"Path is a directory: {path}"})
        return json.dumps({"status": "file_sharing_queued", "path": path, "message": f"File {path} queued for sharing."})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})
