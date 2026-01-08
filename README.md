# 🚨 RustPlus Raid Alarms

**Never miss a raid again!** Get instant notifications on your phone, auto-launch Rust, flash your lights, and more when your base is under attack.

This sleek desktop app monitors your Telegram for raid alerts from Rust+ (via IFTTT) and triggers customizable plugins—no coding required. Just enable the plugins you want and you're set!

## ✨ Features
- **Telegram Integration** 
  - Real-time message polling with configurable rate (default: 2 seconds)
  - Optional keyword filtering for selective alerts
  - Support for channels and group chats
  - Easy configuration via in-app Settings dialog

- **IFTTT + Rust+ Integration**
  - Connect your Rust server to automatically send raid alarms
  - Trigger on events: raids, cargo ship, helicopter, player activity
  - Customize alert messages with smart-alarm data
  - See [IFTTT Setup Guide](docs/IFTTT_RUST_SETUP.md)

- **Plugin Architecture**
  - Auto-discovered from `plugins/` folder every 5 seconds
  - Hot-reload: add/remove plugins without restarting
  - Supports both single-file (`plugin.py`) and package (`plugin/__init__.py`) formats
  - Plugin base API for UI widgets, config persistence, Telegram hooks
  - Example plugin included as development template

- **LED Controller Plugin**
  - **WLED**: Effects, presets, color, brightness (0–255)
  - **Govee**: Scenes, color, brightness (0–100%)
  - **Philips Hue**: Color control with automatic RGB→HSV conversion
  - Color picker dialog with hex preview
  - Dynamic UI based on selected LED type
  - Trigger actions on Telegram messages

- **Modern Dark UI**
  - Card-based layout with hero sections
  - Left-side navigation with plugin tabs
  - Unified dark theme (#1e1e1e background, #131418 cards, #0e639c accents)
   - Drag-and-drop plugin tab reordering
   - Per-plugin enable/disable toggles and dev-only example toggle
   - Clear log button in Activity Log
   - Responsive design with proper spacing and padding

- **Quality of Life**
   - `config.example.json` template; real `config.json` is gitignored
   - Govee device scan button to auto-fill device ID/model from API key
   - Issue templates for bugs, features, and plugin requests

## Quick Start
1. **Clone the repository**
   ```bash
   git clone https://github.com/eman225511/RustPlusRaidAlarms.git
   cd RustPlusRaidAlarms
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Telegram**
   - Create a bot with [@BotFather](https://t.me/BotFather) → get your token
   - Get your chat ID (see [Telegram Setup Guide](docs/TELEGRAM_SETUP.md) with video tutorials!)
   - Enter credentials via the in-app **Settings** dialog (or edit `config.json`)

4. **Connect IFTTT + Rust+ (optional)**
   - Enables automatic raid alarms sent from your Rust server
   - See the [IFTTT + Rust+ Setup Guide](docs/IFTTT_RUST_SETUP.md) for step-by-step instructions

5. **Run the app**
   ```bash
   python main.py
   ```

6. **Customize plugins** (optional)
   - Navigate to plugin tabs in the left sidebar
   - Configure LED devices, phone numbers, audio files, Discord webhooks, etc.
   - Use the ❓ help buttons for setup guides
   - Click test buttons to verify everything works
   - Enable the plugins you want with the checkboxes!

## Plugins
Plugins are automatically loaded from the `plugins/` directory and appear in the left sidebar. No core code changes needed—just drop in your plugin and it's ready.

### Built-in Plugins
- **💡 LED Controller** — Flash WLED, Govee, or Philips Hue lights when raided ([Guide](docs/plugins/LED_CONTROLLER.md))
- **🎮 Rust Auto-Connect** — Automatically launch Rust and join your server ([Guide](docs/plugins/RUST_CONNECT.md))
- **📞 Twilio Caller** — Call multiple phone numbers to wake you up ([Guide](docs/plugins/TWILIO_CALLER.md))
- **🔊 Audio Alert** — Play custom sounds on multiple audio devices ([Guide](docs/plugins/AUDIO_ALERT.md))
- **💬 Discord Webhook** — Post raid alerts to Discord with @mentions ([Guide](docs/plugins/DISCORD_WEBHOOK.md))
- **Example Plugins** — Templates for developers (hidden by default)

### Plugin Types
- **Single-file**: `plugins/my_plugin.py` (simple plugins)
- **Package**: `plugins/my_plugin/__init__.py` (complex plugins with multiple files)

### Creating Plugins
See the [Plugin Development Guide](docs/PLUGIN_DEVELOPMENT.md) for:
- Plugin base class and required methods
- UI creation with PySide6/Qt
- Config persistence patterns
- Telegram message hooks
- Styling guidelines
- Complete skeleton code

**Example Plugins**:
- `plugins/example_plugin/` — Package-based plugin with advanced features (hero cards, settings, status labels)
- `plugins/simple_example.py` — Single-file plugin showing minimal implementation (counter, name input, buttons)

## 📚 Documentation

### Getting Started
- **[Telegram Setup](docs/TELEGRAM_SETUP.md)** — Creating your bot and getting chat IDs (with video guides!)
- **[IFTTT + Rust+ Setup](docs/IFTTT_RUST_SETUP.md)** — Connect Rust server to send raid alarms to Telegram

### Plugin Guides
- **[LED Controller](docs/plugins/LED_CONTROLLER.md)** — WLED, Govee, and Philips Hue setup
- **[Rust Auto-Connect](docs/plugins/RUST_CONNECT.md)** — Auto-launch Rust when raided
- **[Twilio Caller](docs/plugins/TWILIO_CALLER.md)** — Phone call notifications
- **[Audio Alert](docs/plugins/AUDIO_ALERT.md)** — Custom sound alerts
- **[Discord Webhook](docs/plugins/DISCORD_WEBHOOK.md)** — Discord server notifications

### Advanced
- **[Plugin Development](docs/PLUGIN_DEVELOPMENT.md)** — Create your own plugins
- **[Configuration](docs/CONFIGURATION.md)** — Understanding `config.json`
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** — Common issues and solutions

## LED Controller Plugin
Control smart LED devices directly from the app with trigger-on-message support. **[Full Guide →](docs/plugins/LED_CONTROLLER.md)**

### Supported Devices
- **WLED** — WiFi-enabled LED controllers
- **Govee** — Cloud-based smart lighting (requires API key)
- **Philips Hue** — Zigbee bridge-based smart bulbs

### Actions
- **On/Off** — Simple power control
- **Color** — RGB color picker with hex preview
- **Effect** — WLED animated effects (0–255)
- **Preset** — WLED saved presets (0–255)
- **Scene** — Govee predefined scenes (0–50)
- **Brightness** — Intensity control (WLED: 0–255, Govee: 0–100%)

### Configuration
Each device type requires specific credentials:
- **WLED**: Device IP address
- **Govee**: API key, device ID, device model
- **Philips Hue**: Bridge IP, bridge username

See the [LED Plugin Guide](docs/plugins/LED_CONTROLLER.md) for detailed setup instructions and troubleshooting.

## Configuration
All settings are stored in `config.json` (auto-created on first launch).

### Telegram Settings
- Bot token and chat ID (configured via Settings dialog)
- Polling rate (seconds between checks)
- Keyword filter toggle and keyword

### LED Settings
- Device type (WLED/Govee/Hue)
- Device credentials (IP/API keys/bridge info)
- Default action and parameters (color, effect, preset, scene, brightness)

### Editing Config
- **Recommended**: Use the in-app Settings dialog and plugin UIs
- **Manual**: Edit `config.json` directly (close app first to avoid overwrites)
- **Reset**: Delete `config.json` to restore defaults
- **Template**: `config.example.json` is provided; copy to `config.json` if needed

Feature toggles stored in config:
- `show_example_plugins` — show/hide example plugins in sidebar
- `plugin_enabled_<PluginName>` — per-plugin enable/disable state

See the [Configuration Guide](docs/CONFIGURATION.md) for the complete `config.json` schema and field descriptions.

## Project Structure
```
RustPlusRaidAlarms/
├── main.py                    # App shell, plugin loader, dark theme
├── telegram_service.py        # Telegram polling with auto-retry
├── plugin_base.py             # Abstract plugin base class
├── config.json                # Auto-generated config [gitignored]
├── config.example.json        # Template config file
├── requirements.txt           # Python dependencies
│
├── plugins/
│   ├── led_plugin/            # 💡 LED controller (WLED/Govee/Hue)
│   ├── rust_connect.py        # 🎮 Rust auto-connect
│   ├── twilio_plugin/         # 📞 Twilio phone calls
│   ├── audio_alert.py         # 🔊 Custom sound alerts
│   ├── discord_webhook.py     # 💬 Discord notifications
│   ├── example_plugin/        # Development template (package)
│   └── simple_example.py      # Development template (single-file)
│
└── docs/
    ├── TELEGRAM_SETUP.md      # Bot creation with video guides
    ├── IFTTT_RUST_SETUP.md    # IFTTT + Rust+ integration
    ├── PLUGIN_DEVELOPMENT.md  # Plugin API and creation guide
    ├── CONFIGURATION.md       # config.json schema
    ├── TROUBLESHOOTING.md     # Common issues
    └── plugins/               # Individual plugin guides
        ├── LED_CONTROLLER.md
        ├── RUST_CONNECT.md
        ├── TWILIO_CALLER.md
        ├── AUDIO_ALERT.md
        └── DISCORD_WEBHOOK.md
```

## Contributing
Contributions welcome! Here's how to help:

### Adding Plugins
1. Create your plugin in `plugins/your_plugin/` or `plugins/your_plugin.py`
2. Inherit from `PluginBase` and implement required methods
3. Test using the app's plugin auto-reload (no restart needed)
4. See [Plugin Development Guide](docs/PLUGIN_DEVELOPMENT.md) for API details

### Code Guidelines
- Keep plugin code within plugin widgets—avoid modifying core files unless absolutely necessary
- Follow the existing dark theme styling patterns (see `main.py` CSS)
- Use `config` dict for persistence (auto-saved/merged)
- Add dependencies to `requirements.txt` if needed

### Submitting Changes
- Test your changes thoroughly (LED devices, Telegram, plugin loading)
- Include documentation updates if adding features
- Create descriptive commit messages
- Open a pull request with a clear description
- Use the GitHub issue templates for bugs/feature requests so triage is faster

### Bug Reports
- Check [Troubleshooting Guide](docs/TROUBLESHOOTING.md) first
- Include: OS, Python version, error messages, steps to reproduce
- Share relevant `config.json` snippets (redact tokens/IDs)
- File issues via the GitHub bug/feature templates to ensure required details are included

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [PySide6](https://pypi.org/project/PySide6/) (Qt for Python)
- Telegram integration via [python-telegram-bot](https://python-telegram-bot.org/)
- Designed for [Rust](https://rust.facepunch.com/) server monitoring via [Rust+](https://rust.facepunch.com/companion) and [IFTTT](https://ifttt.com)
