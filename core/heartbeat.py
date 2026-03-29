"""
Heartbeat system for Sentinal Lee — handles proactive notifications and autonomous checks.
"""
import asyncio
import logging
import json
import os
from datetime import datetime, timedelta

from core.tools import get_unread_emails, get_calendar_events, get_top_news, get_weather, get_market_data
from channels.telegram_bot import notify_owner as notify_tg
from channels.discord_bot import notify_owner as notify_dc

logger = logging.getLogger(__name__)

HEARTBEAT_INTERVAL = 900  # 15 minutes


async def broadcast_notification(message: str):
    """Send a notification to the owner across all active channels."""
    tg_success = await notify_tg(message)
    dc_success = await notify_dc(message)
    
    # WhatsApp broadcast removed

    if tg_success or dc_success:
        logger.info(f"Heartbeat notification sent: {message[:50]}...")
    else:
        logger.warning("Heartbeat notification failed to send to any channel.")


async def generate_morning_briefing():
    """Phase 8: Aggregate data and synthesize a morning briefing using Gemini."""
    from core.engine import openai_client
    from config import MODEL_NAME
    
    logger.info("Generating morning briefing...")
    
    # 1. Gather Data Concurrently
    tasks = [
        get_calendar_events(days=1),
        get_weather("Chennai"), # Default location for the user
        get_top_news(),
        get_market_data(["RELIANCE.NS", "TCS.NS"])
    ]
    results = await asyncio.gather(*tasks)
    
    # 2. Get Tasks from DB
    from core.history import history
    todo = history.get_tasks(status="Pending")
    todo_str = "\n".join([f"- {t['title']} (Due: {t['due_date']})" for t in todo[:5]])
    
    # 3. Synthesize with Gemini
    prompt = f"""
    Synthesize the following information into a sharp, friendly, and motivational morning briefing 
    for a developer in Tamil Nadu. Keep it under 250 words.
    
    CALENDAR: {results[0]}
    WEATHER: {results[1]}
    NEWS: {results[2]}
    STOCKS: {results[3]}
    TODO LIST: {todo_str}
    
    Format nicely with emojis. Be the perfect secretary.
    """
    
    try:
        response = openai_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "system", "content": "You are Lee, a world-class personal secretary."},
                      {"role": "user", "content": prompt}]
        )
        briefing = response.choices[0].message.content
        await broadcast_notification(f"🌅 **Morning Briefing**\n\n{briefing}")
    except Exception as e:
        logger.error(f"Failed to generate briefing: {e}")


async def sync_to_obsidian():
    """Phase 10: Export SQLite tables to Markdown files in the Obsidian vault."""
    from config import OBSIDIAN_VAULT_PATH
    from core.history import history
    
    vault_path = os.path.expanduser(OBSIDIAN_VAULT_PATH)
    if not os.path.exists(vault_path):
        return

    try:
        # Export Tasks
        tasks = history.get_tasks()
        task_file = os.path.join(vault_path, "Lee_Tasks.md")
        with open(task_file, "w") as f:
            f.write("# ✅ Sentinal Lee Tasks\n\n")
            for t in tasks:
                status_icon = "x" if t['status'] == 'Completed' else " "
                f.write(f"- [{status_icon}] {t['title']} (Project: {t['project']}, Priority: {t['priority']})\n")
        
        # Export Memory
        memories = history.get_all_memories()
        mem_file = os.path.join(vault_path, "Lee_Memory.md")
        with open(mem_file, "w") as f:
            f.write("# 🧠 Sentinal Lee Long-Term Memory\n\n")
            for m in memories:
                f.write(f"- {m['fact']} (Saved: {m['created_at']})\n")
                
        logger.info("Obsidian sync completed.")
    except Exception as e:
        logger.error(f"Obsidian sync failed: {e}")


async def check_emails(only_important: bool = True):
    """Check for new unread emails and alert if found."""
    try:
        raw_result = await get_unread_emails(limit=5, only_important=only_important)
        result = json.loads(raw_result)
        if result.get("status") == "success" and result.get("count", 0) > 0:
            count = result["count"]
            emails = result["emails"]
            subjects = "\n".join([f"• {e['subject']} (from {e['sender']})" for e in emails])
            header = "⭐ **Daily Important Emails Summary:**" if only_important else "✉️ **New Unread Emails:**"
            await broadcast_notification(f"{header}\n{subjects}")
    except Exception as e:
        logger.error(f"Heartbeat email check failed: {e}")


async def monitor_web_changes():
    """Phase 11: Monitor specific URLs for changes."""
    from core.history import history
    import hashlib
    import httpx
    
    monitors = history.get_web_monitors()
    if not monitors:
        return

    logger.info(f"Checking {len(monitors)} web monitors...")
    async with httpx.AsyncClient(timeout=15) as client:
        for m in monitors:
            try:
                resp = await client.get(m['url'])
                if resp.status_code == 200:
                    current_hash = hashlib.md5(resp.text.encode()).hexdigest()
                    if m['last_hash'] and m['last_hash'] != current_hash:
                        await broadcast_notification(f"🔔 **Web Update:** '{m['label']}' has changed!\nLink: {m['url']}")
                    
                    # Update hash in DB
                    history.update_web_monitor_hash(m['id'], current_hash)
            except Exception as e:
                logger.error(f"Web monitor failed for {m['url']}: {e}")


async def run_weekly_reflection():
    """Phase 12: Weekly Sunday night reflection on productivity and goals."""
    from core.engine import openai_client
    from config import MODEL_NAME
    from core.history import history
    
    logger.info("Running weekly reflection...")
    
    # 1. Get stats
    tasks = history.get_tasks(status="Completed")
    expenses = history.get_expenses(limit=50) # Last 50 items
    
    # 2. Synthesize
    prompt = f"""
    Review the following weekly activity and provide a 'Sunday Night Reflection'. 
    Acknowledge wins, identify bottlenecks, and suggest 3 focus areas for next week.
    
    COMPLETED TASKS: {len(tasks)} items
    RECENT EXPENSES: {expenses[:10]}
    
    Format: 'Executive Summary', 'Financial Health', 'Goal Alignment'.
    """
    
    try:
        response = openai_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "system", "content": "You are Lee, an executive coach and secretary."},
                      {"role": "user", "content": prompt}]
        )
        reflection = response.choices[0].message.content
        history.add_reflection("Weekly", reflection)
        await broadcast_notification(f"📔 **Weekly Reflection**\n\n{reflection}")
    except Exception as e:
        logger.error(f"Weekly reflection failed: {e}")


async def heartbeat_loop():
    """Main heartbeat loop."""
    from config import DATA_DIR
    state_file = os.path.join(DATA_DIR, "heartbeat_state.json")
    
    print("  💓 Heartbeat system initialized (autonomous monitoring active).")
    await asyncio.sleep(20) # Wait for bots to connect
    
    while True:
        now = datetime.now()
        current_date = now.strftime("%Y-%m-%d")
        
        # Load state
        state = {}
        if os.path.exists(state_file):
            with open(state_file, "r") as f:
                state = json.load(f)
        
        # 1. 07:30 AM Morning Briefing
        if now.hour == 7 and now.minute >= 30:
            if state.get("last_briefing") != current_date:
                await generate_morning_briefing()
                state["last_briefing"] = current_date

        # 2. 10:00 AM Email Check
        if now.hour == 10:
            if state.get("last_email_check") != current_date:
                from core.heartbeat import check_emails
                await check_emails(only_important=True)
                state["last_email_check"] = current_date

        # 3. Hourly Obsidian Sync
        if state.get("last_sync_hour") != now.hour:
            await sync_to_obsidian()
            state["last_sync_hour"] = now.hour

        # 4. Phase 11: Web Monitoring (Every interval / ~15 mins)
        await monitor_web_changes()

        # 5. Phase 12: Weekly Reflection (Sundays at 9:00 PM)
        if now.weekday() == 6 and now.hour == 21:
            if state.get("last_reflection") != current_date:
                await run_weekly_reflection()
                state["last_reflection"] = current_date

        # Save state
        with open(state_file, "w") as f:
            json.dump(state, f)
        
        await asyncio.sleep(HEARTBEAT_INTERVAL)


def start_heartbeat():
    """Run the heartbeat loop as an async task."""
    return asyncio.create_task(heartbeat_loop())
