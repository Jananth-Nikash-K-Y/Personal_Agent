"""
Pydantic data models for Lee.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid


class Message(BaseModel):
    """A single chat message."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: str  # "user", "assistant", "system", "tool"
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    tool_call_id: Optional[str] = None
    tool_name: Optional[str] = None
    conversation_id: Optional[str] = None


class Conversation(BaseModel):
    """A conversation thread."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = "New Conversation"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    channel: str = "web"  # "web", "discord", "cli"


class ToolCall(BaseModel):
    """Represents a tool call made by the AI."""
    id: str
    name: str
    arguments: dict
    result: Optional[str] = None


class ChatRequest(BaseModel):
    """WebSocket chat request."""
    message: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    """WebSocket chat response."""
    type: str  # "message", "tool_call", "tool_result", "error", "stream"
    content: str = ""
    conversation_id: str = ""
    message_id: str = ""
    tool_name: str = ""
    tool_args: dict = Field(default_factory=dict)
