<div align="center">

# 💬 Discord Webhook Plugin

**Post Raid Alerts to Discord**

[![Discord](https://img.shields.io/badge/Discord-5865F2?style=flat&logo=discord&logoColor=white)](https://discord.com)
[![Webhooks](https://img.shields.io/badge/Webhooks-Supported-brightgreen?style=flat)](https://discord.com/developers/docs/resources/webhook)
[![Instant](https://img.shields.io/badge/Notifications-Instant-blue?style=flat)](https://discord.com)

Post raid alerts to your Discord server with @mentions, custom messages, and formatted alerts!

</div>

---

## ✨ Features

<details open>
<summary><b>What this plugin can do</b></summary>

| Feature | Description |
|---------|-------------|
| ⚡ **Instant Notifications** | Alerts appear in Discord immediately |
| 📢 **@everyone Mentions** | Wake up your whole server |
| 👥 **Role Mentions** | Ping specific groups (@Raiders, @PvP Team) |
| 📝 **Custom Messages** | Template system with markdown support |
| 🧪 **Test Button** | Verify setup before relying on it |

</details>

---

## Setup

### Step 1: Create a Discord Webhook

**📍 Click the ❓ button in the plugin for detailed help!**

1. Open Discord and go to your server
2. Right-click the **channel** you want alerts in
3. Click **Edit Channel** → **Integrations**
4. Click **Webhooks** → **New Webhook**
5. Give it a name (e.g., "Raid Alert Bot")
6. Optionally upload an avatar image
7. Click **Copy Webhook URL**
8. Keep this URL **secret**!

### Step 2: Configure the Plugin

1. Open RustPlus Raid Alarms
2. Go to **Discord Webhook** plugin tab
3. Paste your webhook URL
4. Customize the bot name (optional, default: "Raid Alert Bot")

### Step 3: Customize Your Message

Edit the message template to your liking:

**Default:**
```
🚨 **RAID ALERT!** 🚨

You are being raided in Rust!

{telegram_message}
```

**Example custom messages:**
```
⚠️ **URGENT RAID ALERT** ⚠️
Base under attack! Get online NOW!
{telegram_message}
```

```
🔴 RAID IN PROGRESS 🔴
Server: US-West-1
{telegram_message}
@everyone
```

### Step 4: Add Mentions (Optional)

**Mention everyone:**
1. Check the **"@everyone on raid alerts"** box
2. All server members will be notified

**Mention a specific role:**
1. Enable **Developer Mode** in Discord:
   - User Settings → Advanced → Developer Mode (ON)
2. Right-click the role in server settings
3. Click **Copy ID**
4. Paste the role ID into **"Role to mention"** field

### Step 5: Test It

1. Click **💬 Send Test Message** button
2. Check your Discord channel
3. Message should appear with timestamp
4. If it works, enable the plugin checkbox!

## Message Template Syntax

### Variables

- `{telegram_message}` - Inserts the raid alert from Telegram
  - Example: "On: [US] Main Server | Raided by: PlayerName"

### Discord Markdown

Discord supports rich text formatting:

| Format | Syntax | Example |
|--------|--------|---------|
| **Bold** | `**text**` | `**URGENT**` |
| *Italic* | `*text*` | `*Base name*` |
| __Underline__ | `__text__` | `__RAID ALERT__` |
| ~~Strikethrough~~ | `~~text~~` | `~~False alarm~~` |
| `Code` | `` `text` `` | `` `+connect 192.168.1.1` `` |
| Code block | `` ```text``` `` | Multi-line code |

### Mentions

- **@everyone**: Type `@everyone` in the message
- **@here**: Type `@here` (online members only)
- **Role mention**: Use `<@&ROLE_ID>` format
  - Example: `<@&1234567890>` (get ID by copying role)

### Emojis

- **Unicode emojis**: 🚨 ⚠️ 🔴 🟢 ⚡ 💀 🎮 🏠
- **Custom server emojis**: `:emoji_name:` (must exist in your server)

### Line Breaks

Use `\n` for new lines:
```
Line 1\nLine 2\nLine 3
```

Becomes:
```
Line 1
Line 2
Line 3
```

## Example Messages

### Minimal
```
🚨 RAID! {telegram_message}
```

### Standard
```
**⚠️ RAID ALERT**
{telegram_message}
@everyone
```

### Detailed
```
🔴 **RAID IN PROGRESS** 🔴

📍 Server: US-West-Main
⏰ Time: Just now

{telegram_message}

Get online ASAP!
@everyone
```

### Formatted with Code
```
**RAID DETECTED**

{telegram_message}

Quick connect:
`steam://connect/192.168.1.50:28015`
```

### Team Ping
```
⚔️ **RAID ALERT** ⚔️

<@&123456789> GET ONLINE NOW!

{telegram_message}
```

## Role Mentions Setup

### Step 1: Create a Role (if needed)

1. Server Settings → Roles → Create Role
2. Name it (e.g., "PvP Team", "Raiders", "Active Players")
3. Optionally give it a color/icon
4. Assign role to members

### Step 2: Get Role ID

1. Enable Developer Mode (User Settings → Advanced)
2. Right-click the role in **Server Settings → Roles**
3. Click **Copy ID**
4. You'll get something like `987654321012345678`

### Step 3: Add to Plugin

**Option A: Use the role ID field**
- Paste the ID into "Role to mention" input
- Plugin will auto-format it as `<@&ID>`

**Option B: Manually in message template**
- Type `<@&987654321012345678>` directly in your message
- Replace `987654321012345678` with your actual role ID

## Troubleshooting

### Webhook URL not working

**Check the URL format:**
- Should start with: `https://discord.com/api/webhooks/`
- Should be one long string with no spaces
- Example: `https://discord.com/api/webhooks/123456789/AbCdEfGhIjKlMnOpQrStUvWxYz`

**Regenerate if needed:**
1. Go back to Discord channel settings
2. Delete old webhook
3. Create new webhook
4. Copy new URL

### "Invalid Webhook URL"

**Make sure you copied the full URL:**
- Must include both the webhook ID and token
- Check for trailing spaces or line breaks

**Test in browser:**
- Paste URL in browser address bar
- Should show JSON like `{"type": 1, "id": "...", ...}`
- If you get an error, webhook was deleted or is invalid

### Messages not appearing in Discord

**Check webhook permissions:**
- Webhook must have permission to post in the channel
- Check channel permissions for "Webhooks"

**Check channel:**
- Make sure you're looking at the right channel
- Webhook only posts to the channel it was created in

### @everyone not working

**Server settings:**
1. Server Settings → Roles → @everyone
2. Make sure "Mention @everyone, @here, and All Roles" is enabled
3. Webhooks inherit this permission

**Message settings:**
- Type `@everyone` in your message template
- OR check the "@everyone on raid alerts" box

### Role mention not working

**Check role ID:**
- Must be the numeric ID, not the role name
- Format: `<@&1234567890>` (include `<@&` and `>`)

**Role mentionable:**
1. Server Settings → Roles → [Your Role]
2. Check "Allow anyone to @mention this role"
3. Save changes

### Webhook getting rate limited

**Too many messages:**
- Discord limits webhooks to ~5 messages per second
- If you get raided a lot, consider adding cooldown (future feature)

**Temporary solution:**
- Wait 10-30 seconds between test messages
- Avoid spamming the test button

## Security & Privacy

### Webhook URL Security

**⚠️ Keep your webhook URL secret!**

- Anyone with the URL can post to your Discord channel
- Don't share `config.json` with webhook URL in it
- Don't commit it to public GitHub repos

**If compromised:**
1. Delete the webhook in Discord
2. Create a new webhook
3. Update the plugin with new URL

### What Discord Sees

- **Message content**: Your raid alerts and custom message
- **Bot name**: The webhook name you chose
- **Timestamp**: When messages were sent
- **IP address**: Your public IP (logged by Discord)

### Privacy Settings

- Messages are **public** to anyone in the Discord server
- Consider using a **private channel** for sensitive raid alerts
- **DM alerts**: Webhooks can't DM, but you could use Discord bot API (future plugin idea)

## Configuration

Plugin settings saved in `config.json`:

```json
{
  "discord_webhook_url": "https://discord.com/api/webhooks/123456789/AbCdEfGhIjKlMnOp",
  "discord_bot_name": "Raid Alert Bot",
  "discord_mention_everyone": true,
  "discord_role_id": "987654321012345678",
  "discord_message_template": "🚨 **RAID ALERT!** 🚨\n\n{telegram_message}",
  "plugin_enabled_Discord Webhook": true
}
```

**⚠️ Never share your webhook URL publicly!**

## Advanced: Multiple Webhooks

Want to post to multiple channels? Edit the plugin code:

```python
# In send_discord_message() method
webhooks = [
    "https://discord.com/api/webhooks/123/abc",  # Main channel
    "https://discord.com/api/webhooks/456/def",  # Backup channel
]

for webhook_url in webhooks:
    response = requests.post(webhook_url, json=payload)
```

## Rate Limits

Discord webhooks have the following limits:

- **5 messages per second** per webhook
- **30 messages per minute** per webhook
- **2000 characters** per message
- **10 embeds** per message (not used by this plugin)

If you exceed these, Discord will respond with HTTP 429 (rate limit error).

## Alternative: Discord Bot

Webhooks are simple but limited. For advanced features, consider creating a Discord bot:

- **DM notifications** - Message users directly
- **Commands** - Type `/status` to check connection
- **Rich embeds** - Fancy formatted messages with images
- **Reactions** - React with ✅ to acknowledge alert

This would require a separate plugin and more setup (future idea!).

## Support

- **Discord Webhook Docs**: [discord.com/developers/docs/resources/webhook](https://discord.com/developers/docs/resources/webhook)
- **Markdown Guide**: [discord.com/developers/docs/reference#message-formatting](https://discord.com/developers/docs/reference#message-formatting)
- **Plugin Issues**: File a GitHub issue with error messages

---

<div align="center">

**[⬅️ Back to Main README](../../README.md)** • **[📖 All Plugin Guides](../../README.md#-plugins)**

Made with ❤️ for the Rust community

</div>
