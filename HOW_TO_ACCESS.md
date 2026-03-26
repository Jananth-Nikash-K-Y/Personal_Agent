# How to Access Sentinal Lee

Sentinal Lee can be accessed and used through two distinct interfaces: the **Discord Bot** and the **Telegram Bot**. Both of these interfaces start automatically when you launch the main application.

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
1. Ensure the application is running:
   ```bash
   python3 main.py
   # OR via the service script if setup
   ```
2. Open Telegram and search for the bot you just created.
3. Send it a message! Sentinal Lee will respond privately. Nobody else can interact with this bot.
