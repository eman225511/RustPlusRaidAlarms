# RustPlus Raid Alarms

Sleek, plugin-based desktop app that listens to Telegram for raid alarms and triggers customizable actions (e.g., LEDs). Drop in plugins—no code changes to the core.

## Features
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
   - Get your chat ID (see [Telegram Setup Guide](docs/TELEGRAM_SETUP.md))
   - Enter credentials via the in-app **Settings** dialog (or edit `config.json`)

4. **Connect IFTTT + Rust+ (optional)**
   - Enables automatic raid alarms sent from your Rust server
   - See the [IFTTT + Rust+ Setup Guide](docs/IFTTT_RUST_SETUP.md) for step-by-step instructions

5. **Run the app**
   ```bash
   python main.py
   ```

6. **Customize LED actions** (optional)
   - Navigate to the LED plugin tab
   - Configure your WLED/Govee/Hue device and trigger actions (Govee has a Scan Devices button)
   - See [LED Plugin Guide](docs/LED_PLUGIN.md) for details

## Plugins
Plugins are automatically loaded from the `plugins/` directory and appear in the left sidebar. No core code changes needed—just drop in your plugin and it's ready.

### Built-in Plugins
- **LED Controller** — Control WLED, Govee, or Philips Hue devices with customizable actions
- **Example Plugin** — Development template (package format) showing UI, config persistence, and Telegram hooks
- **Simple Example** — Minimal single-file plugin demonstrating basic functionality

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

## Documentation
- **[Telegram Setup](docs/TELEGRAM_SETUP.md)** — Creating your bot, getting chat IDs, troubleshooting
- **[IFTTT + Rust+ Setup](docs/IFTTT_RUST_SETUP.md)** — Connect your Rust server to send automatic raid alarms to Telegram
- **[LED Plugin Guide](docs/LED_PLUGIN.md)** — Configuring WLED/Govee/Hue devices and actions
- **[Plugin Development](docs/PLUGIN_DEVELOPMENT.md)** — Creating custom plugins with the plugin API
- **[Configuration](docs/CONFIGURATION.md)** — Understanding and editing `config.json`
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** — Common issues and solutions

## LED Controller Plugin
Control smart LED devices directly from the app with trigger-on-message support.

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

See the [LED Plugin Guide](docs/LED_PLUGIN.md) for detailed setup instructions and troubleshooting.

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
├── main.py                    # App shell, plugin loader, dark theme, Telegram wiring
├── telegram_service.py        # Telegram polling thread with keyword filter
├── plugin_base.py             # Abstract plugin base class (contract)
├── config.json                # Auto-generated config (Telegram, LED, plugins) [gitignored]
├── config.example.json        # Template config file
├── requirements.txt           # Python dependencies
│
├── plugins/
│   ├── led_plugin/            # Built-in LED controller
│   │   ├── __init__.py        # Plugin UI and logic
│   │   └── led_controller.py  # WLED/Govee/Hue API clients
│   │
│   ├── example_plugin/        # Package-based development template
│   │   └── __init__.py        # Advanced example with hero cards, settings
│   │
│   └── simple_example.py      # Single-file plugin template (minimal)
│
└── docs/
    ├── TELEGRAM_SETUP.md      # Bot creation and chat ID setup
    ├── IFTTT_RUST_SETUP.md    # IFTTT + Rust+ integration guide
    ├── LED_PLUGIN.md          # LED device configuration
    ├── PLUGIN_DEVELOPMENT.md  # Plugin API and creation guide
    ├── CONFIGURATION.md       # config.json schema and fields
    └── TROUBLESHOOTING.md     # Common issues and solutions
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
