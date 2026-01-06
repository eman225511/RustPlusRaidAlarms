# RustPlus Raid Alarms

Sleek, plugin-based desktop app that listens to Telegram for raid alarms and triggers customizable actions (e.g., LEDs). Drop in plugins—no code changes to the core.

## Features
- **Telegram listener** with polling rate control and optional keyword filter.
- **Auto-discovered plugins**: just add files/folders under `plugins/`.
- **Modern dark UI** with card/hero styling and left-side nav.
- **LED Controller plugin**: WLED, Govee, Philips Hue with presets/effects/color/brightness.
- **Example plugin** template showing UI, config, and Telegram hook.

## Quick start
1) Install deps
```bash
pip install -r requirements.txt
```
2) Configure Telegram (bot token + chat ID) via the in-app **Settings** (or edit `config.json`).
3) Run the app
```bash
python main.py
```

See `docs/TELEGRAM_SETUP.md` if you need help creating a bot and chat ID.

## Plugins
- Auto-loaded from `plugins/` every few seconds—no restart required.
- Single-file (`plugins/foo.py`) or package (`plugins/foo/__init__.py`) both work.
- Use relative imports inside plugin packages.
- Example: `plugins/example_plugin` shows config saving, message box, and Telegram handling.

Docs: `docs/PLUGIN_DEVELOPMENT.md`, `docs/LED_PLUGIN.md`, `docs/TELEGRAM_SETUP.md`, `docs/TROUBLESHOOTING.md`.

## LED Controller plugin (built-in)
- Targets: WLED, Govee, Philips Hue.
- Actions: on/off, color, effect, preset, scene (Govee), brightness.
- Brightness and color pickers, per-type settings (IP/API keys/models/bridge credentials).

## Config
- Stored in `config.json` (auto-created/merged on launch).
- Includes Telegram creds, polling rate, filter toggle/keyword, and LED settings.

## Project structure (key parts)
- `main.py` — app shell, plugin loader, Telegram service wiring, dark theme.
- `telegram_service.py` — polling thread + filter.
- `plugin_base.py` — Plugin contract.
- `plugins/` — all plugins (LED controller, example, your additions).
- `docs/` — docs for plugins and Telegram setup.

## Contributing
- Add new plugins under `plugins/` and they will appear automatically.
- Keep UI pieces within plugin widgets; avoid touching core unless necessary.
- If you add new dependencies, note them in `requirements.txt`.
