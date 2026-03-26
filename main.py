"""
Lee — Personal AI Assistant
=============================
Unified entry point: starts the Discord and Telegram bots.

Usage:
    python main.py
"""
import asyncio
from pyfiglet import Figlet

from config import AGENT_NAME, AGENT_VERSION
from channels.discord_bot import start_discord_bot
from channels.telegram_bot import start_telegram_bot


def print_banner():
    """Print a stylish startup banner."""
    fig = Figlet(font="slant")
    banner = fig.renderText(AGENT_NAME)
    print(f"\033[96m{banner}\033[0m")
    print(f"  \033[1m{AGENT_NAME} v{AGENT_VERSION} — Personal AI Assistant\033[0m")
    print(f"  ─────────────────────────────────────────")
    print(f"  🤖 Running in Headless Mode (Bots Only)")
    print(f"  ─────────────────────────────────────────\n")


async def main():
    print_banner()
    
    # Start bot tasks concurrently
    discord_task = asyncio.create_task(start_discord_bot())
    telegram_task = asyncio.create_task(start_telegram_bot())
    
    # Wait for tasks to complete
    await asyncio.gather(discord_task, telegram_task)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n  Shutting down...")