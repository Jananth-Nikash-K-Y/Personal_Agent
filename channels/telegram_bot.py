"""
Telegram bot channel for Lee.
"""
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from core.engine import chat_simple
from config import TELEGRAM_TOKEN

# Stores conversation IDs per Telegram chat
telegram_conversations = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}! I'm Lee. How can I help you today?",
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming text messages and pass them to Sentinal_Lee's core engine."""
    chat_id = str(update.effective_chat.id)
    user_message = update.message.text
    user_name = update.effective_user.first_name or "User"

    if not user_message:
        return

    # Indicate typing while Lee thinks
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')

    # Get existing conversation ID for this chat, if any
    conv_id = telegram_conversations.get(chat_id)

    try:
        reply, new_conv_id = await chat_simple(
            user_message=f"{user_name}: {user_message}",
            conversation_id=conv_id,
            channel="telegram"
        )

        # Store conversation ID for continuity
        telegram_conversations[chat_id] = new_conv_id

        # Telegram has a 4096 character limit
        if len(reply) > 4000:
            chunks = [reply[i:i + 4000] for i in range(0, len(reply), 4000)]
            for chunk in chunks:
                await update.message.reply_text(chunk)
        else:
            await update.message.reply_text(reply)

    except Exception as e:
        await update.message.reply_text(f"Sorry, I ran into an error: {str(e)}")


async def start_telegram_bot():
    """Start the Telegram bot as a background task."""
    if not TELEGRAM_TOKEN:
        print("  ⚠️  Telegram token not found — Telegram integration disabled")
        return

    try:
        print("  💬 Starting Telegram bot...")
        application = Application.builder().token(TELEGRAM_TOKEN).build()

        # Command handlers
        application.add_handler(CommandHandler("start", start))

        # Message handlers
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        # Initialize and start the application
        await application.initialize()
        await application.start()
        # This will run update fetching in the background
        await application.updater.start_polling()
        
        print("  💬 Telegram bot is running.")
        
        # Keep the background task alive
        while True:
            await asyncio.sleep(3600)
    except Exception as e:
        print(f"  ⚠️  Telegram bot failed to start: {e}")
