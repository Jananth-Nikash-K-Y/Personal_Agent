"""
SQLite-backed persistent conversation history for Lee.
"""
import sqlite3
import json
from datetime import datetime
from typing import Optional
from contextlib import contextmanager

from config import DB_PATH


class ChatHistory:
    """Manages persistent conversation storage using SQLite."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    @contextmanager
    def _db(self):
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self):
        """Create tables if they don't exist."""
        with self._db() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL DEFAULT 'New Conversation',
                    channel TEXT NOT NULL DEFAULT 'web',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tool_call_id TEXT,
                    tool_name TEXT,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_messages_conv_id ON messages(conversation_id);
                CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);
            """)

    def create_conversation(self, conv_id: str, title: str = "New Conversation", channel: str = "web") -> dict:
        """Create a new conversation."""
        now = datetime.now().isoformat()
        with self._db() as conn:
            conn.execute(
                "INSERT INTO conversations (id, title, channel, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (conv_id, title, channel, now, now)
            )
        return {"id": conv_id, "title": title, "channel": channel, "created_at": now, "updated_at": now}

    def get_conversation(self, conv_id: str) -> Optional[dict]:
        """Get a conversation by ID."""
        with self._db() as conn:
            row = conn.execute("SELECT * FROM conversations WHERE id = ?", (conv_id,)).fetchone()
            return dict(row) if row else None

    def list_conversations(self, channel: Optional[str] = None, limit: int = 50) -> list:
        """List conversations, optionally filtered by channel."""
        with self._db() as conn:
            if channel:
                rows = conn.execute(
                    "SELECT * FROM conversations WHERE channel = ? ORDER BY updated_at DESC LIMIT ?",
                    (channel, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM conversations ORDER BY updated_at DESC LIMIT ?",
                    (limit,)
                ).fetchall()
            return [dict(r) for r in rows]

    def update_conversation_title(self, conv_id: str, title: str):
        """Update a conversation's title."""
        with self._db() as conn:
            conn.execute(
                "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
                (title, datetime.now().isoformat(), conv_id)
            )

    def delete_conversation(self, conv_id: str):
        """Delete a conversation and all its messages."""
        with self._db() as conn:
            conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conv_id,))
            conn.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))

    def add_message(self, conv_id: str, msg_id: str, role: str, content: str,
                    tool_call_id: str = None, tool_name: str = None):
        """Add a message to a conversation."""
        now = datetime.now().isoformat()
        with self._db() as conn:
            conn.execute(
                """INSERT INTO messages (id, conversation_id, role, content, tool_call_id, tool_name, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (msg_id, conv_id, role, content, tool_call_id, tool_name, now)
            )
            conn.execute(
                "UPDATE conversations SET updated_at = ? WHERE id = ?",
                (now, conv_id)
            )

    def get_messages(self, conv_id: str, limit: int = 100) -> list:
        """Get messages for a conversation."""
        with self._db() as conn:
            rows = conn.execute(
                "SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC LIMIT ?",
                (conv_id, limit)
            ).fetchall()
            return [dict(r) for r in rows]

    def get_recent_messages_for_context(self, conv_id: str, limit: int = 40) -> list:
        """Get recent messages formatted for the LLM context window."""
        messages = self.get_messages(conv_id, limit=limit + 10)
        formatted = []
        for msg in messages:
            if msg["role"] == "assistant" and msg.get("tool_name") == "multiple_tool_calls":
                try:
                    data = json.loads(msg["content"])
                    entry = {
                        "role": "assistant",
                        "content": data.get("content", ""),
                        "tool_calls": data.get("tool_calls", [])
                    }
                    formatted.append(entry)
                except json.JSONDecodeError:
                    pass
            elif msg["role"] == "assistant" and msg.get("tool_name"):
                # Old format helper
                formatted.append({"role": "assistant", "content": msg["content"]})
            elif msg["role"] == "tool":
                if formatted and formatted[-1]["role"] == "assistant" and "tool_calls" in formatted[-1]:
                    formatted.append({
                        "role": "tool",
                        "content": msg["content"],
                        "tool_call_id": msg["tool_call_id"]
                    })
                else:
                    # Convert to system to preserve context without breaking schema
                    formatted.append({
                        "role": "system",
                        "content": f"[Result from past tool {msg.get('tool_name', 'unknown')}]: {msg['content']}"
                    })
            else:
                formatted.append({"role": msg["role"], "content": msg["content"]})

        while formatted and formatted[0]["role"] == "tool":
            formatted.pop(0)

        if len(formatted) > limit:
            slice_idx = len(formatted) - limit
            while slice_idx > 0 and formatted[slice_idx]["role"] == "tool":
                slice_idx -= 1
            formatted = formatted[slice_idx:]

        return formatted

    def search_messages(self, query: str, limit: int = 20) -> list:
        """Full-text search across all messages."""
        with self._db() as conn:
            rows = conn.execute(
                """SELECT m.*, c.title as conversation_title
                   FROM messages m
                   JOIN conversations c ON m.conversation_id = c.id
                   WHERE m.content LIKE ?
                   ORDER BY m.timestamp DESC LIMIT ?""",
                (f"%{query}%", limit)
            ).fetchall()
            return [dict(r) for r in rows]


# Singleton instance
history = ChatHistory()
