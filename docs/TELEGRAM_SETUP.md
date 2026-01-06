# Telegram Setup

Follow these steps to get a bot and chat ID working with this app.

## 1) Create a bot
1. Open Telegram and start a chat with [@BotFather](https://t.me/BotFather).
2. Send `/newbot` and follow the prompts to name it.
3. BotFather returns a token like `123456789:ABCdefGHIjklMNOpqrsTUVwxyz` — copy it.

## 2) Add the bot to your channel or group
1. Open your target channel/group settings → Administrators.
2. Add your new bot; grant permission to post messages.
3. If you use IFTTT or another sender, add that bot as admin too.

## 3) Get the chat ID
Pick one method:
- Forward any channel message to @userinfobot or @RawDataBot; copy the `chat.id` (channels start with `-100`).
- Or hit `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` after posting a message; find `"chat":{"id":...}` in the JSON.

## 4) Configure the app
1. Launch the app.
2. Open Settings → paste the bot token and chat ID.
3. Save. The status pill should turn green when connected.

## 5) Troubleshooting
- Tokens must contain one colon (`:`); otherwise they are invalid.
- Channel IDs usually start with `-100`. Groups may be shorter negative numbers.
- Ensure the bot is an admin and can post.
- If polling errors persist, regenerate a token with BotFather and update the app.
