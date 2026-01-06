# Configuration Guide

The app stores all settings in `config.json`, auto-created on first launch.

## Structure
```json
{
  "telegram_bot_token": "123456:ABC...",
  "telegram_chat_id": "-1001234567890",
  "last_message_id": 0,
  "polling_rate": 2,
  "filter_enabled": false,
  "filter_keyword": "",
  "led_type": "wled",
  "wled_ip": "192.168.1.100",
  "govee_api_key": "",
  "govee_device_id": "",
  "govee_model": "",
  "hue_bridge_ip": "",
  "hue_username": "",
  "action": "on",
  "color": "#ffffff",
  "effect": "0",
  "preset": "0",
  "scene": "0",
  "brightness": "100",
  "show_example_plugins": false
}
```

## Fields

### Telegram
- `telegram_bot_token`: Bot token from @BotFather (format: `nnnnnnn:xxxxxx`).
- `telegram_chat_id`: Chat/channel ID (starts with `-100` for channels).
- `last_message_id`: Last processed message ID (auto-updated).
- `polling_rate`: Polling interval in seconds (default: 2).
- `filter_enabled`: `true` to filter messages by keyword.
- `filter_keyword`: Keyword to match (case-insensitive).

### LED settings (global)
- `led_type`: `"wled"`, `"govee"`, or `"hue"`.
- `action`: `"on"`, `"off"`, `"color"`, `"effect"`, `"preset"`, `"scene"`, `"brightness"`.
- `color`: Hex color (e.g., `"#ff0000"`).
- `effect`: WLED effect ID (0–255).
- `preset`: WLED preset ID (0–255).
- `scene`: Govee scene ID (0–50).
- `brightness`: Brightness percentage (1–100).

### WLED
- `wled_ip`: Device IP (e.g., `"192.168.1.100"`).

### Govee
- `govee_api_key`: API key from Govee developer portal.
- `govee_device_id`: Device MAC or ID.
- `govee_model`: Device model (e.g., `"H6127"`).

### Plugin visibility and enablement
- `show_example_plugins`: Show/hide example plugins in the sidebar.
- `plugin_enabled_<PluginName>`: Per-plugin enable/disable (created at runtime per plugin).

### Philips Hue
- `hue_bridge_ip`: Bridge IP address.
- `hue_username`: Bridge username (from pairing flow).

## Editing
- **Via UI**: Use the in-app Settings dialog for Telegram, or the LED plugin UI for LED options.
- **Manual**: Edit `config.json` directly (close the app first or changes may be overwritten).

## Defaults
If fields are missing, the app adds defaults on launch. You can delete `config.json` to reset.

## Backup & template
- Consider backing up `config.json` after configuring, especially if you have complex LED/Govee setups.
- A template `config.example.json` is provided; copy it to `config.json` if you need a fresh start.
