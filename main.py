"""
Lee — Personal AI Assistant
=============================
Unified entry point: starts the web dashboard + Discord bot in a single process.

Usage:
    python main.py
"""
import asyncio
from contextlib import asynccontextmanager
import uvicorn
from pyfiglet import Figlet

from config import AGENT_NAME, AGENT_VERSION, HOST, PORT
from channels.web import create_app
from channels.discord_bot import start_discord_bot
from channels.telegram_bot import start_telegram_bot


def print_banner():
    """Print a stylish startup banner."""
    fig = Figlet(font="slant")
    banner = fig.renderText(AGENT_NAME)
    print(f"\033[96m{banner}\033[0m")
    print(f"  \033[1m{AGENT_NAME} v{AGENT_VERSION} — Personal AI Assistant\033[0m")
    print(f"  ─────────────────────────────────────────")
    print(f"  🌐 Web Dashboard:  \033[4mhttp://localhost:{PORT}\033[0m")
    print(f"  ─────────────────────────────────────────\n")


@asynccontextmanager
async def lifespan(application):
    """Lifespan handler — start background services."""
    asyncio.create_task(start_discord_bot())
    asyncio.create_task(start_telegram_bot())
    yield


app = create_app(lifespan=lifespan)


if __name__ == "__main__":
    print_banner()
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=False,
        log_level="info",
    )