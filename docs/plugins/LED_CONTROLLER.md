<div align="center">

# 💡 LED Controller Plugin

**Visual Raid Alarms with Smart Lights**

[![WLED](https://img.shields.io/badge/WLED-Supported-orange?style=flat)](https://kno.wled.ge/)
[![Govee](https://img.shields.io/badge/Govee-Supported-blue?style=flat)](https://www.govee.com/)
[![Philips Hue](https://img.shields.io/badge/Philips_Hue-Supported-brightgreen?style=flat)](https://www.philips-hue.com/)

Trigger WLED, Govee, or Philips Hue lights when Telegram messages arrive.

</div>

---

## 📊 Overview

<details open>
<summary><b>Compatible smart lighting systems</b></summary>

The LED plugin supports three popular platforms with customizable actions:

| System | Type | Control Method | Best For |
|--------|------|----------------|----------|
| 🌈 **WLED** | WiFi LED strips | Local HTTP API | Effects, presets, full customization |
| 🎮 **Govee** | WiFi smart lights | Cloud API | Scenes, easy setup |
| 💡 **Philips Hue** | Zigbee bulbs | Bridge HTTP API | Home automation, reliability |

</details>

---

## 🔌 Supported Systems

<details open>
<summary><b>Platform-specific features and requirements</b></summary>

### 🌈 WLED

**Actions**: On/Off, Color, Effect, Preset, Brightness

**Features**:
- ✨ 255+ built-in effects (Rainbow, Fire, Twinkle, etc.)
- 📦 Custom presets for saved configurations
- 🎨 Full RGB color control
- 🔆 Brightness control (0–255)

**Requirements**:
- 🌐 Device IP address on your local network
- ⚡ WLED firmware installed on ESP8266/ESP32

**Recommended For**: LED strips, addressable LEDs, advanced effects

---

### 🎮 Govee

**Actions**: On/Off, Color, Scene, Brightness

**Features**:
- 🌄 Predefined scenes (0–50, device-dependent)
- 🎨 RGB color control
- 🔆 Brightness control (0–100%)
- ☁️ Cloud API integration

**Requirements**:
- 🔑 [Govee API key](https://developer.govee.com/)
- 🏷️ Device ID (MAC address or identifier)
- 📝 Device model (e.g., "H6127")

**Recommended For**: Govee smart bulbs, light strips with scenes

---

### 💡 Philips Hue

**Actions**: On/Off, Color, Brightness

**Features**:
- 🎨 RGB color control (auto-converted to HSV)
- 🔆 Brightness control
- 🌉 Bridge-based control
- 🔒 Local network only (secure)

**Requirements**:
- 🌐 Bridge IP address
- 👤 Bridge username (from pairing process)

**Recommended For**: Philips Hue bulbs, home automation setups

</details>

---

## 🎬 Available Actions

<details open>
<summary><b>Action types and use cases</b></summary>

| Action | Platforms | Description | Example Use Case |
|--------|-----------|-------------|------------------|
| 🔘 **On / Off** | All | Simple power toggle | Turn on for raids, off after delay |
| 🎨 **Color** | All | RGB hex values | Red for raids, blue for cargo |
| ✨ **Effect** | WLED only | Animated effects (0–255) | Fire flicker, rainbow cycles |
| 📦 **Preset** | WLED only | Saved configurations (0–255) | Complex multi-segment scenes |
| 🌅 **Scene** | Govee only | Predefined scenes (0–50+) | Sunrise, sunset, party modes |
| 🔆 **Brightness** | All | Intensity level (0–100%) | Dim alerts, bright warnings |

### 🔘 On / Off
**Simple power toggle for any LED system**
- ✅ Universal support (all platforms)
- 💡 Use case: Turn on when raid alarm triggers, turn off after delay

### 🎨 Color
**Set RGB color using hex values** (e.g., `#FF0000` for red)
- 🖱️ **UI**: Click color button to open picker dialog
- 🎨 **Popular colors**:
  - `#FF0000` — Red (raids, danger)
  - `#0000FF` — Blue (cargo ship, water events)
  - `#00FF00` — Green (helicopter, safe events)
  - `#FF00FF` — Magenta (special events)
  - `#FFFF00` — Yellow (warnings)

### ✨ Effect (WLED only)
**Trigger animated effects by numeric ID** (0–255)

| ID | Effect Name | Description |
|----|-------------|-------------|
| 0 | Solid | Static color |
| 1 | Blink | Flash on/off |
| 9 | Rainbow | Color cycle |
| 44 | Fire Flicker | Realistic fire |
| 75 | Fireworks | Random bursts |

> 💡 **Find IDs**: Open `http://<wled-ip>/` and check effects list

### 📦 Preset (WLED only)
**Load saved WLED presets** (0–255)
- 🛠️ **Setup**: Create presets in WLED web interface
- 💾 **Storage**: Saved on WLED device
- 🎯 **Use case**: Complex scenes with multiple segments, palettes, effects

### 🌅 Scene (Govee only)
**Trigger predefined Govee scenes** (0–50+, device-dependent)

| Code | Scene | Description |
|------|-------|-------------|
| 1 | Sunrise | Warm sunrise gradient |
| 5 | Sunset | Orange/red sunset |
| 15 | Party | Color cycling |

> 📱 **Find IDs**: Check Govee app or [API docs](https://developer.govee.com)

### 🔆 Brightness
**Set intensity level** (auto-converted to device range)

| Platform | Input Range | Device Range | Conversion |
|----------|-------------|--------------|------------|
| WLED | 0–100% | 0–255 | `value × 2.55` |
| Govee | 0–100% | 0–100 | Direct |
| Hue | 0–100% | 0–254 | `value × 2.54` |

> ℹ️ Brightness applies to all other actions (color, effect, preset, scene)

</details>

---

## ⚙️ Configuration

<details open>
<summary><b>4-step setup guide</b></summary>

### 1️⃣ Select LED Type
1. Open the **LED Controller** plugin tab
2. Click the radio button for your system:
   - 🌈 WLED
   - 🎮 Govee  
   - 💡 Philips Hue
3. UI will show relevant fields automatically

---

### 2️⃣ Enter Device Credentials

<details>
<summary><b>🌈 For WLED</b></summary>

| Field | Value | How to Find |
|-------|-------|-------------|
| **IP Address** | `192.168.1.100` | Router DHCP list or WLED AP mode |

**Quick Find:**
- Connect to WLED's WiFi AP (if not configured)
- Check router admin panel → Connected Devices
- Use network scanner app

</details>

<details>
<summary><b>🎮 For Govee</b></summary>

| Field | Value | How to Get |
|-------|-------|------------|
| **API Key** | `xxxxxxx...` | [Govee Developer Portal](https://developer.govee.com) |
| **Device ID** | `AA:BB:CC:DD:EE:FF` | Govee app or scan button |
| **Device Model** | `H6127` | Device packaging or app |

**🔍 Quick Setup:**
1. Enter your API key
2. Click **🔍 Scan Govee Devices**
3. First device auto-fills ID and Model
4. List of all devices shown for reference

</details>

<details>
<summary><b>💡 For Philips Hue</b></summary>

| Field | Value | How to Get |
|-------|-------|------------|
| **Bridge IP** | `192.168.1.50` | Hue app → Settings → Bridge |
| **Username** | Bridge API key | [Pairing process](https://developers.meethue.com/develop/get-started-2/) |

**🔑 Generate Username:**
1. Press button on Hue bridge
2. Within 30 seconds, send auth request:
   ```json
   POST http://<bridge-ip>/api
   {"devicetype":"rustplus_raid_alarms"}
   ```
3. Copy username from response

</details>

---

### 3️⃣ Configure Action and Parameters

1. **Select action** from dropdown:
   - On/Off, Color, Effect, Preset, Scene, Brightness
2. **Set parameters** based on action:

| Action | Parameter | Input Method |
|--------|-----------|-------------|
| Color | Hex value | 🎨 Click color button for picker |
| Effect | Effect ID | 🔢 Enter 0–255 |
| Preset | Preset ID | 🔢 Enter 0–255 |
| Scene | Scene code | 🔢 Enter 0–50+ |
| Brightness | Percentage | 🔢 Enter 0–100 |

---

### 4️⃣ Save and Test

1. ✅ Click **Save Settings** to persist configuration
2. 🧪 Click **Test LEDs** to verify connection
3. 📨 Send test message to Telegram channel to verify trigger

**Success Indicators:**
- ✅ "Test successful" message
- 💡 LEDs respond to test
- 📧 Telegram messages trigger LEDs

</details>

---

## 💡 Usage Examples

<details>
<summary><b>Real-world configuration examples</b></summary>

### 🚨 Example 1: Red Alert for Raids (WLED)

| Setting | Value |
|---------|-------|
| **LED Type** | 🌈 WLED |
| **IP** | `192.168.1.100` |
| **Action** | 🎨 Color |
| **Color** | `#FF0000` (red) |
| **Brightness** | `100%` |
| **Filter** | ✅ Enabled, keyword: "raid" |

**Result**: Bright red LED flash when "raid" appears in Telegram message.

---

### 🔥 Example 2: Fire Effect for Raids (WLED)

| Setting | Value |
|---------|-------|
| **LED Type** | 🌈 WLED |
| **IP** | `192.168.1.100` |
| **Action** | ✨ Effect |
| **Effect** | `44` (Fire Flicker) |
| **Brightness** | `80%` |

**Result**: Realistic fire flickering effect on alarm trigger.

---

### 🌅 Example 3: Govee Sunrise Scene for Cargo Ship

| Setting | Value |
|---------|-------|
| **LED Type** | 🎮 Govee |
| **API Key** | `your-api-key` |
| **Device ID** | `AA:BB:CC:DD:EE:FF` |
| **Model** | `H6127` |
| **Action** | 🌅 Scene |
| **Scene** | `1` (Sunrise) |
| **Brightness** | `70%` |
| **Filter** | ✅ Enabled, keyword: "cargo" |

**Result**: Warm sunrise gradient when cargo ship spawns.

---

### 🌈 Example 4: Hue Green Alert

| Setting | Value |
|---------|-------|
| **LED Type** | 💡 Philips Hue |
| **Bridge IP** | `192.168.1.50` |
| **Username** | `your-hue-username` |
| **Action** | 🎨 Color |
| **Color** | `#00FF00` (green) |
| **Brightness** | `100%` |

**Result**: Bright green Hue bulbs on any Telegram message.

</details>

---

## 🚀 Advanced Features

<details>
<summary><b>Smart automation and UI features</b></summary>

### 🔄 Brightness Auto-Conversion
The plugin automatically converts your 0–100% input to device-specific ranges:

| Platform | Your Input | Device Receives | Formula |
|----------|------------|-----------------|----------|
| WLED | 75% | 191 | `75 × 2.55 = 191` |
| Govee | 75% | 75 | Direct |
| Hue | 75% | 190 | `75 × 2.54 = 190` |

### 🎛️ Dynamic UI
Fields automatically show/hide based on selections:

| Selection | Visible Fields |
|-----------|----------------|
| WLED + Effect | IP, Effect ID, Brightness |
| WLED + Preset | IP, Preset ID, Brightness |
| Govee + Scene | API Key, Device ID, Model, Scene, Brightness |
| Govee + Color | API Key, Device ID, Model, Color Picker, Brightness |
| Hue + Color | Bridge IP, Username, Color Picker, Brightness |

### 🎨 Color Picker
Click the color button to open full-featured dialog:
- 🌈 Visual color wheel and sliders
- 🔤 Hex value input field
- 🎨 Recent colors palette
- 📊 HSV/RGB sliders
- 🔍 Eyedropper tool (OS-dependent)

> ℹ️ Alpha channel is ignored by LED devices

</details>

---

## 🔧 Troubleshooting

<details>
<summary><b>Common issues and solutions</b></summary>

### 🌈 WLED Issues

| Problem | Symptoms | Solution |
|---------|----------|----------|
| ❌ Test fails / No response | "Test LEDs" button shows error | Verify device IP in router<br>Open `http://<wled-ip>/` in browser<br>Check `http://<wled-ip>/json/info`<br>Verify port 80 not blocked<br>Ensure same WiFi network |
| 🎭 Effect mismatch | Wrong animation plays | Open WLED web UI to verify effect IDs<br>Increase brightness if effect seems dim<br>Check if preset is overriding effect |

---

### 🎮 Govee Issues

| Problem | Symptoms | Solution |
|---------|----------|----------|
| 🔑 API key invalid | Authentication errors | Verify key at [Govee Developer Portal](https://developer.govee.com)<br>Check rate limits (10 requests/min)<br>Confirm device supports API control |
| 🌅 Scene not activating | No visual change | Verify scene ID in Govee app<br>Check model number (case-sensitive)<br>Ensure device is online in app |

---

### 💡 Philips Hue Issues

| Problem | Symptoms | Solution |
|---------|----------|----------|
| 🌉 Bridge not responding | Connection timeout | Verify bridge IP (Hue app → Settings → Bridge)<br>Ensure same network as PC<br>Re-authenticate (press bridge button + new username) |
| 🎨 Color inaccurate | Color shifts from expected | RGB→HSV conversion may shift hues<br>Set brightness >20% for accurate colors<br>Some bulbs have limited color gamut |

---

### ⚙️ General Issues

| Problem | Symptoms | Solution |
|---------|----------|----------|
| 📭 Telegram doesn't trigger | Messages arrive but no LED | Check 🟢 green status in Settings<br>Verify keyword filter (if enabled)<br>Click "Save Settings" after config<br>Test manually with "Test LEDs" button |
| 💾 Settings not saved | Config resets on restart | Check `config.json` file permissions<br>Always click "Save Settings"<br>Restart app to reload config |

---

**📚 Need more help?** See [Full Troubleshooting Guide](../TROUBLESHOOTING.md) or [Configuration Guide](../CONFIGURATION.md)

</details>

---

<div align="center">

**[⬅️ Back to Main README](../../README.md)** • **[📖 All Plugin Guides](../../README.md#-plugins)**

Made with ❤️ for the Rust community

</div>
