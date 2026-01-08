# 🔊 Audio Alert Plugin

Play custom sound files on any audio output device when you get raided. Wake up to your favorite alarm sound, scare your cat, or blast air horns through your speakers!

## Features
- **Custom Sounds** - Use any MP3, WAV, OGG, or FLAC file
- **Multiple Files** - Add unlimited audio alerts
- **Device Selection** - Play on specific speakers/headphones
- **Volume Control** - Adjust from 0-100%
- **Test Playback** - Preview sounds before enabling

## Setup

### Step 1: Prepare Your Audio Files

1. Choose or create audio files:
   - **Alarm sounds**: Air horn, siren, klaxon
   - **Voice alerts**: Record yourself saying "RAID ALERT!"
   - **Music**: Heavy metal, pump-up songs, memes
   - **Game sounds**: Rust gunfire, explosion SFX

2. Supported formats:
   - ✅ MP3 (most common)
   - ✅ WAV (best quality)
   - ✅ OGG (smaller file size)
   - ✅ FLAC (lossless)

3. Save files somewhere accessible:
   - Example: `C:\Users\YourName\Music\Alarms\`
   - Or keep them in the project: `RustPlusRaidAlarms\sounds\`

### Step 2: Configure Audio Devices

1. Open RustPlus Raid Alarms
2. Go to **Audio Alert** plugin tab
3. Click **Scan Audio Devices** button
4. Check the devices you want to use:
   - ✅ Speakers - Main alert
   - ✅ Headphones - Personal notification
   - ✅ Virtual Cable - Stream alert (if you're streaming)

**Tip**: You can select multiple devices to play on all of them simultaneously!

### Step 3: Add Audio Files

1. Click **Browse...** next to an empty file path
2. Navigate to your audio file
3. File path will be auto-filled
4. Repeat for additional files (up to 5 per set)

**Quick Tip**: Copy-paste file paths if you know them:
```
C:\Users\YourName\Music\Alarms\airhorn.mp3
```

### Step 4: Set Volume

1. Use the **slider** for quick adjustments (0-100%)
2. Or type a **specific number** in the box
3. Volume applies to all audio files

**Recommended volumes**:
- **50-70%**: Noticeable but not jarring
- **80-100%**: Wake-you-up loud
- **100%**: MAXIMUM ALERT 🚨

### Step 5: Test It

1. Click **▶ Play Audio** button
2. All configured files will play on all selected devices
3. Adjust volume/devices as needed
4. When happy, enable the plugin checkbox!

## How It Works

When a raid alert is received:
1. Plugin checks if it's enabled
2. Validates audio files exist
3. Starts a background thread for each file
4. Plays all files simultaneously on selected devices
5. Automatically stops when finished

**Plays in background** - Won't freeze the app during playback!

## Audio Device Selection

### What are these devices?

- **Physical speakers/headphones**: Your actual hardware
- **Virtual audio devices**: Software mixers (VoiceMeeter, VB-Cable, etc.)
- **HDMI/DisplayPort audio**: Monitor speakers
- **Bluetooth devices**: Wireless speakers/headphones

### Duplicate devices?

Some devices appear multiple times with different drivers (MME, DirectSound, WASAPI). The plugin automatically filters duplicates by name.

### Can't find your device?

**Refresh the list:**
1. Click **Scan Audio Devices** again
2. Make sure the device is plugged in and powered on
3. Check Windows Sound Settings to see if Windows detects it

**Device not showing?**
- Update audio drivers
- Restart RustPlus Raid Alarms
- Restart your computer (for new Bluetooth devices)

## Troubleshooting

### No sound plays

**Check device selection:**
- At least one device must be checked
- Click **Scan Audio Devices** if list is empty

**Check audio files:**
- Make sure file paths are correct
- Files must exist at the specified location
- Try playing the file in VLC/Windows Media Player first

**Check volume:**
- Plugin volume must be > 0%
- Windows volume must be > 0%
- Device must not be muted

### "Error: File not found"

**File path changed:**
- Did you move/rename/delete the audio file?
- Browse to the new location

**Wrong path format:**
- Windows: Use backslashes `C:\Users\...`
- Or forward slashes work too: `C:/Users/...`

### "Error scanning devices"

**Restart the plugin:**
1. Disable the plugin checkbox
2. Wait 2 seconds
3. Enable it again
4. Click **Scan Audio Devices**

**Still broken?**
- Check if other apps can use audio (Spotify, YouTube, etc.)
- Restart RustPlus Raid Alarms
- Reinstall `pygame` and `sounddevice`: `pip install --upgrade pygame sounddevice`

### Sound plays but is distorted/crackling

**Lower the volume:**
- Try 70% instead of 100%
- Your speakers might be clipping

**Check file quality:**
- Low bitrate MP3s can sound bad at high volume
- Use WAV or high-quality MP3 (320kbps)

**Too many devices?**
- Playing on 5+ devices simultaneously can cause issues
- Try using fewer devices

### Audio keeps playing after raid ends

**Background thread issue:**
- Close and reopen RustPlus Raid Alarms
- The plugin will stop all playback on shutdown

**File is looping:**
- Make sure your audio file isn't set to loop in its metadata
- Re-export the file with no loop markers

## File Organization Tips

### Recommended Folder Structure
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

### Where to Find Sounds

**Free sound libraries:**
- [Freesound.org](https://freesound.org/) - Huge library of CC-licensed sounds
- [Zapsplat.com](https://www.zapsplat.com/) - Free SFX and music
- [Mixkit.co](https://mixkit.co/free-sound-effects/) - High-quality free sounds

**Record your own:**
- Windows Voice Recorder (built-in)
- Audacity (free, open source)
- Your phone's voice recorder

**Convert formats:**
- Use [Audacity](https://www.audacityteam.org/) to convert between formats
- Or [Online-Convert.com](https://audio.online-convert.com/) for quick conversions

## Configuration

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

## Advanced: Simultaneous Playback

The plugin plays all audio files **at the same time** by default. 

Want them to play **one after another** instead? Edit the plugin code:

```python
# In on_telegram_message() method
for audio_file in self.audio_files:
    thread = AudioPlaybackThread(audio_file, self.audio_volume, device_indices)
    thread.start()
    thread.wait()  # Add this line to wait for completion
```

## Performance Notes

- **Memory usage**: ~10-50MB per audio file loaded
- **CPU usage**: Minimal (< 5% during playback)
- **Multiple files**: No significant performance impact

## Privacy & Security

- **No network access** - All audio plays locally
- **No telemetry** - Plugin doesn't track usage
- **Config file** contains file paths only (safe to share)

## Coming Soon (Future Ideas)

- **Random playback** - Play a random file from a list
- **Fade in/out** - Smooth volume transitions
- **Playlist support** - Shuffle through multiple sounds
- **Spatial audio** - Pan sound left/right for dramatic effect
- **Voice changer** - Pitch shift for creepy alerts
