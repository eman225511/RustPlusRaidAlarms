# Telegram Setup

This guide walks you through creating a Telegram bot and obtaining your chat ID for use with RustPlus Raid Alarms.

## 📺 Video Tutorials

**Prefer video guides?** Watch these step-by-step tutorials:
- **[Making a Telegram Bot](https://youtu.be/_w4VcagV8EA?si=f3G6vHn-Wmlz5Elu)** - Create your bot with @BotFather
- **[Add IFTTT to Telegram](https://youtu.be/4NVHvA1kXG0?si=S8XAn8CaeG9b0atQ)** - Add IFTTT bot for Rust+ integration
- **[Add IFTTT Bot to Channel](https://youtu.be/Wex5833rA3k?si=c-wSmEe3KMh-tOGg)** - Make IFTTT post to your channel

## Prerequisites
- Telegram account (mobile or desktop app)
- A Telegram channel or group where raid alarms will be sent

## Step 1: Create a Telegram Bot

**📺 [Video Guide: Making a Bot](https://youtu.be/_w4VcagV8EA?si=f3G6vHn-Wmlz5Elu)**

1. Open Telegram and start a chat with [@BotFather](https://t.me/BotFather)
2. Send the command `/newbot`
3. Follow the prompts:
   - Choose a display name for your bot (e.g., "My Raid Alarm Bot")
   - Choose a username ending in "bot" (e.g., "my_raid_alarm_bot")
4. BotFather will respond with your bot token:
   ```
   123456789:ABCdefGHIjklMNOpqrsTUVwxyz
   ```
   **⚠️ Keep this token secure!** Anyone with the token can control your bot.

## Step 2: Add Bots to Your Channel/Group

**📺 [Video Guide: Add IFTTT to Channel](https://youtu.be/Wex5833rA3k?si=c-wSmEe3KMh-tOGg)**

### Add Your Bot
1. Open your target channel or group
2. Go to **Settings** → **Administrators** → **Add Admin**
3. Search for your bot by username
4. Grant the bot permission to **Post Messages** (minimum required)

### Add IFTTT Bot (for Rust+ integration)
**📺 [Video Guide: Add IFTTT Bot](https://youtu.be/4NVHvA1kXG0?si=S8XAn8CaeG9b0atQ)**

1. Add [@IFTTT](https://t.me/ifttt) bot to Telegram
2. Connect your Telegram account to IFTTT
3. Add IFTTT bot as admin to your channel (same as above)
4. Now IFTTT can post Rust+ raid alerts to your channel!

## Step 3: Get Your Chat ID

You need the numeric ID of your channel/group. Choose one method:

### Method A: Using a Bot (Easiest)
1. Forward any message from your channel to [@userinfobot](https://t.me/userinfobot) or [@RawDataBot](https://t.me/RawDataBot)
2. The bot will reply with the message details
3. Look for `chat.id` or `Chat ID` (channels start with `-100`, e.g., `-1001234567890`)

### Method B: Using Telegram API
1. Post a test message in your channel/group
2. Visit this URL in your browser (replace `<YOUR_BOT_TOKEN>`):
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```
3. Look for the `"chat":{"id":...}` field in the JSON response
4. Copy the numeric ID (including the minus sign)

## Step 4: Configure the App

1. Launch RustPlus Raid Alarms
2. Click the **Settings** button in the top toolbar
3. Enter your bot token and chat ID:
   - **Bot Token**: Paste the token from Step 1
   - **Chat ID**: Paste the ID from Step 3
4. Click **Save**
5. The status pill should turn **green** when connected successfully

## Step 5: Test the Connection

1. Send a test message to your channel/group
2. The app should receive the message (check the Telegram service status)
3. If you have the LED plugin configured, it should trigger on matching keywords

## Next Steps

- **Set up IFTTT integration**: See [IFTTT + Rust+ Setup Guide](IFTTT_RUST_SETUP.md) to automatically send raid alarms from your Rust server
- **Configure LED actions**: Navigate to the LED plugin tab to set up your WLED/Govee/Hue device
- **Customize keyword filters**: Enable filtering in Settings to only trigger on specific keywords (e.g., "raid", "attack")

## Troubleshooting

### Bot Token Issues
- **Invalid token format**: Tokens must contain exactly one colon (`:`) in the format `nnnnnnn:xxxxxxxxxxx`
- **Token doesn't work**: Regenerate a new token with BotFather using `/revoke` then `/newbot`

### Chat ID Issues
- **Channel IDs**: Should start with `-100` (e.g., `-1001234567890`)
- **Group IDs**: May be shorter negative numbers (e.g., `-123456789`)
- **Wrong ID**: Make sure you copied the entire ID including the minus sign

### Connection Issues
- **Red status pill**: Check that your bot token and chat ID are correct
- **No messages received**: Ensure the bot is an admin in your channel/group
- **Polling errors**: Check your internet connection and firewall settings

### Permission Issues
- **Bot can't read messages**: Add the bot as an admin with "Post Messages" permission
- **IFTTT messages not appearing**: Also add the IFTTT bot as an admin

For more help, see the [Troubleshooting Guide](TROUBLESHOOTING.md).
