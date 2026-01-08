# 🎮 Rust Auto-Connect Plugin

Automatically launch Rust and connect to your server when a raid alert is received. Never waste time loading the game manually—get straight into the action!

## Features
- **Instant Launch** - Opens Rust via Steam protocol the moment you get raided
- **Auto-Connect** - Joins your server automatically, no manual clicking
- **No Steam Path Needed** - Works as long as Steam is installed
- **Test Button** - Verify it works before relying on it

## Setup

### Step 1: Find Your Server Info

You need your server's IP address and port.

**Option A: From Rust Console**
1. Join your server in Rust
2. Press `F1` to open console
3. Type `client.connect` and hit Enter
4. You'll see something like: `Connecting to 192.168.1.50:28015`
5. Copy the IP and port

**Option B: From Server Browser**
1. Find your server in the Rust server list
2. Right-click → Copy IP address
3. Port is usually `28015` (default Rust port)

**Option C: From Discord/Website**
- Most servers list their connection info in Discord or on their website
- Format: `IP:PORT` (e.g., `play.myserver.com:28015`)

### Step 2: Configure the Plugin

1. Open RustPlus Raid Alarms
2. Go to the **Rust Auto-Connect** plugin tab
3. Enter your server info:
   - **Server IP**: Can be IP address (`192.168.1.50`) or domain (`play.example.com`)
   - **Server Port**: Usually `28015`

### Step 3: Test the Connection

1. Click **🎮 Test Connection** button
2. Rust should launch and connect to your server
3. If it works, enable the plugin checkbox!

## How It Works

When a raid alert is received:
1. Plugin checks if it's enabled
2. Validates server IP and port
3. Opens a `steam://run/252490//+connect%20IP:PORT` URL
4. Steam launches Rust with the connect command
5. Rust automatically joins your server

**Works even if Rust is already running** - it will just switch servers!

## Troubleshooting

### Nothing happens when I test

**Check Steam:**
- Make sure Steam is running and you're logged in
- Steam must be installed for the protocol handler to work

**Try manually:**
1. Open your browser
2. Paste this URL (replace with your server):
   ```
   steam://run/252490//+connect%20192.168.1.50:28015
   ```
3. If that doesn't work, Steam isn't registered properly

### Rust launches but doesn't connect

**Wrong server info:**
- Double-check your IP and port
- Make sure there are no spaces or typos
- Try joining manually first to verify the address works

**Server offline:**
- Plugin can't check if server is online
- It will try to connect regardless

### Plugin says "disabled" even though checkbox is on

**Restart the app:**
- Close RustPlus Raid Alarms completely
- Reopen it
- The plugin should now be enabled

## Tips

- **Keep Steam running** - The plugin can't launch Steam if it's closed
- **Already in-game?** - Plugin still works, just switches servers
- **Multiple servers?** - Change the IP/port as needed, no need to restart
- **AFK prevention** - Great for overnight raid defense!

## Configuration

Plugin settings are saved in `config.json`:

```json
{
  "rust_server_ip": "192.168.1.50",
  "rust_server_port": "28015",
  "plugin_enabled_Rust Auto-Connect": true
}
```

You can edit these manually if needed (close the app first).

## Common Server Ports

- **Default Rust port**: `28015`
- **Second server on same IP**: `28016`, `28017`, etc.
- **Modded servers**: Check their Discord/website

## Security Notes

- Server IP and port are **not sensitive** - they're public info
- No passwords or credentials are stored
- The plugin only launches Rust, doesn't modify game files
