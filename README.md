<div align="center">

# 🤖 Sentinal Lee — Personal AI Assistant

**A powerful, locally-hosted AI assistant that runs 24/7 on your Mac, built for ultimate privacy and deep system integration.**

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Discord](https://img.shields.io/badge/Discord_Bot-5865F2?logo=discord&logoColor=white)](https://discord.com)
[![Telegram](https://img.shields.io/badge/Telegram_Bot-2CA5E0?logo=telegram&logoColor=white)](https://telegram.org)

*Warm, witty, and competent — Sentinal Lee is not just an assistant, he's your trusted companion.*

<br/>

**Built by Jananth Nikash K Y**
🌐 [www.jananthnikash.com](http://www.jananthnikash.com)
💼 [LinkedIn Profile](https://www.linkedin.com/in/jananth-nikash-k-y/)

</div>

---

## ✨ Features

Sentinal Lee is packed with features designed to make your life easier, all while running securely on your own hardware.

| Feature | Description |
|---------|-------------|
| 💬 **Telegram & Discord** | Chat with Lee directly through Telegram or Discord. **Owner-only security** ensures nobody else can use your bot. |
| 🌐 **Web Dashboard** | A beautiful, real-time web chat interface available on your local network. |
| 🧠 **Long-Term Memory** | Lee remembers your preferences, projects, and facts forever using a robust SQLite database. |
| ⚡ **Lightning Fast** | Powered by Groq's Llama models, Lee responds instantly and runs tools in parallel. |
| 🔧 **System Control** | Let Lee control your Mac — he can read/write files, open apps, create Reminders, and run shell commands. |
| ✉️ **Gmail Integration** | Lee can read your unread emails and draft/send replies for you. |
| 🔍 **Web Search** | Live internet access via Tavily to answer up-to-date questions. |
| 📸 **Screenshots & Clipboard** | Lee can see your screen or read what you just copied. |

---

## 🚀 Quick Start Guide

### 1. Clone & Setup
First, get the code onto your Mac and install the requirements:

```bash
# Navigate to the project folder
cd ~/Desktop/Personal_AI_Assistant/Sentinal_Lee

# Create a virtual environment
python3 -m venv agentEnv

# Activate it
source agentEnv/bin/activate

# Install all the necessary packages
pip install -r requirements.txt
```

### 2. Configure Your Secrets (`.env`)
Create a file named `.env` in the `Sentinal_Lee` folder and add your specific keys. **Do not share this file with anyone!**

```env
# 1. API Keys
GROQ_API_KEY=your_groq_api_key
DISCORD_TOKEN=your_discord_bot_token
TELEGRAM_TOKEN=your_telegram_bot_token
TAVILY_API_KEY=your_tavily_key

# 2. Your Identity
AGENT_USER_NAME=YourName

# 3. Security (CRITICAL)
# Find your Telegram ID from @userinfobot
TELEGRAM_OWNER_ID=123456789
# Find your Discord ID by right-clicking your name in Developer Mode
DISCORD_OWNER_ID=987654321
```

### 3. Start the Engine!
You can start Lee simply by running:
```bash
python main.py
```

He will instantly connect to Telegram, Discord, and start the Web Dashboard on `http://localhost:8000`.

---

## 🧠 How Long-Term Memory Works
Lee is designed to be your constant companion. If you tell him a fact about yourself (e.g., *"I'm working on a Python project"* or *"My favorite food is sushi"*), he will permanently learn it. 

- He stores this in his SQLite brain (`data/Lee.db`).
- Every time you start a fresh chat, he recalls everything he knows about you automatically.
- To check what he remembers, just type `/memory` in Telegram or `!memory` in Discord.

---

## 🛠️ The Toolbelt
Lee uses advanced "function calling" to operate your computer. If you ask him to do something, he will select the right tool entirely on his own.

| Tool Name | What it does | Example of what you can say |
|-----------|--------------|-----------------------------|
| `get_system_info` | Checks your RAM, CPU, Battery | *"How is my Mac running?"* |
| `run_shell_command` | Runs terminal commands | *"List all the folders on my Desktop"* |
| `read_file` | Reads code or text | *"Read the config.py file"* |
| `write_file` / `append_file` | Creates or edits files for you | *"Write a quick python script for me"* |
| `set_reminder` | Interacts with Apple Reminders | *"Remind me to call Mom at 5pm"* |
| `open_url` | Opens links in Safari/Chrome | *"Open YouTube for me"* |
| `get_unread_emails` | Checks your Gmail inbox | *"Any new emails today?"* |
| `send_email` | Drafts and sends via Gmail | *"Email John and say I'll be late"* |

---

## 🛡️ Privacy & Security First
Because Lee can run commands on your machine, strict security is built in:
1. **Owner-Only Bots**: The Discord and Telegram bots will completely ignore everyone except the IDs specified in your `.env` file.
2. **Localhost Only**: The Web Dashboard does not expose itself to the public internet.
3. **Command Blocklist**: Destructive terminal commands (like `rm -rf /` or `shutdown`) are hard-blocked by the core engine.

---

## 🎛️ Behind the Scenes (Architecture)
Sentinal Lee is built on a highly concurrent AI pipeline:
- **FastAPI / Uvicorn**: Powers the internal API and WebSocket dashboards.
- **AsyncIO gather**: Executes multiple tools in parallel (e.g. searching the web while simultaneously checking your system status).
- **SQLite FTS5**: Super-fast full-text search powers the conversation history.
- **Groq API**: Currently optimized for `llama-3.3-70b-versatile` to provide top-tier logic with sub-second response times.

---

## 👨‍💻 Credits
**Sentinal Lee Architecture, Engineering, & Design**
Built by **Jananth Nikash K Y**

- 🌐 **Website**: [www.jananthnikash.com](http://www.jananthnikash.com)
- 💼 **LinkedIn**: [Jananth Nikash K Y](https://www.linkedin.com/in/jananth-nikash-k-y/)

---
<div align="center">
<i>"Why do it yourself when Sentinal Lee can do it for you?"</i>
</div>
