# RustPlus Raid Alarms

A plugin-based application that monitors Telegram for raid alarms and triggers customizable actions through plugins.

## Features

- **Telegram Listener Core**: Monitors Telegram chat for raid alarm messages
- **Plugin System**: Easily extensible with custom plugins
- **Modern UI**: Sleek dark theme with vertical navigation tabs
- **LED Controller Plugin**: Control WLED, Govee, or Philips Hue lights when raids are detected

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure your Telegram bot:
   - Create a bot with [@BotFather](https://t.me/botfather)
   - Get your bot token and chat ID
   - Edit `config.json` with your credentials

3. Run the application:
```bash
python main.py
```

## Plugin Development

To create a new plugin:

1. Create a new folder in the `plugins/` directory
2. Create an `__init__.py` file that imports `PluginBase`
3. Create a `Plugin` class that inherits from `PluginBase`
4. Implement the required methods:
   - `get_name()` - Plugin display name
   - `get_icon()` - Plugin icon (emoji)
   - `get_widget()` - Qt widget for the UI
   - `on_telegram_message(message)` - Handler for Telegram messages

Example plugin structure:
```
plugins/
  my_plugin/
    __init__.py
    other_files.py
```

The plugin will automatically appear in the UI when you restart the application!

## Configuration

Edit `config.json` to configure:
- Telegram bot credentials
- LED system settings (WLED/Govee/Hue)
- Polling rate and other preferences

## Current Plugins

### LED Controller
- Supports WLED, Govee, and Philips Hue
- Triggers light effects on raid alarms
- Configurable presets and colors
