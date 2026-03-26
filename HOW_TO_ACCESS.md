# How to Access Sentinal Lee

Sentinal Lee can be accessed and used through two distinct interfaces: the **Discord Bot** and the **Telegram Bot**. Both of these interfaces start automatically when you launch the main application.

Below are the dedicated steps to access and use each interface.

---

## ⚡ Quick Command Cheat Sheet

> Bookmark this. Everything you need in one place.

```bash
# ── Start ──────────────────────────────────────────────────────
launchctl load ~/Library/LaunchAgents/com.sentinallee.plist

# ── Stop ───────────────────────────────────────────────────────
launchctl unload ~/Library/LaunchAgents/com.sentinallee.plist

# ── Restart (after code update or crash) ───────────────────────
launchctl unload ~/Library/LaunchAgents/com.sentinallee.plist && launchctl load ~/Library/LaunchAgents/com.sentinallee.plist

# ── Check if running (shows PID and exit code) ─────────────────
launchctl list | grep sentinallee

# ── Watch live output log (Ctrl+C to exit) ─────────────────────
tail -f ~/Desktop/Personal_AI_Assistant/Sentinal_Lee/logs/lee.log

# ── Watch error log ────────────────────────────────────────────
tail -f ~/Desktop/Personal_AI_Assistant/Sentinal_Lee/logs/lee.error.log

# ── View last 50 lines of log ──────────────────────────────────
tail -n 50 ~/Desktop/Personal_AI_Assistant/Sentinal_Lee/logs/lee.log
```

---

## 🔍 Understanding `launchctl list` Output

When you run `launchctl list | grep sentinallee`, you'll see something like:

```
23049   0   com.sentinallee
```

| Column | Meaning |
|--------|---------|
| `23049` | **PID** — Lee is running with this process ID |
| `0` | **Exit code** — `0` means healthy; any other number means it crashed |
| `-` | **PID is `-`** — means the service is stopped or not yet loaded |

---

## 🔄 When to Restart

| Situation | Command |
|-----------|---------|
| Pulled new code from GitHub | `launchctl unload ... && launchctl load ...` |
| Added/changed `.env` variables | Restart required |
| Lee stopped responding | Check logs, then restart |
| After updating `requirements.txt` | Install deps first, then restart |

```bash
# Full update workflow after git pull
cd ~/Desktop/Personal_AI_Assistant/Sentinal_Lee
git pull
source agentEnv/bin/activate
pip install -r requirements.txt
launchctl unload ~/Library/LaunchAgents/com.sentinallee.plist && launchctl load ~/Library/LaunchAgents/com.sentinallee.plist
```

---

## 1. Accessing via Discord

The Discord integration allows you to chat with Lee exactly like you would text a friend. She can read DMs, be mentioned in server channels, and execute your system commands securely from your phone or another computer (as long as your main Mac is running the app).

### Setup and Connection:
1. Go to the [Discord Developer Portal](https://discord.com/developers/applications) and create a New Application.
2. In the **Bot** tab:
   - Click "Reset Token" to generate your bot's token.
   - Scroll down and **enable the "Message Content Intent"** toggle (required so she can read what you say).
3. Open your project's `.env` file (`~/Desktop/Personal_AI_Assistant/Sentinal_Lee/.env`) and add the token:
   ```env
   DISCORD_TOKEN=your_token_pasted_here
   ```
4. Invite the bot to your Discord server by going to the **OAuth2 > URL Generator** tab in the portal:
   - Check the `bot` scope.
   - Check the `Read Messages/View Channels`, `Send Messages`, and `Read Message History` permissions.
   - Visit the generated URL to invite Lee to your personal Discord server.

### How to Chat:
Once the service is running, the bot will come online in your Discord server.
- **Direct Message (DM):** Click on Lee's profile and send her a direct message. She will reply privately.
- **Server Channel:** Type `@Lee` in a server channel followed by your question (e.g. `@Lee take a screenshot`).

---

## 2. Accessing via Telegram

The Telegram integration allows for quick, reliable messaging with Lee on the go, making it perfect for rapid requests from your phone.

### Setup and Connection:
1. Open Telegram and search for **BotFather**.
2. Create a new bot using the `/newbot` command and follow the prompts to get your HTTP API Token.
3. Open your project's `.env` file (`~/Desktop/Personal_AI_Assistant/Sentinal_Lee/.env`) and add the token:
   ```env
   TELEGRAM_TOKEN=your_token_pasted_here
   ```
4. Update `TELEGRAM_OWNER_ID` in the `.env` file to your personal Telegram User ID (you can get this from `@userinfobot`).

### How to Chat:
1. Ensure the service is running (see Cheat Sheet above).
2. Open Telegram and search for the bot you just created.
3. Send it a message! Sentinal Lee will respond privately. Nobody else can interact with this bot.

### Telegram Commands:
| Command | What it does |
|---------|-------------|
| `/start` | Greet Lee and confirm she's online |
| `/new` | Reset the current conversation (fresh context) |
| `/memory` | Show everything Lee has remembered about you |

