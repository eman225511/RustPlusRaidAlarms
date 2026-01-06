# IFTTT + Rust+ + Telegram Integration Guide

Connect your Rust server events to Telegram via IFTTT, enabling automatic raid alarms, cargo ship notifications, and more. This app will detect these messages and trigger your configured plugins (e.g., LED lights).

## Overview

This integration creates a complete automation pipeline:
1. **Rust+ Smart Alarms** detect in-game events (raids, cargo, helicopter, etc.)
2. **IFTTT** receives the event and sends a Telegram message
3. **Your Telegram Channel** receives the formatted alert
4. **RustPlus Raid Alarms App** detects the message and triggers actions (LED flash, sounds, etc.)

## Prerequisites

Before starting, ensure you have:
- ✅ **Telegram Bot** — Created via [@BotFather](https://t.me/BotFather) ([Setup Guide](TELEGRAM_SETUP.md))
- ✅ **Telegram Channel** — Where raid alarms will be posted (bot must be admin)
- ✅ **IFTTT Account** — Free tier works perfectly ([Sign up](https://ifttt.com))
- ✅ **Rust+ Companion App** — Installed on your phone ([iOS](https://apps.apple.com/app/rust/id1325038611) / [Android](https://play.google.com/store/apps/details?id=com.facepunch.rust.companion))
- ✅ **Rust Server Access** — You must be able to open the in-game console

## Step 1: Pair Rust+ with Your Server

### In-Game Setup
1. Join your Rust server
2. Open your **Inventory** (Tab key)
3. Click the **Rust+** button (phone icon in top-right corner)
4. Click **Pair with Server**
5. A notification will appear saying "Pairing request sent"

### Accept Pairing on Mobile App
1. Open the **Rust+** app on your phone
2. You'll see a pairing notification
3. Tap **Accept** to complete the pairing
4. Your server will now appear in the app's server list

**✅ Confirmation**: Your server should now appear in the Rust+ app with a green "Connected" status.

**💡 Note**: You must be in-game on the server while pairing. The pairing request expires after a few minutes.

## Step 2: Set Up Smart Alarms in Rust

### Place a Smart Alarm
1. Craft or find a **Smart Alarm** in Rust
2. Place it in your base near valuable loot or TC
3. Wire it to sensors (e.g., door, turret, storage monitor)

### Connect to Rust+
1. Look at the Smart Alarm in-game
2. Press **E** to open its interface
3. Tap the **Rust+** icon
4. The alarm will appear in your Rust+ app

**💡 Tip**: Name your alarm descriptively (e.g., "Main Loot Room" or "TC Area") — this name appears in IFTTT notifications.

## Step 3: Create an IFTTT Applet

### Start a New Applet
1. Go to [IFTTT.com](https://ifttt.com) and log in
2. Click **Create** in the top-right corner

### Configure the IF (Trigger)
1. Click **If This**
2. Search for and select **Rust+**
3. **On first use**: Click **Connect** and authorize IFTTT to access your Rust+ account
4. Choose a trigger event:

   **Most Common Triggers:**
   - **Smart alarm triggered** — Fires when your alarm detects activity (raids, door open, etc.)
   - **Player online** — Notifies when specific players join the server
   - **Cargo ship spawned** — Alerts when cargo ship appears
   - **Patrol helicopter spawned** — Alerts when patrol heli appears
   - **Server wipe detected** — Notifies on server wipe

5. Configure trigger details:
   - **Select Server**: Choose your paired Rust server
   - **Select Device**: Pick the specific smart alarm (if using "Smart alarm triggered")
   - **State**: Usually "Triggered" or "Online"

6. Click **Create trigger**

### Configure the THEN (Action)
1. Click **Then That**
2. Search for and select **Telegram**
3. **On first use**: Click **Connect** and authorize IFTTT to access Telegram
4. Choose **Send message to channel**
5. Configure the action:

   **Channel**:
   - Select your raid alarm channel from the dropdown

   **Message Text**:
   - Customize the message using IFTTT ingredients (dynamic data)
   
   **Example Messages:**

   **For Raid Alarms:**
   ```
   🚨 RAID ALARM! 🚨
   Location: {{DeviceName}}
   Server: {{ServerName}}
   Time: {{OccurredAt}}
   ```

   **For Cargo Ship:**
   ```
   🚢 Cargo Ship Spawned!
   Server: {{ServerName}}
   Time: {{OccurredAt}}
   ```

   **For Helicopter:**
   ```
   🚁 Patrol Helicopter Incoming!
   Server: {{ServerName}}
   Time: {{OccurredAt}}
   ```

   **For Player Online:**
   ```
   👤 {{PlayerName}} joined {{ServerName}}
   ```

   **💡 Available Ingredients** (click "Add ingredient" to see all):
   - `{{ServerName}}` — Your server name
   - `{{DeviceName}}` — Smart alarm name
   - `{{OccurredAt}}` — Timestamp
   - `{{PlayerName}}` — Player name (for player events)
   - `{{Value}}` — Numeric value (for sensors)

6. **Photo URL**: Leave blank (unless you want an image)
7. Click **Create action**

### Finalize the Applet
1. Review your applet configuration
2. Click **Continue**
3. Optionally rename the applet (e.g., "Rust Raid Alarm → Telegram")
4. Click **Finish**

**✅ Confirmation**: Your applet is now live and will trigger when the Rust+ event occurs.

## Step 4: Test the Integration

### End-to-End Test
1. **In Rust**: Trigger your smart alarm (open a wired door, trigger a sensor, etc.)
2. **Wait**: IFTTT typically processes events within 10–60 seconds
3. **Check Telegram**: You should see the message in your channel
4. **Check App**: If RustPlus Raid Alarms is running, verify it detected the message:
   - Check the LED plugin for activation (if configured)
   - Look for status updates in the app

### Troubleshooting the Test
- **No Telegram message**: 
  - Check IFTTT activity log (ifttt.com → My Applets → [Your Applet] → Settings → View Activity)
  - Verify Rust+ connection in companion app
  - Ensure IFTTT Telegram integration is connected

- **Message arrives but app doesn't react**:
  - Verify bot is admin in the channel
  - Check chat ID in app Settings matches your channel
  - If keyword filter is enabled, ensure the message contains the keyword

## Step 5: Add More Applets (Optional)

Create separate applets for different events to customize alerts:

### Recommended Applets
1. **Raid Alarm → Telegram** (Smart alarm triggered)
2. **Cargo Ship → Telegram** (Cargo ship spawned)
3. **Helicopter → Telegram** (Patrol helicopter spawned)
4. **Bradley APC → Telegram** (Bradley APC spawned)
5. **Player Online → Telegram** (Player online)
6. **Server Wipe → Telegram** (Server wipe detected)

### Multi-Alarm Setup
For bases with multiple smart alarms:
- Create one applet per alarm with different message prefixes (e.g., "🚨 TC RAID" vs "⚠️ Loot Room")
- Use keyword filtering in the app to trigger different LED actions per alarm

**💡 IFTTT Free Tier**: Supports unlimited applets — create as many as you need!

## Advanced Configuration

### Keyword Filtering
Use keyword filtering in RustPlus Raid Alarms to trigger different actions:

1. **Enable Filter** in app Settings
2. Set a **Keyword** (e.g., "RAID")
3. Only messages containing that keyword trigger plugins

**Multi-Keyword Strategy:**
- Create IFTTT applets with different keywords in messages
- Example:
  - Raid alarm message: "🚨 RAID ALARM"
  - Cargo message: "🚢 CARGO SHIP"
  - Heli message: "🚁 HELICOPTER"
- Enable filtering in app with keyword "RAID" to only flash LEDs for raids

### Multiple Channels
Route different events to different channels:
- Create multiple Telegram channels (e.g., "Raids", "Events", "Player Activity")
- Configure IFTTT applets to send to different channels
- Run multiple instances of RustPlus Raid Alarms (different `config.json` per instance)

### Message Formatting
Enhance message readability:
- **Emojis**: Add visual indicators (🚨 🚢 🚁 ⚠️ 🔥)
- **Line Breaks**: Use `Shift+Enter` in IFTTT message editor
- **Bold/Italic**: Telegram supports markdown (e.g., `**bold**`, `*italic*`)
- **Structured Data**: Include server name, time, location for quick context

## Troubleshooting

### IFTTT Issues

**Problem**: Applet not triggering
- **Check IFTTT Activity**: View Activity log shows recent trigger attempts
- **Verify Rust+ Connection**: Companion app should show "Connected"
- **Reconnect Rust+**: In IFTTT, disconnect and reconnect the Rust+ service
- **Applet Enabled**: Ensure applet toggle is ON in IFTTT

**Problem**: Delayed notifications
- **Normal Behavior**: IFTTT typically has 10–60 second delay
- **Premium**: IFTTT Pro reduces delay but is not required for this use case
- **Server Issues**: Check IFTTT status page for outages

### Telegram Issues

**Problem**: Messages not appearing in channel
- **Bot Admin**: Verify bot has admin rights in the channel
- **Channel ID**: Ensure IFTTT is sending to the correct channel
- **IFTTT Connection**: Reconnect Telegram in IFTTT settings

**Problem**: App not detecting messages
- **Chat ID**: Must match exactly (including `-100` prefix for channels)
- **Bot Token**: Verify token is correct in app Settings
- **Polling**: Check green status pill in Settings (indicates active connection)

### Rust+ Issues

**Problem**: Can't find Pair with Server button
- **Location**: Open inventory (Tab), click Rust+ icon (phone) in top-right corner
- **In-Game Requirement**: Must be connected to the server you want to pair

**Problem**: Pairing request not appearing in app
- **Check Notifications**: Ensure notifications are enabled for Rust+ app
- **Retry**: Send another pairing request from in-game
- **App Running**: Rust+ app should be open or running in background
- **Same Account**: Ensure you're logged into the same Steam/Facepunch account on both game and app

**Problem**: Pairing expires before acceptance
- **Time Limit**: Pairing requests expire after a few minutes
- **Quick Accept**: Have your phone ready before clicking "Pair with Server"
- **Retry**: Simply send a new pairing request from in-game

**Problem**: Smart alarm not appearing in Rust+ app
- **Place Alarm**: Must place the smart alarm in-game first
- **Look at Alarm**: Open its interface and tap the Rust+ icon
- **Server Connection**: Ensure you're connected to the same server in the app

**Problem**: Smart alarm triggers but IFTTT doesn't
- **Device Selection**: In IFTTT applet, verify you selected the correct alarm
- **Refresh Devices**: Disconnect and reconnect Rust+ service in IFTTT to refresh device list

### App Integration Issues

**Problem**: LEDs don't flash on raid alarm
- **Test Manually**: Use "Test LEDs" button in LED plugin to verify device connectivity
- **Keyword Filter**: Disable filter or ensure message contains the keyword
- **Save Settings**: Click "Save Settings" after configuring LED plugin

**Problem**: Multiple triggers firing
- **Expected Behavior**: Each IFTTT applet sends a separate Telegram message
- **Filter by Keyword**: Use keyword filtering to only react to specific messages
- **Disable Unwanted Applets**: Turn off applets you don't need in IFTTT

## Next Steps

After successful setup:
1. **Configure LED Actions**: See [LED Plugin Guide](LED_PLUGIN.md) for customizing light triggers
2. **Create Custom Plugins**: See [Plugin Development Guide](PLUGIN_DEVELOPMENT.md) to add custom reactions (sounds, notifications, etc.)
3. **Fine-Tune Filters**: Enable keyword filtering for selective LED triggers
4. **Monitor Performance**: Check IFTTT activity log periodically to ensure applets are firing correctly

## Resources

- **IFTTT Rust+ Service**: [https://ifttt.com/rust](https://ifttt.com/rust)
- **Rust+ Companion App**: [https://rust.facepunch.com/companion](https://rust.facepunch.com/companion)
- **IFTTT Help Center**: [https://help.ifttt.com](https://help.ifttt.com)
- **Telegram Bot API**: [https://core.telegram.org/bots](https://core.telegram.org/bots)
- **Rust Console Commands**: [https://www.corrosionhour.com/rust-admin-commands/](https://www.corrosionhour.com/rust-admin-commands/)

## Example Complete Setup

Here's a full working example:

**Telegram**:
- Bot: `@MyRaidAlarmBot`
- Channel: `@MyRustRaids`
- Chat ID: `-1001234567890`

**IFTTT Applet**:
- Trigger: Rust+ → Smart alarm triggered → "Main TC Alarm"
- Action: Telegram → Send to channel `@MyRustRaids`
- Message: `🚨 RAID ALARM! Location: {{DeviceName}} on {{ServerName}} at {{OccurredAt}}`

**RustPlus Raid Alarms App**:
- Settings: Bot token + chat ID configured
- LED Plugin: WLED at `192.168.1.100`, action = Color, color = `#FF0000`, brightness = 100
- Filter: Enabled, keyword = "RAID"

**Result**: When your TC alarm triggers in Rust, IFTTT sends a message, and your LEDs flash red!
