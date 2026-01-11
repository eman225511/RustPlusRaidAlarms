# RustPlus Raid Alarms - Plugin Store

This directory contains the plugin index for the RustPlus Raid Alarms Plugin Store.

## How It Works

1. **No plugins shipped by default** - The app ships without any plugins in this folder
2. **Plugin Store** - Users browse and install plugins from the built-in Plugin Store tab
3. **Auto-download** - When installed, plugins are downloaded to the user's local `plugins/` folder
4. **index.json** - Contains metadata for all available plugins (name, version, author, download URL, etc.)

## For Plugin Developers

### Plugin Metadata Fields

Each plugin in `index.json` should have:

```json
{
  "id": "plugin_folder_name",
  "name": "Display Name",
  "icon": "🔥",
  "version": "1.0.0",
  "author": "Your Name",
  "description": "What your plugin does",
  "homepage": "https://github.com/...",
  "download_url": "https://raw.githubusercontent.com/.../plugin.zip",
  "min_app_version": "1.0.0",
  "category": "Alert|Notification|Automation|Development",
  "tags": ["tag1", "tag2"],
  "requires": ["package1", "package2"],
  "size_kb": 50
}
```

### Adding Your Plugin

1. **Create your plugin** following the PluginBase interface:
   - Inherit from `PluginBase`
   - Implement required methods: `get_name()`, `get_icon()`, `get_widget()`, `on_telegram_message()`
   - Optional metadata: `get_version()`, `get_author()`, `get_description()`, `get_homepage()`

2. **Package as zip**:
   ```bash
   zip -r my_plugin.zip my_plugin/
   ```

3. **Upload the zip** to a public URL (GitHub releases, raw.githubusercontent.com, etc.)

4. **Add entry to index.json** with your plugin metadata

5. **Submit a pull request** to this repository

### Plugin Structure

```
my_plugin/
├── __init__.py          # Main plugin file with Plugin class
├── helpers.py           # (Optional) Helper modules
└── requirements.txt     # (Optional) Python dependencies
```

### Example Plugin Class

```python
from plugin_base import PluginBase
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout

class Plugin(PluginBase):
    def get_name(self) -> str:
        return "My Cool Plugin"
    
    def get_icon(self) -> str:
        return "🔥"
    
    def get_version(self) -> str:
        return "1.0.0"
    
    def get_author(self) -> str:
        return "Your Name"
    
    def get_description(self) -> str:
        return "Does cool things when raids happen"
    
    def get_widget(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("My plugin settings here"))
        return widget
    
    def on_telegram_message(self, message: str):
        print(f"Raid alert: {message}")
```

## Security

⚠️ **Important**: Only install plugins from trusted sources! Plugins are Python code and can execute arbitrary commands on your system.

The app warns users before installation, but it's your responsibility to review plugin code before publishing.

## License

Plugins maintain their own licenses. Check each plugin's repository for details.
