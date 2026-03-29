"""
Telegram bot channel for Lee — owner-only, per-user conversation isolation.
"""
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from core.engine import chat
from config import TELEGRAM_TOKEN, TELEGRAM_OWNER_ID, AGENT_NAME

logger = logging.getLogger(__name__)

# Stores conversation IDs per Telegram USER ID
_user_conversations: dict[int, str] = {}
_application: Application = None


def _is_owner(update: Update) -> bool:
    """Check if the sender is the authorized owner."""
    if TELEGRAM_OWNER_ID == 0:
        logger.warning("TELEGRAM_OWNER_ID is not set in .env — blocking all access for safety.")
        return False
    return update.effective_user.id == TELEGRAM_OWNER_ID


async def _keep_typing(context, chat_id: int, stop_event: asyncio.Event):
    """Send typing action every 4 seconds until stop_event is set."""
    while not stop_event.is_set():
        try:
            await context.bot.send_chat_action(chat_id=chat_id, action="typing")
        except Exception:
            pass
        await asyncio.sleep(4)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    if not _is_owner(update):
        await update.message.reply_text("⛔ Sorry, I'm a private assistant and only respond to my owner.")
        return
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}! I'm {AGENT_NAME}, your personal AI assistant. How can I help you today?"
    )


async def cmd_new(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /new command — reset conversation."""
    if not _is_owner(update):
        await update.message.reply_text("⛔ Access denied.")
        return
    user_id = update.effective_user.id
    _user_conversations.pop(user_id, None)
    await update.message.reply_text("🔄 Conversation reset! Starting fresh.")


async def cmd_memory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /memory command — show persistent memory."""
    if not _is_owner(update):
        await update.message.reply_text("⛔ Access denied.")
        return
    
    from core.history import history
    try:
        memories = history.get_all_memories()
        if memories:
            lines = [f"• [ID: {m['id']}] {m['fact']}" for m in memories]
            mem_str = "\n".join(lines)
            
            reply = f"🧠 **My long-term memory about you:**\n\n{mem_str}"
            if len(reply) > 4000:
                reply = reply[:4000] + "\n... (truncated)"
            
            await update.message.reply_text(reply, parse_mode="Markdown")
        else:
            await update.message.reply_text("🧠 My long-term memory is currently empty.")
    except Exception as e:
        logger.error(f"Failed to fetch memory: {e}")
        await update.message.reply_text("❌ Could not read memory database.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming text messages."""
    # ── Security: owner-only ──────────────────────────────────────────────────
    if not _is_owner(update):
        await update.message.reply_text("⛔ Sorry, I'm a private assistant and only respond to my owner.")
        return

    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    user_message = update.message.text

    if not user_message:
        return

    conv_id = _user_conversations.get(user_id)

    # Start persistent typing indicator in background
    stop_typing = asyncio.Event()
    typing_task = asyncio.create_task(_keep_typing(context, chat_id, stop_typing))

    try:
        # Initial message to be edited as we stream
        sent_msg = await update.message.reply_text("Thinking...")
        
        full_reply = ""
        last_edit_time = 0
        files_to_send = []
        new_conv_id = conv_id

        async for event in chat(
            user_message=user_message,
            conversation_id=conv_id,
            channel="telegram",
        ):
            if event["type"] == "conversation_id":
                new_conv_id = event["content"]
            
            elif event["type"] == "content_chunk":
                full_reply += event["content"]
                
                # Update the message every 1.5 seconds to avoid Telegram rate limits
                import time
                current_time = time.time()
                if current_time - last_edit_time > 1.5 and full_reply.strip():
                    try:
                        # Append a blinking cursor or indicator if you want
                        display_content = full_reply + " ▌"
                        await context.bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=sent_msg.message_id,
                            text=display_content
                        )
                        last_edit_time = current_time
                    except Exception:
                        pass # Often just "message is not modified"

            elif event["type"] == "tool_call":
                # Show tool execution status
                try:
                    await context.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=sent_msg.message_id,
                        text=full_reply + f"\n\n🔧 *Executing {event['tool_name']}...*",
                        parse_mode="Markdown"
                    )
                except Exception: pass

            elif event["type"] == "message":
                # Final message event
                full_reply = event["content"]
            
            elif event["type"] == "tool_result" and event.get("tool_name") == "share_file_to_chat":
                import json
                try:
                    data = json.loads(event["content"])
                    if data.get("status") == "file_sharing_queued" and "path" in data:
                        files_to_send.append(data["path"])
                except Exception: pass

        _user_conversations[user_id] = new_conv_id

        # Final revision to remove the cursor and handle the full final text
        try:
            # Handle Telegram limit (4KB per msg)
            if len(full_reply) > 4000:
                # If too long, we might need a whole new message or just truncate
                final_text = full_reply[:3900] + "\n... (truncated)"
            else:
                final_text = full_reply

            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=sent_msg.message_id,
                text=final_text
            )
        except Exception as e:
            # If editing failed (e.g. msg too different/old), just send a final reply
            if not full_reply: 
                await context.bot.edit_message_text(chat_id=chat_id, message_id=sent_msg.message_id, text="I processed that for you.")
            else:
                logger.debug(f"Final edit failed: {e}")

        # Send requested files
        for file_path in files_to_send:
            try:
                with open(file_path, "rb") as f:
                    await update.message.reply_document(document=f)
            except Exception as e:
                await update.message.reply_text(f"❌ Failed to attach file {file_path}: {e}")

    except Exception as e:
        logger.error(f"Telegram message handling error: {e}", exc_info=True)
        await update.message.reply_text(f"Sorry, I ran into an error: {str(e)}")
    finally:
        stop_typing.set()
        typing_task.cancel()


async def notify_owner(message: str):
    """Send a proactive message to the authorized owner."""
    if _application and TELEGRAM_OWNER_ID != 0:
        try:
            await _application.bot.send_message(chat_id=TELEGRAM_OWNER_ID, text=message)
            return True
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")
    return False


async def start_telegram_bot():
    """Start the Telegram bot as a background task."""
    if not TELEGRAM_TOKEN:
        print("  ⚠️  Telegram token not found — Telegram integration disabled")
        return
    if TELEGRAM_OWNER_ID == 0:
        print("  ⚠️  TELEGRAM_OWNER_ID not set in .env — bot will deny all users. Set it for access.")

    try:
        print("  💬 Starting Telegram bot...")
        global _application
        _application = Application.builder().token(TELEGRAM_TOKEN).build()

        _application.add_handler(CommandHandler("start", cmd_start))
        _application.add_handler(CommandHandler("new", cmd_new))
        _application.add_handler(CommandHandler("memory", cmd_memory))
        _application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        await _application.initialize()
        await _application.start()
        await _application.updater.start_polling()

        print("  💬 Telegram bot is running.")

        # Keep the background task alive
        while True:
            await asyncio.sleep(3600)

    except Exception as e:
        logger.error(f"Telegram bot failed to start: {e}", exc_info=True)
        print(f"  ⚠️  Telegram bot failed to start: {e}")
