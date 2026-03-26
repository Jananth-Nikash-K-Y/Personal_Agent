"""
Discord bot channel for Lee — owner-only, per-user conversation isolation.
"""
import logging
import discord
from core.engine import chat_simple
from config import DISCORD_TOKEN, DISCORD_OWNER_ID, AGENT_NAME

logger = logging.getLogger(__name__)

# Stores conversation IDs per Discord USER (not channel)
_user_conversations: dict[int, str] = {}

intents = discord.Intents.default()
intents.message_content = True
discord_client = discord.Client(intents=intents)


def _is_owner(user: discord.User | discord.Member) -> bool:
    """Check if the user is the authorized owner."""
    if DISCORD_OWNER_ID == 0:
        # If not configured, warn and deny all
        logger.warning("DISCORD_OWNER_ID is not set in .env — blocking all access for safety.")
        return False
    return user.id == DISCORD_OWNER_ID


@discord_client.event
async def on_ready():
    logger.info(f"Discord bot logged in as {discord_client.user}")
    print(f"  💬 Discord bot logged in as {discord_client.user}")


@discord_client.event
async def on_message(message: discord.Message):
    if message.author == discord_client.user:
        return

    # Only respond when mentioned or in a DM
    is_dm = isinstance(message.channel, discord.DMChannel)
    is_mentioned = discord_client.user in message.mentions
    if not is_dm and not is_mentioned:
        return

    # ── Security: owner-only ──────────────────────────────────────────────────
    if not _is_owner(message.author):
        await message.reply("⛔ Sorry, I'm a private assistant and only respond to my owner.")
        return

    user_id = message.author.id
    user_message = message.content.replace(f"<@{discord_client.user.id}>", "").strip()

    # ── Commands ──────────────────────────────────────────────────────────────
    if user_message.lower() in ("!new", "!reset"):
        _user_conversations.pop(user_id, None)
        await message.reply("🔄 Conversation reset! Starting fresh.")
        return

    if user_message.lower() == "!memory":
        from core.history import history
        try:
            memories = history.get_all_memories()
            if memories:
                lines = [f"**ID {m['id']}**: {m['fact']}" for m in memories]
                mem_str = "\n".join(lines)
                reply = f"🧠 **My long-term memory about you:**\n\n{mem_str}"
                
                # Truncate if too long for Discord
                if len(reply) > 1900:
                    reply = reply[:1900] + "\n... (truncated)"
                await message.reply(reply)
            else:
                await message.reply("🧠 My long-term memory is currently empty.")
        except Exception as e:
            logger.error(f"Failed to fetch memory: {e}")
            await message.reply("❌ Could not read memory database.")
        return

    if not user_message:
        await message.reply(f"Yes? How can I help you?")
        return

    conv_id = _user_conversations.get(user_id)

    async with message.channel.typing():
        try:
            reply, new_conv_id, files_to_send = await chat_simple(
                user_message=user_message,
                conversation_id=conv_id,
                channel="discord",
            )
            _user_conversations[user_id] = new_conv_id

            # Discord has a 2000 character limit — split if needed
            if len(reply) > 1900:
                chunks = [reply[i:i + 1900] for i in range(0, len(reply), 1900)]
                for chunk in chunks:
                    await message.channel.send(chunk)
            elif reply:
                await message.reply(reply)

            # Send requested files
            for file_path in files_to_send:
                try:
                    await message.channel.send(file=discord.File(file_path))
                except Exception as e:
                    await message.reply(f"❌ Failed to attach file {file_path}: {e}")

        except Exception as e:
            logger.error(f"Discord message handling error: {e}", exc_info=True)
            await message.reply(f"Sorry, I ran into an error: {str(e)}")


async def start_discord_bot():
    """Start the Discord bot as a background task."""
    if not DISCORD_TOKEN:
        print("  ⚠️  Discord token not found — Discord integration disabled")
        return
    if DISCORD_OWNER_ID == 0:
        print("  ⚠️  DISCORD_OWNER_ID not set in .env — bot will deny all users. Set it for access.")

    try:
        await discord_client.start(DISCORD_TOKEN)
    except Exception as e:
        logger.error(f"Discord bot failed to start: {e}", exc_info=True)
        print(f"  ⚠️  Discord bot failed to start: {e}")
