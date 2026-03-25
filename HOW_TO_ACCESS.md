# How to Access Sentinal Lee

Sentinal Lee can be accessed and used through two distinct interfaces: the **Discord Bot** and the **Local Web UI**. Both of these interfaces start automatically when you launch the main application.

Below are the dedicated steps to access and use each interface.

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
Once you start the application (`bash scripts/Lee.sh start`), the bot will come online in your Discord server.
- **Direct Message (DM):** You can click on Lee's profile and send her a direct message. She will reply privately.
- **Server Channel:** You can type `@Lee` in a server channel followed by your question or command (e.g. `@Lee take a screenshot`).

---

## 2. Accessing via the Web UI (Dashboard)

The Web Dashboard is a beautiful, locally-hosted interface that runs directly in your browser. It supports rich markdown rendering (code blocks, tables) and shows you a visual history of your conversations.

### How to Access:
1. Ensure the application is running using one of the launch commands:
   ```bash
   python3 main.py
   # OR
   bash scripts/Lee.sh start
   ```
2. Open your preferred web browser (Safari, Chrome, Arc, etc.).
3. Navigate to **[http://localhost:8000](http://localhost:8000)**.

### Features of the Web UI:
- **Conversation History:** A sidebar on the left lets you view, select, and manage past chat sessions.
- **Real-time Streaming:** Lee's responses stream in instantly just like ChatGPT.
- **Tool Visualization:** Whenever Lee uses a tool (like checking the weather or reading a file), you will see exactly what tool she explicitly called before the text answer arrives.
- **Local Network Access (Advanced):** If you want to access this dashboard from another device on your home Wi-Fi (like an iPad), you would need to change the `HOST` setting in `config.py` from `127.0.0.1` to `0.0.0.0`, and then go to your Mac's IP address on the iPad (e.g., `http://192.168.1.5:8000`). *(Warning: Only do this on a trusted home network!)*
