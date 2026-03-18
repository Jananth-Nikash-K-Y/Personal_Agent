"""
Web channel for Lee — FastAPI routes + WebSocket for real-time chat.
"""
import json
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from config import STATIC_DIR
from core.engine import chat
from core.history import history


def create_app(lifespan=None) -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(title="Lee — Personal AI Assistant", version="2.0.0", lifespan=lifespan)

    # ── Static files ──────────────────────────────────────────────────────
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    # ── Serve the dashboard ───────────────────────────────────────────────
    @app.get("/")
    async def serve_dashboard():
        return FileResponse(f"{STATIC_DIR}/index.html")

    # ── REST API ──────────────────────────────────────────────────────────
    @app.get("/api/conversations")
    async def list_conversations(channel: str = None):
        convs = history.list_conversations(channel=channel)
        return JSONResponse(content=convs)

    @app.get("/api/conversations/{conv_id}")
    async def get_conversation(conv_id: str):
        conv = history.get_conversation(conv_id)
        if not conv:
            return JSONResponse(content={"error": "Not found"}, status_code=404)
        messages = history.get_messages(conv_id)
        return JSONResponse(content={"conversation": conv, "messages": messages})

    @app.delete("/api/conversations/{conv_id}")
    async def delete_conversation(conv_id: str):
        history.delete_conversation(conv_id)
        return JSONResponse(content={"status": "deleted"})

    @app.get("/api/tools")
    async def list_tools():
        from config import TOOL_DEFINITIONS
        tools = [
            {"name": t["function"]["name"], "description": t["function"]["description"]}
            for t in TOOL_DEFINITIONS
        ]
        return JSONResponse(content=tools)

    # ── WebSocket for real-time chat ──────────────────────────────────────
    @app.websocket("/ws")
    async def websocket_chat(ws: WebSocket):
        await ws.accept()
        try:
            while True:
                data = await ws.receive_text()
                payload = json.loads(data)
                user_message = payload.get("message", "").strip()
                conversation_id = payload.get("conversation_id")

                if not user_message:
                    await ws.send_json({"type": "error", "content": "Empty message"})
                    continue

                # Stream events from the engine
                async for event in chat(user_message, conversation_id, channel="web"):
                    await ws.send_json(event)

        except WebSocketDisconnect:
            pass
        except Exception as e:
            try:
                await ws.send_json({"type": "error", "content": str(e)})
            except:
                pass

    return app
