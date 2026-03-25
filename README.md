<div align="center">

# 🤖 Lee — Personal AI Assistant

**A powerful, locally-hosted AI assistant that runs 24/7 on your Mac**

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Discord](https://img.shields.io/badge/Discord_Bot-5865F2?logo=discord&logoColor=white)](https://discord.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

*Warm, witty, and competent — Lee is not just an assistant, she's your trusted companion.*

</div>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🌐 **Web Dashboard** | Beautiful real-time chat interface with markdown support |
| 💬 **Discord Integration** | Chat with Lee via Discord DMs or by mentioning her |
| 🔧 **System Tools** | Control your Mac — open apps, run commands, manage files |
| 🔍 **Web Search** | Search the web via Tavily or DuckDuckGo fallback |
| 🌤️ **Weather** | Get real-time weather for any location |
| 📸 **Screenshots** | Capture your screen on demand |
| 📋 **Clipboard** | Read and write clipboard contents |
| 💾 **Chat History** | Persistent SQLite-backed conversation history |
| ⚡ **24/7 Service** | Runs as a macOS `launchd` service with auto-restart |

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────┐
│                   Lee v2.0.0                    │
├──────────────┬───────────────────────────────────┤
│  Channels    │        Core Engine                │
│  ┌────────┐  │  ┌──────────┐  ┌──────────────┐  │
│  │  Web   │──│──│  LLM     │  │  Tool        │  │
│  │  (WS)  │  │  │  Engine  │──│  Executor    │  │
│  ├────────┤  │  │  (Groq)  │  │              │  │
│  │Discord │──│──│          │  │  12 built-in │  │
│  │  Bot   │  │  └──────────┘  │  tools       │  │
│  └────────┘  │  ┌──────────┐  └──────────────┘  │
│              │  │ History  │                     │
│              │  │ (SQLite) │                     │
│              │  └──────────┘                     │
├──────────────┴───────────────────────────────────┤
│          macOS launchd service layer             │
│     (auto-start on login, auto-restart)          │
└──────────────────────────────────────────────────┘
```

---

## 📋 Prerequisites

- **macOS** 12+ (Monterey or later recommended)
- **Python** 3.11 or later
- **Groq API Key** — [Get one free](https://console.groq.com/keys)
- **Discord Bot Token** *(optional)* — [Create a bot](https://discord.com/developers/applications)
- **Tavily API Key** *(optional)* — [Sign up](https://tavily.com/) for web search
- **Gmail API Credentials** *(optional)* — Save `credentials.json` to the `data/` folder for email access

---

## 🚀 Quick Start

### 1. Clone & Setup

```bash
# Navigate to the project
cd ~/Desktop/Personal_AI_Assistant

# Create a virtual environment (if not already done)
python3 -m venv agentEnv

# Activate it
source agentEnv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the project root:

```env
# Required
GROQ_API_KEY=your_groq_api_key_here

# Optional — for Discord integration
DISCORD_TOKEN=your_discord_bot_token_here

# Optional — for web search (falls back to DuckDuckGo)
TAVILY_API_KEY=your_tavily_api_key_here
```

### 3. Setup Gmail (Optional)

If you want Lee to read and send emails:
1. Save your `credentials.json` from Google Cloud Console into the `data/` directory.
2. Run `python scripts/auth_gmail.py` and grant permissions in your browser.
3. This will generate `data/token.json` for future access.

### 4. Run Lee

#### Option A: Manual (Foreground)

```bash
python main.py
```

#### Option B: Background (via Management Script)

```bash
bash scripts/Lee.sh start
```

#### Option C: 24/7 Service (Recommended ⭐)

```bash
bash scripts/install_service.sh
```

This will:
- ✅ Install Lee as a macOS `launchd` service
- ✅ Start automatically on every login
- ✅ Auto-restart if Lee crashes
- ✅ Run silently in the background

Then open **[http://localhost:8000](http://localhost:8000)** 🎉

---

## 🔄 Service Management

Lee can be run in three ways: **manually** in the foreground, as a **background process**, or as a persistent **24/7 launchd service**. Below is everything you need to manage it.

---

### 📌 Quick Reference

| What you want to do | Command |
|----------------------|---------|
| **Start** Lee in the foreground | `python main.py` |
| **Start** Lee in the background | `bash scripts/Lee.sh start` |
| **Stop** Lee | `bash scripts/Lee.sh stop` |
| **Restart** Lee | `bash scripts/Lee.sh restart` |
| **Check** if Lee is running | `bash scripts/Lee.sh status` |
| **View live logs** | `bash scripts/Lee.sh logs` |
| **Install** as 24/7 service | `bash scripts/install_service.sh` |
| **Uninstall** the 24/7 service | `bash scripts/install_service.sh --uninstall` |

---

### ▶️ Starting Lee

#### Method 1: Manual (Foreground)

Run Lee directly in your terminal. Logs appear in real-time. Press `Ctrl+C` to stop.

```bash
# Make sure the virtualenv is activated
source agentEnv/bin/activate

# Start Lee
python main.py
```

You'll see the startup banner:
```
    __
   / /   ___  ___
  / /   / _ \/ _ \
 / /___/  __/  __/
/_____/\___/\___/

  Lee v2.0.0 — Personal AI Assistant
  ─────────────────────────────────────────
  🌐 Web Dashboard:  http://localhost:8000
  ─────────────────────────────────────────
```

#### Method 2: Background Process

Start Lee in the background using the management script. It will keep running even after you close the terminal.

```bash
bash scripts/Lee.sh start
```

Expected output:
```
  ╔════════════════════════════════════╗
  ║     🤖 Lee Service Manager        ║
  ╚════════════════════════════════════╝

  Starting Lee...
  ✓ Lee started successfully (PID: 12345)
    Dashboard: http://localhost:8000
    Logs:      data/Lee_stdout.log
```

#### Method 3: 24/7 launchd Service (Recommended ⭐)

This is the best option if you want Lee **always running**. It will:
- ✅ Start automatically when you log in
- ✅ Auto-restart if it crashes
- ✅ Run silently in the background with zero effort

```bash
bash scripts/install_service.sh
```

Expected output:
```
  ╔════════════════════════════════════╗
  ║   🤖 Lee Service Installer        ║
  ╚════════════════════════════════════╝

  Generating launchd configuration...
  ✓ Plist created at: ~/Library/LaunchAgents/com.Lee.assistant.plist
  Loading service...
  ✓ Service loaded successfully!
  ✓ Lee is running!

  ═══════════════════════════════════════
    ✅ Lee is now a 24/7 service!
  ═══════════════════════════════════════

  Dashboard:    http://localhost:8000
  Auto-start:   Enabled (runs on login)
  Auto-restart: Enabled (restarts on crash)
  Logs:         data/Lee_stdout.log
  Manage:       bash scripts/Lee.sh {start|stop|restart|status|logs}
  Uninstall:    bash scripts/install_service.sh --uninstall
```

---

### ⏹️ Stopping Lee

```bash
# Stop Lee (works for both background and launchd modes)
bash scripts/Lee.sh stop
```

Expected output:
```
  Stopping Lee (PID: 12345)...
  ✓ Lee stopped
```

> **Note:** If Lee is running as a launchd service, `launchd` may auto-restart it after you stop it (that's the whole point of 24/7 mode). To stop it permanently, uninstall the service first — see below.

---

### 🔁 Restarting Lee

Useful after changing `config.py`, `.env`, or any source code:

```bash
bash scripts/Lee.sh restart
```

This gracefully stops and then starts Lee again.

---

### 📊 Checking Status

```bash
bash scripts/Lee.sh status
```

When Lee is **running**:
```
  ● Lee is RUNNING
    PID:       12345
    Dashboard: http://localhost:8000
    Started:   Tue Mar 18 10:00:00 2026
    Memory:    85.3 MB
    CPU:       0.2%
    Service:   launchd managed (auto-start enabled)
```

When Lee is **stopped**:
```
  ● Lee is STOPPED
```

---

### 📜 Viewing Logs

View live logs in real-time (press `Ctrl+C` to exit):

```bash
bash scripts/Lee.sh logs
```

You can also read log files directly:

```bash
# Standard output log
cat data/Lee_stdout.log

# Error log
cat data/Lee_stderr.log

# Follow logs in real-time
tail -f data/Lee_stdout.log
```

---

### 🗑️ Uninstalling the 24/7 Service

If you no longer want Lee to auto-start:

```bash
bash scripts/install_service.sh --uninstall
```

Expected output:
```
  Uninstalling Lee service...
  ✓ Service unloaded
  ✓ Plist removed from ~/Library/LaunchAgents/com.Lee.assistant.plist
  ✓ Lee process stopped

  ✓ Lee service uninstalled.
    You can still run Lee manually with: python main.py
```

> After uninstalling, you can still run Lee manually with `python main.py` or `bash scripts/Lee.sh start` — it just won't auto-start anymore.

---

### 🔧 Advanced: Manual launchctl Commands

For power users who want finer control over the macOS service:

```bash
# Check if the launchd service is loaded
launchctl list | grep Lee

# View detailed service info (PID, exit status, etc.)
launchctl list com.Lee.assistant

# Temporarily stop the service (will NOT auto-restart)
launchctl unload ~/Library/LaunchAgents/com.Lee.assistant.plist

# Re-enable and start the service
launchctl load ~/Library/LaunchAgents/com.Lee.assistant.plist

# Validate the plist file for syntax errors
plutil -lint ~/Library/LaunchAgents/com.Lee.assistant.plist
```

---

### 🔄 Lifecycle Summary

```
┌─────────────────────────────────────────────────────────────┐
│                    Lee Service Lifecycle                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  install_service.sh ──► launchd loads plist                 │
│                              │                              │
│                              ▼                              │
│                    ┌─────────────────┐                      │
│   Mac login ──────►│   Lee starts   │◄──── auto-restart    │
│                    │   (port 8000)   │      on crash        │
│                    └────────┬────────┘                      │
│                             │                               │
│              Lee.sh stop ──┤── Lee.sh restart              │
│                             │                               │
│                             ▼                               │
│                    ┌─────────────────┐                      │
│                    │   Lee stops    │                       │
│                    └────────┬────────┘                      │
│                             │                               │
│         install_service.sh --uninstall                       │
│                    (removes auto-start)                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```



## 🌐 Web Dashboard

The web dashboard is available at **http://localhost:8000** and provides:

- 💬 **Real-time chat** via WebSocket — instant responses
- 📝 **Markdown rendering** — code blocks, tables, lists
- 📂 **Conversation sidebar** — browse & manage chat history
- 🔧 **Tool visualization** — see when Lee uses system tools
- 🎨 **Beautiful UI** — dark theme with smooth animations

---

## 💬 Discord Bot

To use Lee on Discord:

1. Create a bot at [Discord Developer Portal](https://discord.com/developers/applications)
2. Enable **Message Content Intent** in Bot settings
3. Add the bot token to your `.env` file
4. Invite the bot to your server with these permissions:
   - Read Messages / View Channels
   - Send Messages
   - Read Message History

**Usage:**
- **DM the bot** directly, or
- **@mention Lee** in any channel she's in

---

## 🔧 Available Tools

Lee has 12 built-in tools that let her interact with your Mac:

| Tool | Description | Example Prompt |
|------|-------------|----------------|
| `get_system_info` | CPU, RAM, disk, battery status | *"How's my system doing?"* |
| `get_datetime` | Current date, time, timezone | *"What time is it?"* |
| `open_application` | Launch macOS apps | *"Open Safari"* |
| `run_shell_command` | Execute shell commands | *"List running processes"* |
| `read_file` | Read file contents | *"Read my ~/.zshrc file"* |
| `write_file` | Create or modify files | *"Create a Python hello world script"* |
| `list_directory` | Browse directory contents | *"What's on my Desktop?"* |
| `get_clipboard` | Read clipboard | *"What's in my clipboard?"* |
| `set_clipboard` | Write to clipboard | *"Copy this text for me: ..."* |
| `take_screenshot` | Capture the screen | *"Take a screenshot"* |
| `web_search` | Search the internet | *"Search for latest Python news"* |
| `get_weather` | Weather information | *"Weather in Tokyo?"* |
| `get_unread_emails` | Read unread Gmails | *"Do I have any new emails?"* |
| `send_email` | Send a Gmail | *"Email john@example.com saying hello"* |

---

## ✅ Do's — What You Can Do

### 💬 Chat Naturally
- Ask Lee anything — general questions, quick tasks, or system operations
- Chat via the **Web Dashboard** (`http://localhost:8000`) or **Discord** (DM or @mention)
- Browse, search, and delete past conversations from the sidebar

### 🔧 Use All 12 System Tools
| What to Ask | Example Prompt |
|-------------|----------------|
| Check system health | *"How's my system doing?"* |
| Get the current time | *"What time is it?"* |
| Open any macOS app | *"Open Safari"* |
| Run shell commands | *"List running processes"* |
| Read file contents (≤ 1MB) | *"Read my ~/.zshrc"* |
| Create or overwrite files | *"Create a Python hello world script"* |
| Browse directories | *"What's on my Desktop?"* |
| Read clipboard contents | *"What's in my clipboard?"* |
| Copy text to clipboard | *"Copy this for me: ..."* |
| Capture screen | *"Take a screenshot"* |
| Search the internet | *"Search for latest Python news"* |
| Check weather anywhere | *"Weather in Tokyo?"* |
| Check or send Gmails | *"Read my unread emails or send an email"* |

### ⚙️ Manage the Service
- Run in foreground (`python main.py`), background (`bash scripts/Lee.sh start`), or as a 24/7 `launchd` service
- Use `bash scripts/Lee.sh {stop|restart|status|logs}` for full control
- Install/uninstall the auto-start service anytime

### 🎨 Customize Lee
- Change the **model**, **temperature**, **max tokens**, or **history length** in `config.py`
- Change the **name** and **personality** via `SYSTEM_PROMPT` in `config.py`
- Change the **port** (default `8000`) in `config.py`
- Web search works **without** a Tavily API key — it falls back to DuckDuckGo automatically

---

## 🚫 Don'ts — What to Avoid

### 🔒 Security Don'ts

| Don't | Why |
|-------|-----|
| **Don't expose port 8000 to the internet** | Lee has no authentication — anyone with access could control your machine |
| **Don't port-forward 8000 on your router** | Same reason — keep it strictly on `localhost` |
| **Don't commit `.env` to version control** | It contains your API keys (Groq, Discord, Tavily) |
| **Don't change `HOST` from `127.0.0.1` to `0.0.0.0`** | This would expose Lee to your entire network |
| **Don't share your Groq API key** | Free tier has rate limits; misuse could exhaust your quota |

### ⚠️ Usage Don'ts

| Don't | Why |
|-------|-----|
| **Don't ask Lee to delete critical system files** | The dangerous-command blocklist is limited — use caution |
| **Don't try to read files larger than 1MB** | They will be rejected; use the terminal directly for large files |
| **Don't run long-running commands** | Shell commands timeout at **30 seconds** |
| **Don't run interactive commands** (vim, nano, ssh, etc.) | The shell tool only captures stdout/stderr, not interactive I/O |
| **Don't rely solely on the command blocklist** | It only blocks a few patterns (`rm -rf /`, `mkfs`, `dd if=`, fork bombs) — many destructive commands can still pass through |

### 🏗️ Architecture Don'ts

| Don't | Why |
|-------|-----|
| **Don't edit source files without restarting** | Code changes only take effect after `bash scripts/Lee.sh restart` |
| **Don't run multiple instances on the same port** | You'll get a "port already in use" error |
| **Don't expect multi-user support** | Lee is designed for single-user, local use only |
| **Don't expect image/vision capabilities** | The current LLM (LLaMA 3.3 70B via Groq) is text-only |

---

## 🛡️ Security

Lee is designed for **local, personal use**. Here's what you should know:

### ✅ Safe by Default

- **Localhost only** — Lee binds to `127.0.0.1`, so only your machine can access it
- **No internet exposure** — Nothing is exposed beyond your machine
- **Dangerous command blocking** — Destructive shell commands (like `rm -rf /`) are blocked
- **File size limits** — File reads are capped at 1MB to prevent memory issues
- **Command timeouts** — Shell commands timeout after 30 seconds

### ⚠️ Precautions

| Risk | Mitigation |
|------|-----------|
| API keys in `.env` | Keep `.env` out of version control (add to `.gitignore`) |
| Shell command execution | Lee blocks known dangerous patterns, but use judgment |
| Don't port-forward port 8000 | Keep your router's port forwarding off for this port |
| macOS Firewall | Keep it enabled — it blocks unsolicited incoming connections |

### 🔒 Optional: Add Authentication

If you want an extra layer of security, you can add HTTP Basic Auth to the FastAPI app by modifying `channels/web.py`.

---

## 📁 Project Structure

```
Personal_AI_Assistant/
├── main.py                     # Entry point — starts web server + Discord bot
├── config.py                   # Central configuration & tool definitions
├── requirements.txt            # Python dependencies
├── .env                        # API keys (not in version control)
│
├── core/                       # Core AI engine
│   ├── engine.py               # LLM interaction & tool execution loop
│   ├── tools.py                # 12 system tool implementations
│   ├── history.py              # SQLite conversation history manager
│   └── models.py               # Data models
│
├── channels/                   # Communication channels
│   ├── web.py                  # FastAPI routes + WebSocket chat
│   └── discord_bot.py          # Discord bot integration
│
├── static/                     # Web dashboard frontend
│   ├── index.html              # Dashboard HTML
│   ├── style.css               # Styles (dark theme)
│   └── app.js                  # Frontend logic (WebSocket, markdown)
│
├── scripts/                    # Service management
│   ├── Lee.sh                 # Start/stop/restart/status/logs
│   └── install_service.sh      # launchd installer/uninstaller
│
└── data/                       # Runtime data (auto-created)
    ├── Lee.db                 # SQLite database
    ├── Lee_stdout.log         # Service stdout logs
    └── Lee_stderr.log         # Service stderr logs
```

---

## 🐛 Troubleshooting

### Lee won't start

```bash
# Check the error logs
cat data/Lee_stderr.log

# Verify Python environment
./agentEnv/bin/python -c "import fastapi, groq, discord; print('All good!')"

# Verify .env is configured
cat .env
```

### Port 8000 is already in use

```bash
# Find what's using port 8000
lsof -i :8000

# Kill it (replace PID with actual PID)
kill -9 <PID>

# Or change the port in config.py
```

### launchd service issues

```bash
# Check if the service is loaded
launchctl list | grep Lee

# View the plist for errors
plutil -lint ~/Library/LaunchAgents/com.Lee.assistant.plist

# Reload the service
launchctl unload ~/Library/LaunchAgents/com.Lee.assistant.plist
launchctl load ~/Library/LaunchAgents/com.Lee.assistant.plist
```

### Discord bot not connecting

1. Verify `DISCORD_TOKEN` is set in `.env`
2. Check that **Message Content Intent** is enabled in the [Developer Portal](https://discord.com/developers/applications)
3. Check logs: `tail -f data/Lee_stdout.log`

### High memory usage

Lee is lightweight (typically ~50-100MB). If memory is high:
```bash
# Restart Lee
bash scripts/Lee.sh restart
```

---

## ⚙️ Configuration

All configuration lives in `config.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `AGENT_NAME` | `Lee` | The assistant's name |
| `MODEL_NAME` | `llama-3.3-70b-versatile` | Groq LLM model |
| `MAX_TOKENS` | `4096` | Max response tokens |
| `TEMPERATURE` | `0.7` | LLM creativity (0.0–1.0) |
| `MAX_HISTORY_MESSAGES` | `40` | Context window (messages) |
| `HOST` | `127.0.0.1` | Server bind address |
| `PORT` | `8000` | Server port |

---

## 📜 License

This project is for personal use. Feel free to modify and extend it to your needs.

---

<div align="center">

**Made with ❤️ by you, powered by Groq + LLaMA**

*Lee is always here for you — 24/7* 🌙

</div>
