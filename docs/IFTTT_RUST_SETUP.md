<div align="center">

# 🔗 IFTTT + Rust+ + Telegram Integration

**Automate Your Rust Raid Alarms**

[![IFTTT](https://img.shields.io/badge/IFTTT-000000?style=flat&logo=ifttt&logoColor=white)](https://ifttt.com)
[![Rust+](https://img.shields.io/badge/Rust+-CE422B?style=flat&logo=rust&logoColor=white)](https://companion-rust.facepunch.com/)
[![Telegram](https://img.shields.io/badge/Telegram-26A5E4?style=flat&logo=telegram&logoColor=white)](https://telegram.org)

Connect your Rust server events to Telegram via IFTTT, enabling automatic raid alarms, cargo ship notifications, and more.

</div>

---

## 📋 Overview

<details open>
<summary><b>How the automation pipeline works</b></summary>

```
🎮 Rust Server (Smart Alarm) 
        ⬇️
📱 Rust+ Companion App
        ⬇️
🔗 IFTTT (Automation)
        ⬇️
💬 Telegram Channel
        ⬇️
💻 RustPlus Raid Alarms App
        ⬇️
💡 Plugins (LEDs, Sounds, Calls, etc.)
```

## 📺 Video Tutorials

> **Prefer video guides?** Watch these step-by-step tutorials:

| Tutorial | Topic | Duration |
|----------|-------|----------|
| 🤖 [**Making a Telegram Bot**](https://youtu.be/_w4VcagV8EA?si=f3G6vHn-Wmlz5Elu) | Create bot with @BotFather | ~5 min |
| ➕ [**Add IFTTT to Telegram**](https://youtu.be/4NVHvA1kXG0?si=S8XAn8CaeG9b0atQ) | Connect IFTTT for Rust+ | ~3 min |
| 📢 [**Add IFTTT Bot to Channel**](https://youtu.be/Wex5833rA3k?si=c-wSmEe3KMh-tOGg) | Configure channel posting | ~2 min |

---

### Workflow
1. **🚨 Rust+ Smart Alarms** detect in-game events (raids, cargo, helicopter, etc.)
2. **🔗 IFTTT** receives the event and sends a formatted Telegram message
3. **💬 Your Telegram Channel** receives the alert
4. **💻 RustPlus Raid Alarms App** detects the message and triggers actions (LED flash, sounds, calls, etc.)

</details>

---

## ✅ Prerequisites

<details open>
<summary><b>Checklist before you begin</b></summary>

| Requirement | Status | Setup Guide |
|-------------|--------|-------------|
| 🤖 **Telegram Bot** | ☐ | Created via [@BotFather](https://t.me/BotFather) → [Setup Guide](TELEGRAM_SETUP.md) |
| 💬 **Telegram Channel** | ☐ | Where alarms post (bot must be admin) |
| 🔗 **IFTTT Account** | ☐ | Free tier works! → [Sign up](https://ifttt.com) |
| 📱 **Rust+ App** | ☐ | [iOS](https://apps.apple.com/app/rust/id1325038611) \| [Android](https://play.google.com/store/apps/details?id=com.facepunch.rust.companion) |

> 💡 **New to Telegram bots?** Start with our [Telegram Setup Guide](TELEGRAM_SETUP.md) first.

</details>

---

## 🔗 Step 1: Pair Rust+ with Your Server

<details open>
<summary><b>Connect your Rust server to the companion app</b></summary>

### 🎮 In-Game Setup
1. **Join** your Rust server
2. Open your **Main Menu** (ESC)
3. Click the **Rust+** button (📱 phone icon in top-right corner)
4. Click **Pair with Server**
5. 🔔 A notification will appear: "Pairing request sent"

### 📱 Accept Pairing on Mobile App
1. Open the **Rust+** app on your phone
2. You'll see a pairing notification
3. Tap **Accept** to complete the pairing
4. ✅ Your server will now appear in the app's server list

**Success Indicator**: Your server appears with a 🟢 green "Connected" status.

> ⚠️ **Important**: You must be in-game while pairing. Requests expire after a few minutes.

</details>

---

## 🚨 Step 2: Set Up Smart Alarms in Rust

<details open>
<summary><b>Deploy and connect smart alarms in your base</b></summary>

### 🔨 Place a Smart Alarm
1. **Craft or find** a Smart Alarm in Rust
2. **Place it** in your base near valuable loot or TC
3. **Wire it** to sensors:
   - 🚪 Door Controller
   - 🔫 Auto Turret
   - 📦 Storage Monitor
   - ⚡ HBHF Sensor

### 📱 Connect to Rust+
1. Look at the Smart Alarm in-game
2. Press **E** to open its interface
3. Tap the **Rust+** icon (📱)
4. ✅ The alarm appears in your Rust+ app

> 📝 **Naming Tip**: Use descriptive names (e.g., "TC Room" or "Main Loot") — this name appears in your Telegram alerts!

**Common Alarm Placements:**
- 🏗️ **Tool Cupboard Room** - Detects base raids
- 🚪 **Airlock Entrance** - Monitors door breaches
- 📦 **Loot Room** - Guards valuable storage
- 🔫 **Roof/Perimeter** - Detects turret triggers

</details>

---

## 🔗 Step 3: Create an IFTTT Applet

<details open>
<summary><b>Automate Rust events to Telegram messages</b></summary>

### ➕ Start a New Applet
1. Go to [IFTTT.com](https://ifttt.com) and log in
2. Click **Create** in the top-right corner

### 🔴 Configure the IF (Trigger)
1. Click **If This**
2. Search for and select **Rust+**
3. **🔒 First use**: Click **Connect** and authorize IFTTT to access your Rust+ account
4. **Choose a trigger event:**

   | Event | Description | Use Case |
   |-------|-------------|----------|
   | 🚨 **Smart alarm triggered** | Alarm detects activity | Raids, door breaches, turret triggers |
   | 👤 **Player online** | Specific player joins | Track teammates or threats |
   | 🚢 **Cargo ship spawned** | Cargo ship appears | Monument events |
   | 🚁 **Patrol helicopter spawned** | Patrol heli appears | Server events |
   | 🔄 **Server wipe detected** | Server wipes | Blueprint day tracking |

5. **Configure trigger details:**
   - **Select Server**: Choose your paired Rust server
   - **Select Device**: Pick the specific smart alarm (for "Smart alarm triggered")
   - **State**: Usually "Triggered" or "Online"

6. Click **Create trigger**

### 🟢 Configure the THEN (Action)
1. Click **Then That**
2. Search for and select **Telegram**
3. **🔒 First use**: Click **Connect** and authorize IFTTT to access Telegram
4. Choose **Send message to channel**
5. **Configure the action:**

   **Channel**: Select your raid alarm channel from the dropdown

   **Message Text**: Customize using IFTTT ingredients (dynamic data)
   
   <details>
   <summary><b>📝 Message Templates (click to expand)</b></summary>

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

   **📦 Available Ingredients** (click "Add ingredient" to see all):
   - `{{ServerName}}` — Your server name
   - `{{DeviceName}}` — Smart alarm name
   - `{{OccurredAt}}` — Timestamp
   - `{{PlayerName}}` — Player name (for player events)
   - `{{Value}}` — Numeric value (for sensors)

   </details>

6. **Photo URL**: Leave blank (unless you want an image)
7. Click **Create action**

### ✅ Finalize the Applet
1. Review your applet configuration
2. Click **Continue**
3. Optionally rename the applet (e.g., "Rust Raid Alarm → Telegram")
4. Click **Finish**

**✅ Confirmation**: Your applet is now live and will trigger when the Rust+ event occurs.

</details>

---

## 🧪 Step 4: Test the Integration

<details open>
<summary><b>Verify the complete automation pipeline</b></summary>

### End-to-End Test
1. **🎮 In Rust**: Trigger your smart alarm
   - Open a wired door
   - Trigger a sensor
   - Fire at a turret
2. **⏱️ Wait**: IFTTT typically processes events within 10–60 seconds
3. **💬 Check Telegram**: Message should appear in your channel
4. **💻 Check App**: Verify RustPlus Raid Alarms detected the message:
   - 🟢 LED plugin activates (if configured)
   - Status updates appear

**Success Indicators:**
- ✅ Telegram receives the message
- ✅ App shows green connection status
- ✅ Configured plugins trigger (LEDs flash, sounds play, etc.)

### 🔧 Troubleshooting the Test

| Problem | Solution |
|---------|----------|
| ❌ No Telegram message | Check [IFTTT activity log](https://ifttt.com) → My Applets → Settings → View Activity |
| 🔗 Rust+ disconnected | Verify connection in Rust+ app |
| 🔌 IFTTT not connected | Reconnect Telegram integration in IFTTT settings |
| 📭 Message arrives but app doesn't react | Verify bot is admin, check chat ID, check keyword filter |

</details>

---

## 🔄 Step 5: Add More Applets (Optional)

<details>
<summary><b>Create separate applets for different events</b></summary>

### 🎯 Recommended Applets

| Priority | Event | Emoji | Use Case |
|----------|-------|-------|----------|
| 🔴 High | Smart alarm triggered | 🚨 | Base raids, door breaches |
| 🟡 Medium | Cargo ship spawned | 🚢 | Monument events |
| 🟡 Medium | Patrol helicopter | 🚁 | Server events |
| 🟢 Low | Bradley APC spawned | 🚂 | Launch site events |
| 🟢 Low | Player online | 👤 | Track teammates/enemies |
| 🟢 Low | Server wipe detected | 🔄 | Wipe day tracking |

### 🏗️ Multi-Alarm Setup
For bases with multiple smart alarms:
- Create **one applet per alarm** with different message prefixes:
  - "🚨 TC RAID" vs "⚠️ Loot Room"
- Use **keyword filtering** in the app to trigger different LED actions per alarm

> 🆓 **IFTTT Free Tier**: Supports unlimited applets — create as many as you need!

</details>

---

## 🚀 Advanced Configuration

<details>
<summary><b>Optimize your raid alarm setup</b></summary>

### 🔍 Keyword Filtering
Trigger different actions based on message content:

1. **Enable Filter** in RustPlus Raid Alarms Settings
2. Set a **Keyword** (e.g., "RAID")
3. Only messages containing that keyword trigger plugins

**Multi-Keyword Strategy:**

| Message Type | IFTTT Message | App Keyword | Action |
|--------------|---------------|-------------|--------|
| Raid alarm | "🚨 RAID ALARM" | "RAID" | Flash red LEDs |
| Cargo ship | "🚢 CARGO SHIP" | (none) | No LED trigger |
| Helicopter | "🚁 HELICOPTER" | (none) | No LED trigger |

### 💬 Multiple Channels
Route different events to different channels:

- Create multiple Telegram channels:
  - 🚨 "Raids" channel
  - 🎯 "Events" channel
  - 👤 "Player Activity" channel
- Configure IFTTT applets to send to specific channels
- Run multiple RustPlus Raid Alarms instances (different `config.json` per instance)

### 🎨 Message Formatting
Enhance message readability:

| Feature | Syntax | Example |
|---------|--------|----------|
| Emojis | Unicode | 🚨 🚢 🚁 ⚠️ 🔥 |
| Line Breaks | `Shift+Enter` | Multi-line messages |
| Bold | `**text**` | **Important** |
| Italic | `*text*` | *emphasis* |
| Code | `` `text` `` | `DeviceName` |

**Example Structured Message:**
```
🚨 **RAID ALERT** 🚨
────────────
📍 Location: `{{DeviceName}}`
🎮 Server: {{ServerName}}
⏰ Time: {{OccurredAt}}
```

</details>

---

## 🔧 Troubleshooting

<details>
<summary><b>Common issues and solutions</b></summary>

### 🔗 IFTTT Issues

| Problem | Symptoms | Solution |
|---------|----------|----------|
| ❌ Applet not triggering | No Telegram messages after alarm fires | Check [Activity log](https://ifttt.com) → View Activity<br>Verify Rust+ shows "Connected"<br>Reconnect Rust+ service in IFTTT<br>Ensure applet toggle is ON |
| ⏱️ Delayed notifications | Messages arrive 30-60s late | Normal behavior for IFTTT free tier<br>Pro tier reduces delay (optional) |
| 🔴 Service disconnected | "Reconnect required" error | Disconnect and reconnect Rust+ service<br>Reauthorize in IFTTT |

### 📱 Telegram Issues

| Problem | Symptoms | Solution |
|---------|----------|----------|
| 📭 Messages not appearing | IFTTT sends but channel empty | Verify bot is admin in channel<br>Check channel ID in IFTTT<br>Reconnect Telegram in IFTTT |
| 🚫 App not detecting messages | Telegram receives but app doesn't react | Verify chat ID matches (include `-100` prefix)<br>Check bot token in Settings<br>Look for 🟢 green status pill |

### 🎮 Rust+ Issues

| Problem | Symptoms | Solution |
|---------|----------|----------|
| ❓ Can't find Pair button | Menu doesn't show Rust+ option | Open inventory (Tab) → Rust+ icon (📱) top-right<br>Must be in-game on the server |
| 📵 Pairing not appearing | No notification in mobile app | Enable notifications for Rust+ app<br>Ensure same Steam account on both<br>App must be running in background |
| ⏰ Pairing expires | "Request expired" message | Requests expire in ~2 minutes<br>Have phone ready before pairing<br>Simply send a new request |
| 🚨 Alarm not in app | Smart alarm doesn't appear | Place alarm in-game first<br>Look at alarm → Press E → Tap 📱 Rust+ icon<br>Verify server connection in app |
| 🔕 Alarm triggers but IFTTT doesn't | In-game trigger works but no IFTTT | Verify correct device selected in IFTTT applet<br>Disconnect/reconnect Rust+ in IFTTT to refresh devices |

### 💻 App Integration Issues

| Problem | Symptoms | Solution |
|---------|----------|----------|
| 💡 LEDs don't flash | Telegram message received but no LED | Use "Test LEDs" button to verify connectivity<br>Disable keyword filter or add keyword to message<br>Click "Save Settings" after configuration |
| 🔄 Multiple triggers | Same event fires multiple times | Expected if you have multiple applets<br>Use keyword filtering for selective triggers<br>Disable unwanted applets in IFTTT |

---

**📚 Still stuck?** Check the [Full Troubleshooting Guide](TROUBLESHOOTING.md) or open an issue on GitHub.

</details>

---

## 🎯 Next Steps

<details>
<summary><b>Enhance your raid alarm system</b></summary>

| Task | Guide | Description |
|------|-------|-------------|
| 💡 **LED Controller** | [LED Plugin Guide](plugins/LED_CONTROLLER.md) | Set up WLED, Govee, or Hue smart lights |
| 🔌 **Custom Plugins** | [Plugin Development](PLUGIN_DEVELOPMENT.md) | Add custom reactions (sounds, Discord, calls) |
| 🔍 **Keyword Filters** | App Settings | Enable selective triggers |
| 📊 **Monitor Performance** | IFTTT Activity Log | Verify applets are firing correctly |

</details>

---

## 📚 Resources

| Resource | Link | Purpose |
|----------|------|---------|
| 🔗 **IFTTT Rust+ Service** | [ifttt.com/rust](https://ifttt.com/rust) | Browse all Rust+ triggers |
| 📱 **Rust+ Companion** | [companion-rust.facepunch.com](https://companion-rust.facepunch.com/) | Official app info |
| ❓ **IFTTT Help** | [help.ifttt.com](https://help.ifttt.com) | IFTTT documentation |
| 🤖 **Telegram Bot API** | [core.telegram.org/bots](https://core.telegram.org/bots) | Bot development docs |

---

## ✅ Example Complete Setup

<details>
<summary><b>Full working configuration</b></summary>

### Configuration

**Telegram:**
- 🤖 Bot: `@MyRaidAlarmBot`
- 📢 Channel: `@MyRustRaids`
- 🔢 Chat ID: `-1001234567890`

**IFTTT Applet:**
- **Trigger**: Rust+ → Smart alarm triggered → "Main TC Alarm"
- **Action**: Telegram → Send to channel `@MyRustRaids`
- **Message**: 
  ```
  🚨 RAID ALARM!
  Location: {{DeviceName}}
  Server: {{ServerName}}
  Time: {{OccurredAt}}
  ```

**RustPlus Raid Alarms App:**
- ⚙️ **Settings**: Bot token + chat ID configured
- 💡 **LED Plugin**: WLED at `192.168.1.100`
  - Action: Color
  - Color: `#FF0000` (red)
  - Brightness: 100
- 🔍 **Filter**: Enabled, keyword = "RAID"

### Result
When your TC alarm triggers in Rust → IFTTT sends message → Your LEDs flash red! 🔴

</details>

---

<div align="center">

**[⬅️ Back to Main README](../README.md)** • **[📖 All Documentation](../README.md#-documentation)**

Made with ❤️ for the Rust community

</div>
