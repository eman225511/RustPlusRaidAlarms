<div align="center">

# 🌐 Relay Server Mode Guide

**Share alerts with your clan - only ONE person needs Telegram setup!**

[![Server Mode](https://img.shields.io/badge/Mode-Relay%20Server-brightgreen?style=for-the-badge)](https://github.com/eman225511/RustPlusRaidAlarms)
[![Ngrok](https://img.shields.io/badge/Tunnel-Automatic-blue?style=for-the-badge)](https://ngrok.com)

</div>

---

## 🎯 What is Relay Server Mode?

Instead of everyone setting up their own Telegram bot:
- ✅ **ONE person** runs the app in "Server Mode" (connects to Telegram)
- ✅ **Everyone else** connects to that person's relay server
- ✅ **Automatic tunneling** - no port forwarding needed (uses ngrok)
- ✅ **All clan members** receive the same raid alerts instantly

---

## 📋 Quick Start

### **Person 1 (Server Host):**

1. **Setup Telegram bot** (one-time, follow main setup guide)
2. **Enable Server Mode:**
   - Go to "Core" tab
   - Check ✅ "Enable Server Mode"
   - Wait 10-20 seconds for ngrok tunnel to start
3. **Export Server Code:**
   - Click "👥 Clan Codes" button
   - Select "🌐 Export Server Code (Relay)"
   - Copy the code shown in the dialog
4. **Share the code** with your clan members

### **Everyone Else (Clients):**

1. **Download and run the app** (no Telegram setup needed!)
2. **Import Server Code:**
   - Click "👥 Clan Codes" button
   - Select "🌐 Import Server Code (Relay)"
   - Paste the code you received
3. **Done!** You're now connected to the relay server

---

## 🔧 How It Works

```
┌─────────────┐
│   IFTTT     │ (Rust+ raid detection)
└──────┬──────┘
       │
       v
┌─────────────┐
│  Telegram   │ (raid alert message)
└──────┬──────┘
       │
       v
┌─────────────────────┐
│  Person 1 (Server)  │ ← Runs Server Mode
│  - Telegram Bot     │
│  - Relay Server     │
│  - Ngrok Tunnel     │
└──────┬──────────────┘
       │
       ├──────────────────────┐
       │                      │
       v                      v
┌─────────────┐      ┌─────────────┐
│ Person 2    │      │ Person 3    │
│ (Client)    │      │ (Client)    │
└─────────────┘      └─────────────┘
```

---

## ⚙️ Server Status Indicators

| Status | Meaning |
|--------|---------|
| `✓ Server running on port 5555` | Server started locally |
| `✓ Public URL: X.tcp.ngrok.io:XXXXX` | Ngrok tunnel ready - shareable! |
| `✓ 3 client(s) connected` | Number of clan members connected |
| `⚠ ngrok not installed` | Install with `pip install pyngrok` |

---

## 🛠️ Troubleshooting

### Server won't start
- ✅ Make sure port 5555 isn't in use
- ✅ Check firewall isn't blocking the app
- ✅ Ensure `pyngrok` is installed: `pip install pyngrok`

### Clients can't connect
- ✅ Server host must keep app running
- ✅ Wait 10-20 seconds after enabling Server Mode for ngrok
- ✅ Export a fresh server code if tunnel URL changed
- ✅ Check you copied the ENTIRE server code (it's JSON)

### Ngrok tunnel issues
- ✅ Free ngrok has 40 connections/min limit (plenty for clans)
- ✅ Tunnels reset when app restarts (just export new code)
- ✅ If ngrok fails, clients can use local IP on same network

---

## 💡 Tips & Best Practices

### For Server Hosts:
- 🖥️ **Keep app running** - clients depend on you
- 🔄 **Restart = new code** - export fresh code after restarts
- 📊 **Monitor connections** - see who's connected in status
- 🌐 **Local network** - clan members on same WiFi can use local IP

### For Clients:
- 📱 **Reconnect if server restarts** - just import code again
- ⚡ **Lightweight** - no Telegram polling, just relay connection
- 🔌 **Always connected** - real-time alerts from server

---

## 🆚 Server Mode vs. Clan Codes (Telegram)

| Feature | Server Mode 🌐 | Clan Codes 📱 |
|---------|----------------|---------------|
| Setup complexity | One person | Everyone |
| Telegram bot needed | One shared | One shared |
| Conflicts | None | Can happen with polling |
| Internet needed | Server host only | Everyone |
| Best for | Clans, teams | Personal sharing |

---

## 🔐 Security

- 🔒 **No encryption on relay** - don't send sensitive data through Telegram
- 🌐 **Ngrok tunnels** - randomly generated, temporary URLs
- 👥 **No authentication** - anyone with code can connect (share carefully)
- 🛡️ **Firewall** - server opens port 5555 locally (ngrok handles public)

---

## 📚 Advanced: Local Network Only

Don't want to use ngrok? Use local IPs for LAN parties or home networks:

1. Enable Server Mode (ngrok will fail, that's OK)
2. Find your local IP: `ipconfig` (Windows) or `ifconfig` (Mac/Linux)
3. Share your IP manually: `192.168.1.X:5555`
4. Clan members manually create code:
```json
{"type":"relay_server","url":"192.168.1.X:5555","version":1}
```

---

<div align="center">

### Need Help?

[📖 Main README](../README.md) • [💬 Issues](https://github.com/eman225511/RustPlusRaidAlarms/issues)

**Made with ❤️ for the Rust community**

</div>
