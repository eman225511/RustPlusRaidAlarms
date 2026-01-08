<div align="center">

# 🔊 Audio Alert Plugin

**Custom Sound Alerts for Raids**

[![MP3](https://img.shields.io/badge/MP3-Supported-blue?style=flat)](https://en.wikipedia.org/wiki/MP3)
[![WAV](https://img.shields.io/badge/WAV-Supported-green?style=flat)](https://en.wikipedia.org/wiki/WAV)
[![OGG](https://img.shields.io/badge/OGG-Supported-orange?style=flat)](https://en.wikipedia.org/wiki/Ogg)
[![FLAC](https://img.shields.io/badge/FLAC-Supported-purple?style=flat)](https://en.wikipedia.org/wiki/FLAC)

Play custom sound files on any audio device when you get raided!

</div>

---

## ✨ Features

<details open>
<summary><b>What this plugin can do</b></summary>

| Feature | Description |
|---------|-------------|
| 🎵 **Custom Sounds** | Use any MP3, WAV, OGG, or FLAC file |
| 📦 **Multiple Files** | Add unlimited audio alerts |
| 🔈 **Device Selection** | Play on specific speakers/headphones |
| 🔉 **Volume Control** | Adjust from 0-100% |
| ▶️ **Test Playback** | Preview sounds before enabling |

</details>

---

## 🛠️ Setup

<details open>
<summary><b>5-step configuration guide</b></summary>

### 1️⃣ Prepare Your Audio Files

**Choose or create audio files:**

| Category | Examples | Purpose |
|----------|----------|---------|
| 🚨 **Alarm Sounds** | Air horn, siren, klaxon | Wake-up alerts |
| 🎤 **Voice Alerts** | "RAID ALERT!", "Get online NOW!" | Personal messages |
| 🎵 **Music** | Heavy metal, pump-up songs | Motivational |
| 🎮 **Game SFX** | Rust gunfire, explosions | Immersive |
| 😂 **Memes** | "Oh no no no", Inception horn | Entertainment |

**Supported formats:**

| Format | Quality | File Size | Best For |
|--------|---------|-----------|----------|
| ✅ **MP3** | Good | Small | Most common, widely compatible |
| ✅ **WAV** | Excellent | Large | Best quality, no compression |
| ✅ **OGG** | Good | Smaller | Compressed, efficient |
| ✅ **FLAC** | Lossless | Medium | Audiophile-grade quality |

**Save files somewhere accessible:**
- 📁 Example: `C:\Users\YourName\Music\Alarms\`
- 📁 Or in project: `RustPlusRaidAlarms\sounds\`

---

### 2️⃣ Configure Audio Devices

1. Open **RustPlus Raid Alarms**
2. Go to **Audio Alert** plugin tab  
3. Click **🔍 Scan Audio Devices** button
4. **Check the devices** you want to use:

| Device Type | Use Case |
|-------------|----------|
| 🔊 **Speakers** | Main alert (wake up whole room) |
| 🎧 **Headphones** | Personal notification |
| 📡 **Virtual Cable** | Stream alert (if streaming) |
| 📺 **HDMI/Monitor** | TV/monitor speakers |
| 🔵 **Bluetooth** | Wireless speakers |

> 💡 **Multi-device**: Select multiple devices to play on all simultaneously!

---

### 3️⃣ Add Audio Files

1. Click **📁 Browse...** next to an empty file path
2. Navigate to your audio file
3. File path auto-fills
4. Repeat for additional files (up to 5+ per set)

**Quick Tip**: Copy-paste paths if you know them:
```
C:\Users\YourName\Music\Alarms\airhorn.mp3
```

---

### 4️⃣ Set Volume

**Slider**: Drag for quick adjustments (0-100%)  
**Number box**: Type specific value

| Volume | Effect |
|--------|--------|
| 🔉 **50-70%** | Noticeable but not jarring |
| 🔊 **80-100%** | Wake-you-up loud |
| 📢 **100%** | MAXIMUM ALERT 🚨 |

> ⚠️ Volume applies to **all** audio files

---

### 5️⃣ Test It

1. Click **▶️ Play Audio** button
2. All files play on all selected devices
3. Adjust volume/devices as needed
4. ✅ When happy, enable the plugin checkbox!

</details>

---

## ⚙️ How It Works

<details>
<summary><b>Behind the scenes</b></summary>

When a raid alert is received:

```
1. ✅ Plugin checks if enabled
2. 📁 Validates audio files exist
3. 🧵 Starts background thread per file
4. 🔊 Plays all files simultaneously on selected devices
5. ⏹️ Auto-stops when finished
```

**Background playback** - Won't freeze the app!

</details>

---

## 🔧 Audio Device Selection

<details>
<summary><b>Understanding audio devices</b></summary>

### 📋 Device Types

| Device | Description | Example |
|--------|-------------|---------|
| 🔊 **Physical speakers** | Actual hardware | Logitech, JBL |
| 🎧 **Headphones** | Wired/wireless audio | HyperX, Sony |
| 📺 **HDMI/DisplayPort** | Monitor speakers | Dell monitor audio |
| 🔵 **Bluetooth** | Wireless devices | AirPods, Bose |
| 📡 **Virtual devices** | Software mixers | VoiceMeeter, VB-Cable |

### 🔄 Duplicate Devices

Some devices appear multiple times with different drivers (MME, DirectSound, WASAPI).  
**The plugin automatically filters duplicates by name.**

### 🔍 Can't Find Your Device?

| Issue | Solution |
|-------|----------|
| 📋 Empty list | Click **🔍 Scan Audio Devices** again |
| 🔌 Not detected | Ensure device is plugged in and powered on |
| 🪟 Windows missing it | Check Windows Sound Settings |
| 🔄 Still missing | Update audio drivers<br>Restart app<br>Restart computer (for Bluetooth) |

</details>

---

## 🔧 Troubleshooting

<details>
<summary><b>Common issues and solutions</b></summary>

### 🔇 No Sound Plays

| Cause | Fix |
|-------|-----|
| ☑️ **No device selected** | At least one device must be checked<br>Click **🔍 Scan Audio Devices** if list empty |
| 📁 **Missing files** | Verify file paths are correct<br>Files must exist at specified location<br>Test in VLC/Windows Media Player first |
| 🔊 **Volume zero** | Plugin volume must be > 0%<br>Windows volume must be > 0%<br>Device must not be muted |

---

### 📂 "Error: File not found"

| Problem | Solution |
|---------|----------|
| 📁 **File moved** | Browse to new location |
| ✏️ **Wrong path** | Windows: Use `C:\Users\...` (backslashes)<br>Or forward slashes: `C:/Users/...` |

---

### 🔍 "Error scanning devices"

**Restart the plugin:**
1. Disable the plugin checkbox
2. Wait 2 seconds
3. Enable it again
4. Click **🔍 Scan Audio Devices**

**Still broken?**
- Check if other apps can use audio (Spotify, YouTube)
- Restart RustPlus Raid Alarms
- Reinstall packages: `pip install --upgrade pygame sounddevice`

---

### 📢 Sound Distorted/Crackling

| Issue | Fix |
|-------|-----|
| 🔊 **Too loud** | Lower volume (try 70% instead of 100%)<br>Speakers might be clipping |
| 🎵 **Low quality file** | Use WAV or high-quality MP3 (320kbps) |
| 📡 **Too many devices** | Playing on 5+ devices can cause issues<br>Try using fewer devices |

---

### 🔁 Audio Keeps Playing After Raid Ends

| Cause | Fix |
|-------|-----|
| 🧵 **Background thread** | Close and reopen RustPlus Raid Alarms<br>Plugin stops all playback on shutdown |
| 🔂 **File looping** | Check file metadata for loop markers<br>Re-export file with no loop |

</details>

---

## 📁 File Organization Tips

<details>
<summary><b>Recommended folder structure and resources</b></summary>

### 🗂️ Folder Structure

```
RustPlusRaidAlarms/
├── sounds/
│   ├── alerts/
│   │   ├── airhorn.mp3
│   │   ├── siren.wav
│   │   └── alarm.mp3
│   ├── voice/
│   │   ├── raid_alert.mp3
│   │   └── get_online.wav
│   └── memes/
│       ├── inception.mp3
│       └── ohdear.wav
```

### 🌐 Free Sound Libraries

| Resource | Link | Description |
|----------|------|-------------|
| 🔊 **Freesound** | [freesound.org](https://freesound.org/) | Huge library of CC-licensed sounds |
| ⚡ **Zapsplat** | [zapsplat.com](https://www.zapsplat.com/) | Free SFX and music |
| 🎬 **Mixkit** | [mixkit.co](https://mixkit.co/free-sound-effects/) | High-quality free sounds |

### 🎙️ Record Your Own

| Tool | Platform | Cost |
|------|----------|------|
| 🪟 **Voice Recorder** | Windows built-in | Free |
| 🎵 **Audacity** | All platforms | Free, open source |
| 📱 **Phone recorder** | iOS/Android | Built-in |

### 🔄 Convert Formats

- 🎵 [Audacity](https://www.audacityteam.org/) - Convert between formats
- 🌐 [Online-Convert.com](https://audio.online-convert.com/) - Quick conversions

</details>

---

## 📝 Configuration

<details>
<summary><b>Config file format</b></summary>

Plugin settings saved in `config.json`:

```json
{
  "audio_files": [
    "C:/Users/YourName/Music/airhorn.mp3",
    "C:/Users/YourName/Music/siren.wav"
  ],
  "audio_volume": 80,
  "selected_audio_devices": [
    "Speakers (Realtek High Definition Audio)",
    "Headphones (USB Audio Device)"
  ],
  "plugin_enabled_Audio Alert": true
}
```

</details>

---

## 🚀 Advanced Features

<details>
<summary><b>Sequential playback and performance notes</b></summary>

### 🔄 Sequential Playback

The plugin plays all files **simultaneously** by default.

Want **one after another** instead? Edit `plugins/audio_alert.py`:

```python
# In on_telegram_message() method
for audio_file in self.audio_files:
    thread = AudioPlaybackThread(audio_file, self.audio_volume, device_indices)
    thread.start()
    thread.wait()  # ⬅️ Add this line to wait for completion
```

### 📊 Performance Notes

| Metric | Usage |
|--------|-------|
| 💾 **Memory** | ~10-50MB per audio file |
| ⚡ **CPU** | < 5% during playback |
| 📁 **Multiple files** | No significant impact |

### 🔒 Privacy & Security

- 🌐 **No network access** - All audio plays locally
- 🔍 **No telemetry** - Plugin doesn't track usage
- 📄 **Config file** - Contains file paths only (safe to share)

</details>

---

<div align="center">

**[⬅️ Back to Main README](../../README.md)** • **[📖 All Plugin Guides](../../README.md#-plugins)**

Made with ❤️ for the Rust community

</div>
