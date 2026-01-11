# Plugin Development Guide

This app discovers plugins from the `plugins/` folder automatically. Drop in a Python file or a package (folder with `__init__.py`) and it will be picked up at runtime—no manual imports required.

## Plugin contract
- Implement a class named `Plugin` that inherits from `plugin_base.PluginBase`.
- Required methods:
  - `get_name(self) -> str`: Display name for the sidebar.
  - `get_icon(self) -> str`: Small emoji/text icon shown beside the name.
  - `get_description(self) -> str`: Short description.
  - `get_widget(self) -> QWidget`: Returns your plugin's root widget (build lazily and cache it).
  - `on_telegram_message(self, message: str)`: Called for every Telegram message that passes filters.
- Recommended metadata (used by the Plugin Store for update checks):
    - `get_version(self) -> str`
    - `get_author(self) -> str`
    - `get_homepage(self) -> str`

## Auto-discovery
- Plugins live under `plugins/`.
- Single file: `plugins/foo.py` with class `Plugin`.
- Package: `plugins/foo/__init__.py` with class `Plugin`.
- The app scans every ~5 seconds and loads new plugins without restart.
- The module name is `plugins.<folder or filename>`; use relative imports inside packages (e.g., `from .utils import helper`).

## Styling guidance
- The app applies a global dark theme. Use lightweight, semantic widgets and avoid hard-coded colors when possible.
- For card-like sections, set `QFrame` objectName to `"card"` or `"heroCard"` to inherit the main styles.
- Prefer `QVBoxLayout` / `QHBoxLayout` with `setContentsMargins` and `setSpacing` for tidy spacing.
- Fonts: use `QFont("Segoe UI", size, weight)` for consistency.
- Buttons: minimum height ~36–42px feels good; rely on inherited palette rather than custom colors unless needed.

## Config and state
- `self.config` is a shared dict persisted by the main app.
- Read defaults with `self.config.get("key", default)`.
- Update values in your UI handlers, then call `self.config[...] = value`; the app persists on save (or you can call main `save_config` if exposed). The example plugin shows inline persistence.
- Per-plugin enable/disable: the main UI has a checkbox beside each plugin; users can turn your plugin off without removing it.
- Example plugins visibility: hidden by default; users must enable "Show Example Plugins (For Devs)" to see them.

## Telegram hook
- `on_telegram_message(self, message: str)` is invoked on every incoming Telegram message (post-filter). Use it to trigger actions. Keep handlers fast; offload long work to threads if needed.

## Example walkthrough

### Package-based Plugin (Advanced)
See `plugins/example_plugin/__init__.py` for a full-featured reference including:
- Hero card UI with title and subtitle
- Reading/saving text settings to `self.config`
- Showing `QMessageBox` dialogs
- Reacting to Telegram messages with hooks
- Status labels and user feedback
- Multiple UI cards and sections

### Single-file Plugin (Simple)
See `plugins/simple_example.py` for a minimal single-file example including:
- Basic card UI with title and subtitle
- Click counter with config persistence
- Name input field with save functionality
- Simple button interactions
- Reacting to Telegram messages

**Note**: Example plugins are hidden by default. Enable "Show Example Plugins (For Devs)" in the navigation sidebar to view them.

## Publishing to the Plugin Store

1. **Add metadata methods**: implement `get_version`, `get_author`, and `get_homepage` so the store can display and compare versions.
2. **Package your plugin**:
    - Single-file: zip the `.py` (e.g., `zip my_plugin.zip my_plugin.py`).
    - Package: zip the folder contents (keep `__init__.py` at the root of the zip).
3. **Host the zip** on a public URL (GitHub Release asset, raw GitHub link, etc.).
4. **Add to `plugins/index.json`** with: `id`, `name`, `icon`, `version`, `author`, `description`, `homepage`, `download_url`, `min_app_version`, `category`, `tags`, `requires`, `size_kb`.
5. **Open a PR** to this repo updating `plugins/index.json` (and a short README for your plugin if desired).
6. **Versioning**: bump `get_version` and the `index.json` version together so users see the Update button.

## Minimal skeleton
```python
from plugin_base import PluginBase
from PySide6.QtWidgets import QWidget

class Plugin(PluginBase):
    def __init__(self, telegram_service, config):
        super().__init__(telegram_service, config)
        self.widget = None

    def get_name(self):
        return "My Plugin"

    def get_icon(self):
        return "🧩"

    def get_description(self):
        return "Does something cool"

    def get_widget(self) -> QWidget:
        if self.widget is None:
            self.widget = QWidget()  # build your UI here
        return self.widget

    def on_telegram_message(self, message: str):
        print(f"Got message: {message}")
```

## Common tips
- Use relative imports inside plugin packages to avoid import errors.
- Guard long-running work; keep UI responsive.
- Log with `print(...)` for quick debugging; the main log captures stdout.
- If you add external dependencies, document them; the app does not auto-install extras.
