"""
Heartbeat system for Sentinal Lee — handles proactive notifications and autonomous checks.
"""
import asyncio
import logging
import json
import os
from datetime import datetime, timedelta

from core.tools import get_unread_emails, get_calendar_events
from channels.telegram_bot import notify_owner as notify_tg
from channels.discord_bot import notify_owner as notify_dc

logger = logging.getLogger(__name__)

HEARTBEAT_INTERVAL = 600  # 10 minutes

async def broadcast_notification(message: str):
    """Send a notification to the owner across all active channels."""
    tg_success = await notify_tg(message)
    dc_success = await notify_dc(message)
    if tg_success or dc_success:
        logger.info(f"Heartbeat notification sent: {message[:50]}...")
    else:
        logger.warning("Heartbeat notification failed to send to any channel.")

async def check_emails(only_important: bool = True):
    """Check for new unread emails and alert if found."""
    try:
        raw_result = await get_unread_emails(limit=5, only_important=only_important)
        result = json.loads(raw_result)
        if result.get("status") == "success" and result.get("count", 0) > 0:
            count = result["count"]
            emails = result["emails"]
            
            # Simple list of subjects
            subjects = "\n".join([f"• {e['subject']} (from {e['sender']})" for e in emails])
            header = "⭐ **Daily Important Emails Summary:**" if only_important else "✉️ **New Unread Emails:**"
            msg = f"{header}\n{subjects}"
            await broadcast_notification(msg)
    except Exception as e:
        logger.error(f"Heartbeat email check failed: {e}")

async def heartbeat_loop():
    """Main heartbeat loop."""
    from config import DATA_DIR
    last_check_file = os.path.join(DATA_DIR, "last_email_check.txt")
    
    print("  💓 Heartbeat system initialized (autonomous monitoring active).")
    await asyncio.sleep(15) # Wait for bots to connect
    
    while True:
        now = datetime.now()
        
        # 1. Daily Email Summary at 10:00 AM
        if now.hour == 10:
            last_date = ""
            if os.path.exists(last_check_file):
                with open(last_check_file, "r") as f:
                    last_date = f.read().strip()
            
            current_date = now.strftime("%Y-%m-%d")
            if last_date != current_date:
                logger.info("Heartbeat: Triggering daily 10 AM important email check.")
                await check_emails(only_important=True)
                with open(last_check_file, "w") as f:
                    f.write(current_date)
        
        # 2. Other periodic checks (e.g. calendar) can go here if periodic
        # await check_calendar() 
        
        await asyncio.sleep(HEARTBEAT_INTERVAL)

def start_heartbeat():
    """Run the heartbeat loop as an async task."""
    return asyncio.create_task(heartbeat_loop())
