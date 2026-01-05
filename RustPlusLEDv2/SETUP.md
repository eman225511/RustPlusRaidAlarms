# Setup Guide

Follow these steps to set up the Rust+ Multi-LED Trigger App. The process takes about 10-15 minutes.

---

## Prerequisites

- **Python 3.7 or higher** installed on your computer
- **LED system**:
  - **WLED controller** connected to your local network, OR
  - **Govee smart LED devices** with WiFi connection, OR  
  - **Philips Hue system** (coming soon)
- **Rust+ app** installed on your phone with smart alarms configured in-game
- **Telegram account**
- **IFTTT account** (free tier is sufficient)

---

## Step 1: Install Python Dependencies

Open a terminal/command prompt in the project folder and run:

```bash
pip install -r requirements.txt
```

This installs the required packages:
- `python-telegram-bot` - Telegram Bot API
- `requests` - HTTP requests to LED devices
- `pillow` - Color picker support
- `PySide6` - GUI framework

---

## Step 2: Telegram Bot Setup

### 2.1 Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` command
3. Follow the prompts:
   - Choose a name for your bot (e.g., "Rust LED Trigger")
   - Choose a username (must end in 'bot', e.g., "rust_led_bot")
4. BotFather will give you a **Bot Token** - save this! (looks like `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)
5. Copy the bot token

### 2.2 Create a Telegram Channel

1. In Telegram, click the **New Message** button
2. Select **New Channel**
3. Choose a name (e.g., "Rust+ LED Notifications")
4. Make it **Private** (recommended for security)
5. Click **Create Channel**
6. Skip adding subscribers for now

### 2.3 Add Bots as Channel Administrators

1. In your new channel, click the **channel name** at the top
2. Click **Administrators**
3. Click **Add Administrator**
4. Search for and add **@IFTTT** bot
5. Give it permissions to **Post Messages**
6. Click **Save**
7. Repeat steps 3-6 to add **your bot** (the one you created in step 2.1)
8. Give your bot permissions to **Post Messages**

### 2.4 Get Your Channel ID

**Method 1 - Using @userinfobot (Recommended):**
1. Search for **@userinfobot** on Telegram
2. Forward any message from your channel to @userinfobot
3. It will reply with channel information including the **Chat ID** (starts with -100, like `-1001234567890`)
4. Save this Channel ID

**Method 2 - Using bot API:**
1. Post a test message in your channel
2. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. Look for `"chat":{"id":-100xxxxxxxxx}` in the response
4. Save the ID (including the minus sign)

---

## Step 3: IFTTT Applet Setup

### 3.1 Create the Applet

1. Go to [IFTTT](https://ifttt.com) and sign in
2. Click **Create** (top right)
3. Click **If This**
4. Search for and select **Rust+**
5. Choose a trigger (e.g., "Smart Alarm triggered")
6. Connect your Rust+ account if prompted
7. Select your server and smart alarm device
8. Click **Create Trigger**

### 3.2 Configure the Action

1. Click **Then That**
2. Search for and select **Telegram**
3. Choose **Send message**
4. Configure:
   - **Message text**: `Rust+ Alert: {{Title}} - {{Body}}`
   - **Target chat**: Use the chat with your bot
5. Click **Create Action**
6. Click **Continue** → **Finish**

**Note**: You may need to connect IFTTT to your Telegram account and authorize it to send messages to your bot.

### 3.3 Test the Applet

1. Trigger your Rust+ smart alarm in-game (or use the test button in IFTTT)
2. Check your Telegram bot chat - you should see a new message appear
3. If it works, you're ready to go!

---

## Step 4: LED System Configuration

Choose your LED system and follow the appropriate setup:

### Option A: WLED Setup

**WLED** is for DIY LED strips controlled by ESP32/ESP8266 microcontrollers.

1. Make sure your WLED device is powered on and connected to your network
2. Find its IP address (check your router, or use the WLED app)
3. Open a web browser and go to `http://[WLED_IP]` to verify it's accessible
4. (Optional) Configure presets and effects in WLED that you want to use
5. Note the IP address for use in the app

### Option B: Govee Setup

**Govee** smart LEDs can be controlled through their cloud API.

#### 4.1 Get Govee API Access

1. Go to https://developer.govee.com/
2. Create an account or sign in
3. Click **"Apply API Key"** 
4. Fill out the application form:
   - **Use case**: Personal home automation
   - **Company**: Personal (or your name)
   - **Reason**: LED control integration
5. Submit the application and wait for approval (usually 1-2 business days)
6. Once approved, you'll receive an **API Key** via email

#### 4.2 Find Your Govee Device Information

You have two options:

**Option 1: Use the App (Easier)**
1. Enter your API key in the Rust+ LED app
2. Click **"Get My Devices"** button
3. Select your device from the list
4. The app will automatically fill in Device ID and Model

**Option 2: Manual API Call**
1. Use a tool like Postman or curl to call the Govee API:
   ```bash
   curl -X GET "https://developer-api.govee.com/v1/devices/devices" \
        -H "Govee-API-Key: YOUR_API_KEY_HERE"
   ```
2. Find your device in the response and note:
   - `device` (MAC address like "AB:CD:EF:12:34:56:78:90")
   - `model` (like "H6163")
   - Make sure `controllable` is `true`

#### 4.3 Test Govee Connection

1. In the Rust+ LED app, go to Settings tab
2. Select **"Govee"** LED type
3. Enter your API Key, Device ID, and Model
4. Click **"Test LEDs"** button
5. Your Govee lights should respond

### Option C: Philips Hue Setup (Coming Soon)

Philips Hue integration will be added in a future update. The framework is already in place!

---

## Step 5: IFTTT Applet Setup

### 5.1 Create the Applet

1. Go to [IFTTT](https://ifttt.com) and sign in
2. Click **Create** (top right)
3. Click **If This**
4. Search for and select **Rust+**
5. Choose a trigger (e.g., "Smart Alarm triggered")
6. Connect your Rust+ account if prompted
7. Select your server and smart alarm device
8. Click **Create Trigger**

### 5.2 Configure the Action

1. Click **Then That**
2. Search for and select **Telegram**
3. Choose **Send message to channel**
4. Configure:
   - **Channel**: Select your newly created channel from the dropdown
   - **Message text**: `Rust+ Alert: {{Title}} - {{Body}}`
   - **Photo URL**: (leave blank)
5. Click **Create Action**
6. Click **Continue** → **Finish**

**Important Notes**: 
- Make sure you connected IFTTT to your Telegram account
- Verify that @IFTTT bot is an administrator in your channel
- The channel must allow posting from bots

### 5.3 Test the Applet

1. Trigger your Rust+ smart alarm in-game (or use the test button in IFTTT)
2. Check your Telegram bot chat - you should see a new message appear
3. If it works, you're ready to go!

---

## Step 6: Run the Application

1. In the project folder, run:
   ```bash
   python main.py
   ```

2. The GUI window will open

3. Configure your settings in the **Settings** tab:
   
   **LED Type Selection:**
   - Select **WLED**, **Govee**, or **Philips Hue** (when available)
   
   **For WLED:**
   - **WLED IP**: Enter your WLED controller's IP address
   
   **For Govee:**
   - **API Key**: Enter your Govee API key from developer.govee.com
   - **Device ID**: Enter your device MAC address (or use "Get My Devices")
   - **Model**: Enter your device model (or use "Get My Devices")
   
   **Telegram Settings:**
   - **Bot Token**: Paste the bot token from BotFather
   - **Chat ID**: Paste your channel ID from step 2.4 (starts with -100)

4. In the **Control** tab, choose your action on trigger:
   
   **Universal Actions** (all LED types):
   - **Turn ON**: Turns lights on
   - **Turn OFF**: Turns lights off
   - **Set Color**: Changes to a specific color (click "Pick Color" to choose)
   
   **WLED-Specific Actions:**
   - **Set Effect**: Runs a WLED effect (enter effect number 0-255)
   - **Run Preset**: Activates a saved WLED preset (enter preset number)
   
   **Govee-Specific Actions:**
   - **Run Scene**: Activates a Govee scene preset (enter scene number)
   - **Set Brightness**: Sets brightness level (1-100%)

5. Click **Save Settings**

6. Click **Test LEDs** to verify your configuration works

7. The status will show "Waiting for Rust+ trigger..."

8. Trigger a Rust+ smart alarm - you should receive a Telegram message and your lights should respond!

---

## Step 7: Running in the Background

### Option A: Keep the Window Open
Simply minimize the window and let it run while you play Rust.

### Option B: Run as a Background Process (Advanced)
For Windows, create a `.vbs` script to run it silently:

Create `run_hidden.vbs`:
```vbscript
Set objShell = CreateObject("WScript.Shell")
objShell.Run "python main.py", 0, False
```

Double-click the `.vbs` file to run the app without a visible window.

---

## Troubleshooting

### "ERROR: Telegram bot token or chat ID not set!"
- Make sure you've entered both the bot token and channel ID in the app
- Verify you copied them correctly (no extra spaces)
- Channel ID must start with -100 (e.g., -1001234567890)

### "Telegram error" messages
- Verify your bot token is correct
- Make sure your bot is an administrator in the channel
- Make sure @IFTTT bot is also an administrator in the channel
- Check that your channel ID is correct and starts with -100

### IFTTT applet not triggering
- Check that your Rust+ alarm is properly configured in-game
- Verify the IFTTT applet is enabled (toggle it off and on)
- Make sure IFTTT is connected to your Telegram account
- Verify @IFTTT bot has "Post Messages" permission in your channel
- Check IFTTT activity log to see if the applet is running

### Govee API issues
- Verify your API key is correct and approved
- Check that your device is online in the Govee app
- Make sure the device is controllable (some older models may not support API control)
- Verify Device ID and Model are correct (use "Get My Devices" button)

### Lights not responding
- **WLED**: Test manually by visiting `http://[WLED_IP]` in a browser
- **Govee**: Test using the official Govee app first
- Check effect/preset/scene numbers are valid
- Look for error messages in the app's status label

---

## Tips for Best Experience

### WLED Users
- **Create multiple LED presets** in WLED for different scenarios (raid alert, door breach, etc.)
- **Effect numbers** can be found in your WLED web interface (typically 0-100+)

### Govee Users  
- **Scene numbers** correspond to your presets in the Govee app
- **Test different scenes** to find the best ones for alerts
- **Brightness control** works independently of scenes

### General Tips
- **Test your setup** before a raid by manually triggering alarms
- **Keep the app running** whenever you're playing Rust for real-time notifications
- **Multiple LED types** can be configured for different situations

---

## Next Steps

Once everything is working:
1. Set up multiple smart alarms in Rust (doors, turrets, vending machines, etc.)
2. Create multiple IFTTT applets for different alarm types
3. Experiment with different LED effects, colors, and scenes
4. Try different LED systems for various rooms or setups
5. Enjoy your immersive lighting setup!

Happy raiding! 🎮💡

