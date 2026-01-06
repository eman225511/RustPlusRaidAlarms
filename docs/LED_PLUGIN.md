# LED Controller Plugin

The built-in LED plugin triggers WLED, Govee, or Philips Hue lights when Telegram messages arrive, creating visual raid alarms.

## Overview

The LED plugin supports three popular smart lighting systems with customizable actions:
- **WLED** — WiFi-enabled LED controllers with effects, presets, and color control
- **Govee** — Cloud-based smart lighting with scenes and color options
- **Philips Hue** — Zigbee bridge-based smart bulbs with RGB color control

## Supported Systems

### WLED
- **Actions**: On/Off, Color, Effect, Preset, Brightness
- **Features**: 
  - 255+ built-in effects (e.g., Rainbow, Fire, Twinkle)
  - Custom presets for saved configurations
  - Full RGB color control
  - Brightness control (0–255)
- **Requirements**: Device IP address on your local network

### Govee
- **Actions**: On/Off, Color, Scene, Brightness
- **Features**:
  - Predefined scenes (0–50, device-dependent)
  - RGB color control
  - Brightness control (0–100%)
  - Cloud API integration
- **Requirements**: 
  - Govee API key (from developer portal)
  - Device ID (MAC address or device identifier)
  - Device model (e.g., "H6127")

### Philips Hue
- **Actions**: On/Off, Color, Brightness
- **Features**:
  - RGB color control (auto-converted to HSV)
  - Brightness control
  - Bridge-based control
- **Requirements**:
  - Bridge IP address
  - Bridge username (from pairing process)

## Available Actions

### On / Off
Simple power toggle for any LED system.
- **Use Case**: Turn on lights when raid alarm arrives, turn off after delay

### Color
Set RGB color using hex values (e.g., `#FF0000` for red).
- **UI**: Click the color button to open a color picker dialog
- **Use Case**: Red for raids, blue for cargo ship, green for helicopter

### Effect (WLED only)
Trigger animated effects by numeric ID (0–255).
- **Examples**: 
  - `0` — Solid color
  - `1` — Blink
  - `9` — Rainbow
  - `44` — Fire Flicker
- **Find IDs**: Open `http://<wled-ip>/` and check the effects list
- **Use Case**: Flashing red effect for raids, rainbow for special events

### Preset (WLED only)
Load saved WLED presets by numeric ID (0–255).
- **Setup**: Create presets in the WLED web interface
- **Use Case**: Complex lighting scenes with multiple segments
- **Note**: Presets are stored on the WLED device

### Scene (Govee only)
Trigger predefined Govee scenes by numeric code (0–50+).
- **Examples** (device-dependent):
  - `1` — Sunrise
  - `5` — Sunset
  - `15` — Party
- **Find IDs**: Check your Govee app or API documentation
- **Use Case**: Dynamic lighting for different event types

### Brightness
Set intensity level (converted to device-specific range).
- **WLED**: 0–255 (raw value)
- **Govee**: 0–100 (percentage)
- **Hue**: 0–254 (Hue API range)
- **Note**: Brightness applies to all other actions (color, effect, preset, scene)

## Configuration

### Step 1: Select LED Type
1. Open the LED plugin tab
2. Click the radio button for your LED system (WLED/Govee/Hue)
3. The UI will show relevant configuration fields

### Step 2: Enter Device Credentials

**For WLED:**
- **IP Address**: Device IP on your local network (e.g., `192.168.1.100`)
- **Find IP**: Check your router's DHCP list or WLED AP mode

**For Govee:**
- **API Key**: Get from [Govee Developer Portal](https://developer.govee.com)
- **Device ID**: MAC address or device identifier (from Govee app)
- **Device Model**: Model number (e.g., `H6127`, `H6159`)
- **Scan Devices (recommended)**: Click **🔍 Scan Govee Devices** after entering your API key. The first device will auto-fill Device ID and Model, and a list of all found devices will be shown.

**For Philips Hue:**
- **Bridge IP**: Hue bridge IP address (find in Hue app under Settings → Bridge)
- **Username**: Bridge API username (requires pairing — press bridge button then make auth request)
- **Generate Username**: Follow [Hue Getting Started Guide](https://developers.meethue.com/develop/get-started-2/)

### Step 3: Configure Action and Parameters

1. Select an action (On/Off/Color/Effect/Preset/Scene/Brightness)
2. Set parameters based on action:
   - **Color**: Click color button to open picker
   - **Effect**: Enter effect ID (0–255)
   - **Preset**: Enter preset ID (0–255)
   - **Scene**: Enter scene code (0–50+)
   - **Brightness**: Enter percentage (0–100)

### Step 4: Save and Test

1. Click **Save Settings** to persist configuration
2. Click **Test LEDs** to verify the connection
3. Send a test message to your Telegram channel to verify trigger

## Usage Examples

### Example 1: Red Alert for Raids (WLED)
- **LED Type**: WLED
- **IP**: `192.168.1.100`
- **Action**: Color
- **Color**: `#FF0000` (red)
- **Brightness**: `100`
- **Telegram Filter**: Enable filter, keyword: "raid"

### Example 2: Fire Effect for Raids (WLED)
- **LED Type**: WLED
- **IP**: `192.168.1.100`
- **Action**: Effect
- **Effect**: `44` (Fire Flicker)
- **Brightness**: `80`

### Example 3: Govee Sunrise Scene for Cargo Ship
- **LED Type**: Govee
- **API Key**: `your-api-key`
- **Device ID**: `AA:BB:CC:DD:EE:FF`
- **Model**: `H6127`
- **Action**: Scene
- **Scene**: `1` (Sunrise)
- **Brightness**: `70`
- **Telegram Filter**: Enable filter, keyword: "cargo"

### Example 4: Hue Color Cycle
- **LED Type**: Hue
- **Bridge IP**: `192.168.1.50`
- **Username**: `your-hue-username`
- **Action**: Color
- **Color**: `#00FF00` (green)
- **Brightness**: `100`

## Advanced Features

### Brightness Auto-Conversion
The plugin automatically converts brightness values to the correct range:
- **WLED**: Your percentage is multiplied by 2.55 (0–100 → 0–255)
- **Govee**: Percentage sent directly (0–100)
- **Hue**: Converted to Hue's 0–254 range

### Dynamic UI
The plugin shows/hides fields based on selected LED type and action:
- Effect/Preset fields only appear for WLED
- Scene field only appears for Govee
- Color picker appears for Color action
- Brightness field appears for all actions

### Color Picker
Click the color button to open a full-featured color dialog:
- Visual color wheel and sliders
- Hex value input
- Recent colors palette
- Alpha channel support (ignored by LED devices)

## Troubleshooting

### WLED Issues

**Problem**: "Test LEDs" fails or no response
- **Check IP**: Verify device IP in your router settings
- **Verify Reachability**: Open `http://<wled-ip>/` in a browser
- **Check JSON API**: Visit `http://<wled-ip>/json/info` to verify API is enabled
- **Firewall**: Ensure port 80 is not blocked
- **WiFi**: Ensure WLED device is connected to the same network

**Problem**: Effect doesn't match expected behavior
- **Check Effect ID**: Open WLED web interface and verify effect numbers
- **Brightness Too Low**: Increase brightness value if effect is dim
- **Preset Override**: Some presets may override effect settings

### Govee Issues

**Problem**: API key not working
- **Verify Key**: Check [Govee Developer Portal](https://developer.govee.com) for valid key
- **Rate Limiting**: Govee API has rate limits (10 requests/min)
- **Device Support**: Not all Govee devices support API control

**Problem**: Scene doesn't activate
- **Invalid Scene ID**: Check device-specific scene codes in Govee app
- **Device Model**: Ensure model number matches exactly (case-sensitive)
- **Cloud Connection**: Verify device is online in Govee app

### Philips Hue Issues

**Problem**: Bridge not responding
- **Check Bridge IP**: Verify IP in Hue app (Settings → Bridge)
- **Network**: Ensure bridge is on the same network as your PC
- **Username Invalid**: Re-authenticate by pressing bridge button and creating new username

**Problem**: Color not accurate
- **RGB Conversion**: Hue uses HSV internally; some colors may shift slightly
- **Brightness**: Ensure brightness is above 20% for accurate colors
- **Light Capabilities**: Some Hue bulbs have limited color ranges

### General Issues

**Problem**: Telegram trigger doesn't activate LEDs
- **Check Telegram Connection**: Verify green status pill in Settings
- **Keyword Filter**: If enabled, ensure message contains the keyword
- **Config Saved**: Click "Save Settings" after changing LED config
- **Test First**: Use "Test LEDs" button before relying on Telegram trigger

**Problem**: Settings not persisted
- **Config File**: Check that `config.json` is writable
- **Save Button**: Always click "Save Settings" after changes
- **App Restart**: Try restarting the app to reload config

For more help, see the [Troubleshooting Guide](TROUBLESHOOTING.md) or [Configuration Guide](CONFIGURATION.md).
