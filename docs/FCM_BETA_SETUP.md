# Beta FCM Feature - Setup Instructions

## Overview
The FCM (Firebase Cloud Messaging) beta feature allows you to receive Rust+ notifications directly without using Telegram. This mode bypasses Telegram entirely and connects directly to Rust+ servers, similar to the official companion app.

## Requirements

### 1. Python Dependencies
Install the required packages:
```bash
pip install flask rustplus
```

Or install all requirements:
```bash
pip install -r requirements.txt
```

### 2. Node.js and npm
The FCM setup requires Node.js for initial authentication:
- Download and install Node.js from: https://nodejs.org/
- Verify installation: `node --version` and `npm --version`

## How to Use

### First Time Setup
1. **Open the Beta Features Tab**
   - Launch the application
   - Click on "🧪 Beta Features" in the navigation sidebar

2. **Authenticate with Steam**
   - Click "🔐 Authenticate with Steam"
   - A browser window will open for Steam login
   - Login with your Steam account
   - The app will automatically:
     - Receive your auth token
     - Run Node.js scripts to setup FCM credentials
     - Register your device for push notifications

3. **Start FCM Mode**
   - Once authenticated (status shows "✓ Authenticated")
   - Click "▶️ Start FCM Mode"
   - This will:
     - Stop Telegram service if running
     - Disconnect from relay server if connected
     - Start listening for FCM notifications

4. **Pair with Rust Server**
   - Open Rust game
   - Use the Rust+ companion app pairing flow
   - Notifications will be received directly

### Switching Between Modes

**You can only use ONE mode at a time:**
- **Telegram Mode** - Uses Telegram bot for notifications
- **Relay Mode** - Connects to a relay server
- **FCM Mode** - Direct Rust+ notifications (Beta)

To switch modes:
- From FCM to Telegram: Click "🔄 Switch to Telegram Mode" in Beta tab
- From Telegram to FCM: Go to Beta tab and click "▶️ Start FCM Mode"

## Features

### Keyword Filtering
- Works exactly like Telegram mode
- Configure in the Core tab settings
- Filters notifications by keyword before forwarding to plugins

### Plugin Support
- All plugins receive FCM notifications just like Telegram messages
- No code changes needed in plugins
- Enable/disable plugins as normal

### Persistent Authentication
- Credentials are saved in:
  - `rustplus_token.json` - Auth token and Steam ID
  - `rustplus.config.json` - FCM credentials
  - `seen_notifications.json` - Prevents duplicate notifications

### Auto-Resume
- If FCM mode is active when you close the app
- It will automatically resume on next launch (if authenticated)

## Troubleshooting

### "Not authenticated" error
- Click "🔐 Authenticate with Steam" again
- Make sure Node.js is installed
- Check console logs for errors

### Node.js not found
- Install Node.js from https://nodejs.org/
- Restart the application after installing
- Try re-authenticating

### No notifications received
- Make sure FCM mode is started (listener status shows "✓ FCM listener active")
- Check that you're paired with a Rust server in-game
- Verify keyword filter isn't blocking notifications
- Check notification count in Beta tab

### Switch back to Telegram
- Click "🔄 Switch to Telegram Mode" in Beta tab
- Or manually disable FCM mode and restart Telegram service

## Technical Details

### How It Works
1. Authenticates with Steam Companion API
2. Uses Node.js to setup Firebase Cloud Messaging credentials
3. Registers device with Expo push notifications
4. Listens for FCM notifications using rustplus library
5. Parses notifications and forwards to plugins

### Files Created
- `rustplus_token.json` - Contains auth token and Steam ID
- `rustplus.config.json` - Contains FCM credentials and Expo token
- `seen_notifications.json` - Tracks processed notification IDs
- `scripts/` - Node.js helper scripts for FCM setup

### Security
- Credentials are stored locally only
- No data is sent to third parties
- Uses same authentication as official Rust+ app

## Known Limitations
- Beta feature - may have bugs
- Requires Node.js for initial setup
- Cannot use simultaneously with Telegram or Relay mode
- Authentication expires and may need to be refreshed periodically

## Support
If you encounter issues:
1. Check the Logs tab for error messages
2. Try re-authenticating
3. Ensure Node.js and npm are properly installed
4. Verify internet connection

## Credits
- Based on TestAuthFlow implementation
- Uses @liamcottle/rustplus.js for FCM setup
- rustplus Python library for FCM listening
