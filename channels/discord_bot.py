"""
Discord bot channel for Lee — extracted from original main.py.
"""
import discord
import asyncio
from core.engine import chat_simple
from config import DISCORD_TOKEN

# Stores conversation IDs per Discord channel
discord_conversations = {}

intents = discord.Intents.default()
intents.message_content = True
discord_client = discord.Client(intents=intents)


@discord_client.event
async def on_ready():
    print(f"  💬 Discord bot logged in as {discord_client.user}")


@discord_client.event
async def on_message(message):
    if message.author == discord_client.user:
        return

    # Only respond when mentioned or in a DM
    is_dm = isinstance(message.channel, discord.DMChannel)
    is_mentioned = discord_client.user in message.mentions
    if not is_dm and not is_mentioned:
        return

    channel_id = str(message.channel.id)
    user_message = message.content.replace(f"<@{discord_client.user.id}>", "").strip()

    if not user_message:
        await message.reply("Yes? How can I help you?")
        return

    # Get existing conversation ID for this channel, if any
    conv_id = discord_conversations.get(channel_id)

    async with message.channel.typing():
        try:
            reply, new_conv_id = await chat_simple(
                user_message=f"{message.author.display_name}: {user_message}",
                conversation_id=conv_id,
                channel="discord"
            )

            # Store conversation ID for continuity
            discord_conversations[channel_id] = new_conv_id

            # Discord has a 2000 character limit
            if len(reply) > 1900:
                chunks = [reply[i:i + 1900] for i in range(0, len(reply), 1900)]
                for chunk in chunks:
                    await message.channel.send(chunk)
            else:
                await message.reply(reply)

        except Exception as e:
            await message.reply(f"Sorry, I ran into an error: {str(e)}")


async def start_discord_bot():
    """Start the Discord bot as a background task."""
    if not DISCORD_TOKEN:
        print("  ⚠️  Discord token not found — Discord integration disabled")
        return

    try:
        await discord_client.start(DISCORD_TOKEN)
    except Exception as e:
        print(f"  ⚠️  Discord bot failed to start: {e}")
