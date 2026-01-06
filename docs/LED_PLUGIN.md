# LED Controller Plugin

The built-in LED plugin can trigger WLED, Govee, or Philips Hue lights when Telegram messages arrive.

## Supported systems
- **WLED**: presets, effects, color, brightness
- **Govee**: on/off, color, scene, brightness
- **Philips Hue**: on/off, color, brightness

## Actions
- **On / Off**: Power toggle.
- **Color**: Set color (hex) via color picker.
- **Effect (WLED)**: Run effect by numeric ID.
- **Preset (WLED)**: Run preset by numeric ID.
- **Scene (Govee)**: Run scene by numeric ID/code.
- **Brightness**: Percentage (converted to 0–255 for WLED).

## Fields by system
- **WLED**: IP address, action, effect #, preset #, color, brightness.
- **Govee**: API key, device ID, model, scene #, brightness, color.
- **Hue**: Bridge IP, username, brightness, color.

## Usage
1. Pick LED type (WLED/Govee/Hue).
2. Fill connection fields (IP or API credentials).
3. Choose an action and set parameters (color/effect/preset/scene/brightness).
4. Click **Save Settings**.
5. Click **Test LEDs** to verify.
6. When Telegram messages arrive, the selected action runs.

## Notes
- Brightness always applies for WLED effect/preset/color.
- Govee scenes require valid scene IDs supported by the device.
- Hue uses RGB→Hue conversion under the hood.

## Troubleshooting
- Ensure IP/API credentials are correct.
- For WLED, open `http://<ip>/json/info` in a browser to verify reachability.
- For Govee, verify the device is online and API key is correct.
- For Hue, ensure the username/bridge IP are valid and the light ID is the default (1) unless changed in code.
