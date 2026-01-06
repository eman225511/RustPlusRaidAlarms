# Troubleshooting

Common issues and quick fixes.

## Telegram
- **Invalid token format**: Must contain one colon (`:`). Regenerate via @BotFather.
- **Chat ID wrong**: Channel IDs start with `-100`. Use @userinfobot or `getUpdates` to confirm.
- **Status stays red**: Ensure the bot is admin and can post; check internet connectivity.
- **Missed messages**: Make sure polling rate isn’t too high (default 2s) and filters aren’t blocking your keywords.

## Plugins
- **Plugin doesn’t appear**: Verify file/package is under `plugins/`, class name is `Plugin`, and imports are relative inside the package.
- **Import errors**: Use `from .module import Thing` inside plugin packages; avoid absolute imports.
- **UI not updating**: Ensure you return the same cached widget from `get_widget` or refresh your layout explicitly.

## LED plugin
- **No effect/preset trigger**: Confirm WLED IP reachable; open `http://<ip>/json/info` in a browser.
- **Govee scene fails**: Check API key, device ID, model; ensure scene ID is valid for the device.
- **Hue won’t set color**: Verify bridge IP/username; light ID defaults to 1 in code.

## Environment
- **Missing dependencies**: Run `pip install -r requirements.txt` in your virtualenv.
- **Multiple Python versions**: Activate the project venv before running (`.venv/Scripts/Activate.ps1`).

## Logging
- The main window activity log shows recent events.
- `print()` in plugins writes to stdout; check terminal for stack traces.
