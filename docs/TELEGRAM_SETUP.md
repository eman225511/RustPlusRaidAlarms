<div align="center">

# 📱 Telegram Setup Guide

*Create your bot and connect it to RustPlus Raid Alarms*

</div>

---

## 📺 Video Tutorials

> **Prefer video guides?** Watch these step-by-step tutorials:

| Tutorial | Topic | Duration |
|----------|-------|----------|
| 🤖 [**Making a Telegram Bot**](https://youtu.be/_w4VcagV8EA?si=f3G6vHn-Wmlz5Elu) | Create bot with @BotFather | ~5 min |
| ➕ [**Add IFTTT to Telegram**](https://youtu.be/4NVHvA1kXG0?si=S8XAn8CaeG9b0atQ) | Connect IFTTT for Rust+ | ~3 min |
| 📢 [**Add IFTTT Bot to Channel**](https://youtu.be/Wex5833rA3k?si=c-wSmEe3KMh-tOGg) | Configure channel posting | ~2 min |

---

## ✅ Prerequisites

- ✔️ Telegram account (mobile or desktop app)
- ✔️ A Telegram channel or group for raid alarms

---

## 🤖 Step 1: Create a Telegram Bot

<details open>
<summary><b>📺 <a href="https://youtu.be/_w4VcagV8EA?si=f3G6vHn-Wmlz5Elu">Video Guide: Making a Bot</a></b></summary>

### Instructions

1. **Open Telegram** and start a chat with [@BotFather](https://t.me/BotFather)
2. **Send** the command `/newbot`
3. **Follow the prompts:**
   - Choose a **display name** (e.g., "My Raid Alarm Bot")
   - Choose a **username** ending in "bot" (e.g., "my_raid_alarm_bot")

4. **BotFather will respond** with your bot token:
   ```
   123456789:ABCdefGHIjklMNOpqrsTUVwxyz
   ```

> ⚠️ **Keep this token secure!** Anyone with it can control your bot.

</details>

---

## ➕ Step 2: Add Bots to Your Channel/Group

<details open>
<summary><b>Add your bot and IFTTT bot as admins</b></summary>

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

</details>

---

## 🔢 Step 3: Get Your Chat ID

<details open>
<summary><b>Find your channel/group numeric ID</b></summary>

You need the numeric ID of your channel/group. Choose one method:

### 🤖 Method A: Using a Bot (Easiest)
1. Forward any message from your channel to [@userinfobot](https://t.me/userinfobot) or [@RawDataBot](https://t.me/RawDataBot)
2. The bot will reply with the message details
3. Look for `chat.id` or `Chat ID`
   - Channels start with `-100` (e.g., `-1001234567890`)
   - Groups are shorter (e.g., `-123456789`)

### 🌐 Method B: Using Telegram API
1. Post a test message in your channel/group
2. Visit this URL in your browser (replace `<YOUR_BOT_TOKEN>`):
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```
3. Look for the `"chat":{"id":...}` field in the JSON response
4. Copy the numeric ID (including the minus sign)

> 💡 **Tip**: Always include the minus sign when copying the Chat ID!

</details>

---

## ⚙️ Step 4: Configure the App

<details open>
<summary><b>Connect your bot to the application</b></summary>

1. **Launch** RustPlus Raid Alarms
2. Click the **Settings** button (⚙️) in the top toolbar
3. **Enter your credentials:**
   - **Bot Token**: Paste the token from Step 1
   - **Chat ID**: Paste the ID from Step 3
4. Click **Save**
5. ✅ The status pill should turn **green** when connected successfully

> ⚠️ **Connection failed?** Double-check your token and chat ID for typos.

</details>

---

## ✅ Step 5: Test the Connection

<details open>
<summary><b>Verify everything is working</b></summary>

1. ✉️ **Send a test message** to your channel/group
2. 📡 **Check the app** - it should receive the message (monitor the Telegram service status)
3. 💡 **Plugin trigger** - If you have the LED plugin configured, it should activate on matching keywords

**Success indicators:**
- 🟢 Green status pill in main window
- 📥 Messages appear in the application
- 💡 LED/Plugins trigger as configured

</details>

---

## 🎯 Next Steps

<details>
<summary><b>Expand your raid alarm system</b></summary>

### Recommended Setup

| Task | Guide | Description |
|------|-------|-------------|
| 🔗 **IFTTT Integration** | [IFTTT + Rust+ Setup](IFTTT_RUST_SETUP.md) | Automatically send raid alarms from your Rust server |
| 💡 **LED Controller** | [LED Plugin Guide](plugins/LED_CONTROLLER.md) | Set up WLED, Govee, or Hue lights |
| 📞 **Phone Calls** | [Twilio Plugin Guide](plugins/TWILIO_CALLER.md) | Get called when raided (requires Twilio account) |
| 🔊 **Audio Alerts** | [Audio Plugin Guide](plugins/AUDIO_ALERT.md) | Play custom MP3 files on raid |
| 💬 **Discord Webhooks** | [Discord Plugin Guide](plugins/DISCORD_WEBHOOK.md) | Send formatted alerts to Discord |
| 🎮 **Auto-Connect** | [Rust Connect Plugin](plugins/RUST_CONNECT.md) | Launch Rust and connect to your server |

### Advanced Configuration

- 🔍 **Keyword Filtering**: Enable in Settings to only trigger on specific words (e.g., "raid", "attack", "offline")
- ⏰ **Quiet Hours**: Configure time windows to disable notifications
- 🔌 **Custom Plugins**: See [Plugin Development Guide](PLUGIN_DEVELOPMENT.md)

</details>

---

## 🔧 Troubleshooting

<details>
<summary><b>Common issues and solutions</b></summary>

### 🤖 Bot Token Issues

| Problem | Solution |
|---------|----------|
| ❌ Invalid token format | Tokens must contain exactly one colon (`:`) in format `nnnnnnn:xxxxxxxxxxx` |
| 🔑 Token doesn't work | Regenerate with BotFather: `/revoke` then `/newbot` |
| 🔒 Token exposed | Immediately revoke and create a new bot |

### 🔢 Chat ID Issues

| Problem | Solution |
|---------|----------|
| 📺 Channel IDs | Must start with `-100` (e.g., `-1001234567890`) |
| 👥 Group IDs | Shorter negative numbers (e.g., `-123456789`) |
| ❌ Wrong ID | Copy entire ID including the minus sign (`-`) |
| 🔍 Can't find ID | Use [@userinfobot](https://t.me/userinfobot) or [@RawDataBot](https://t.me/RawDataBot) |

### 🌐 Connection Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| 🔴 Red status pill | Incorrect credentials | Verify bot token and chat ID |
| 📭 No messages received | Bot not admin | Add bot as admin with "Post Messages" permission |
| ⚠️ Polling errors | Network/firewall | Check internet connection and firewall settings |
| ⏱️ Timeout errors | API unreachable | Wait a few minutes, app auto-retries |

### 👮 Permission Issues

| Problem | Solution |
|---------|----------|
| 🚫 Bot can't read messages | Make bot an admin with minimum "Post Messages" permission |
| 📭 IFTTT messages not appearing | Add [@IFTTT](https://t.me/ifttt) bot as admin to your channel |
| 🔇 Bot doesn't respond | Check bot is not blocked by Privacy Mode (disable in BotFather) |

---

📚 **Still having issues?** Check the [Full Troubleshooting Guide](TROUBLESHOOTING.md) or [open an issue](https://github.com/YOUR_USERNAME/RustPlusRaidAlarms/issues).

</details>
