"""
Telegram bot channel for Lee — owner-only, per-user conversation isolation.
"""
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from core.engine import chat_simple
from config import TELEGRAM_TOKEN, TELEGRAM_OWNER_ID, AGENT_NAME

logger = logging.getLogger(__name__)

# Stores conversation IDs per Telegram USER ID
_user_conversations: dict[int, str] = {}


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
        reply, new_conv_id, files_to_send = await chat_simple(
            user_message=user_message,
            conversation_id=conv_id,
            channel="telegram",
        )
        _user_conversations[user_id] = new_conv_id

        # Telegram has a 4096 character limit — split if needed
        if len(reply) > 4000:
            chunks = [reply[i:i + 4000] for i in range(0, len(reply), 4000)]
            for chunk in chunks:
                await update.message.reply_text(chunk)
        elif reply:
            await update.message.reply_text(reply)

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


async def start_telegram_bot():
    """Start the Telegram bot as a background task."""
    if not TELEGRAM_TOKEN:
        print("  ⚠️  Telegram token not found — Telegram integration disabled")
        return
    if TELEGRAM_OWNER_ID == 0:
        print("  ⚠️  TELEGRAM_OWNER_ID not set in .env — bot will deny all users. Set it for access.")

    try:
        print("  💬 Starting Telegram bot...")
        application = Application.builder().token(TELEGRAM_TOKEN).build()

        application.add_handler(CommandHandler("start", cmd_start))
        application.add_handler(CommandHandler("new", cmd_new))
        application.add_handler(CommandHandler("memory", cmd_memory))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        await application.initialize()
        await application.start()
        await application.updater.start_polling()

        print("  💬 Telegram bot is running.")

        # Keep the background task alive
        while True:
            await asyncio.sleep(3600)

    except Exception as e:
        logger.error(f"Telegram bot failed to start: {e}", exc_info=True)
        print(f"  ⚠️  Telegram bot failed to start: {e}")
