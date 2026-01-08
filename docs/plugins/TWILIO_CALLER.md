<div align="center">

# 📞 Twilio Caller Plugin

**Get Phone Calls During Raids**

[![Twilio](https://img.shields.io/badge/Twilio-F22F46?style=flat&logo=twilio&logoColor=white)](https://www.twilio.com)
[![Free Trial](https://img.shields.io/badge/Free_Trial-$15_Credit-brightgreen?style=flat)](https://www.twilio.com/try-twilio)
[![Voice Calls](https://img.shields.io/badge/Voice_Calls-$0.01%2Fmin-blue?style=flat)](https://www.twilio.com/voice/pricing)

Call multiple phone numbers when your base is raided! Perfect for waking you up during offline raids.

</div>

---

## ✨ Features

<details open>
<summary><b>What this plugin can do</b></summary>

| Feature | Description |
|---------|-------------|
| 📞 **Multiple Numbers** | Call up to 10+ phone numbers simultaneously |
| 🗣️ **Custom Message** | Text-to-speech reads your raid alert |
| 🧪 **Test Calls** | Verify setup before relying on it |
| ❓ **Built-in Help** | Step-by-step guide in the plugin UI |

</details>

---

## ✅ Prerequisites

<details open>
<summary><b>What you need to get started</b></summary>

### 🆓 Twilio Free Trial

| What | Details |
|------|----------|
| 🎁 **Free Credits** | $15 USD (~100 calls) |
| ⚠️ **Limitations** | Can only call verified phone numbers |
| 🚀 **Upgrade** | Add payment method to call any number |

### 💰 Costs (After Trial)

| Item | Price | Notes |
|------|-------|-------|
| 📞 Voice calls | $0.01-0.02/min | Per call, varies by country |
| 📱 Phone number | $1/month | Optional, for custom caller ID |

> 💡 **Free trial is perfect for testing!** You get $15 credit with no payment method required.

</details>

---

## 🛠️ Setup

<details open>
<summary><b>7-step configuration guide</b></summary>

### 1️⃣ Create Twilio Account

1. Go to [twilio.com/try-twilio](https://www.twilio.com/try-twilio)
2. Sign up for free trial (🎁 $15 credit included)
3. Verify your email and phone number
4. Complete the "Get Started" wizard

---

### 2️⃣ Get Your Credentials

> 💡 **Quick Help**: Click the **❓ button** in the plugin for detailed guidance!

1. Log in to [Twilio Console](https://console.twilio.com/)
2. On the dashboard, find:

| Credential | Format | Location |
|------------|--------|----------|
| **Account SID** | `ACxxxxx...` (33 chars) | Main dashboard |
| **Auth Token** | Click "Show" to reveal | Below Account SID |

3. 📋 Copy both values

---

### 3️⃣ Get a Twilio Phone Number

**🆓 Free Trial**: Skip this step (uses generic caller ID)

**💳 Paid Account**:
1. In Twilio Console → **Phone Numbers** → **Buy a Number**
2. Select your country
3. Choose any available number ($1/month)
4. Click **Buy**

---

### 4️⃣ Configure the Plugin

1. Open **RustPlus Raid Alarms**
2. Go to **Twilio Caller** plugin tab
3. Enter your credentials:

| Field | Value | Example |
|-------|-------|----------|
| **Account SID** | From dashboard | `AC1234567890abcdef...` |
| **Auth Token** | Click "Show" in Twilio | `your_secret_token` |
| **From Number** | Your Twilio number | `+15551234567` |

---

### 5️⃣ Add Phone Numbers to Call

1. Click **➕ Add Phone Number**
2. Enter in **E.164 format**: `+[country code][number]`

**Examples:**

| Format | Example | Country |
|--------|---------|----------|
| ✅ Correct | `+15551234567` | USA |
| ✅ Correct | `+447911123456` | UK |
| ❌ Wrong | `555-123-4567` | Missing + and country code |
| ❌ Wrong | `(555) 123-4567` | Has parentheses |

3. Add multiple numbers if desired
4. Click the ❌ to remove numbers

---

### 6️⃣ Verify Phone Numbers (Free Trial Only)

**💳 Paid accounts can skip this step.**

For free trial accounts, verify each number:

1. Twilio Console → **Phone Numbers** → **Verified Caller IDs**
2. Click **➕ Add a new number**
3. Enter the number you want to call
4. Twilio calls/texts with a verification code
5. Enter the code to verify
6. Repeat for each number

---

### 7️⃣ Test It

1. Click **📞 Make Test Call** button
2. All configured numbers receive a test call
3. Answer to hear: *"This is a test call from your Raid Alarm system"*
4. ✅ If it works, enable the plugin checkbox!

</details>

---

## ⚙️ How It Works

<details>
<summary><b>Behind the scenes</b></summary>

When a raid alert is received:

```
1. ✅ Plugin checks if enabled
2. 🔑 Validates Twilio credentials
3. 📞 Makes simultaneous calls to all numbers
4. 🗣️ Plays TTS: "Raid alert: [Your Telegram message]"
5. ⏱️ Call lasts ~10-30 seconds
```

**Call Flow:**
```
Telegram Message → Plugin Triggers → Twilio API → Phone Rings → TTS Plays
```

</details>

---

## 🌍 Phone Number Format (E.164)

<details open>
<summary><b>International phone number formatting</b></summary>

**Always use E.164 format**: `+[country code][number]` with **NO** spaces, dashes, or parentheses.

### 🌎 Examples by Country

| Country | Example | Format | Notes |
|---------|---------|--------|-------|
| 🇺🇸 USA/Canada | `+15551234567` | +1 + 10 digits | |
| 🇬🇧 UK | `+447911123456` | +44 + 9-10 digits | Drop leading 0 |
| 🇦🇺 Australia | `+61412345678` | +61 + 9 digits | Drop leading 0 |
| 🇩🇪 Germany | `+4915112345678` | +49 + 10-11 digits | Drop leading 0 |
| 🇫🇷 France | `+33612345678` | +33 + 9 digits | Drop leading 0 |

**🔍 Find your country code**: [Wikipedia - Country Calling Codes](https://en.wikipedia.org/wiki/List_of_country_calling_codes)

### ✅ Valid vs ❌ Invalid

| Status | Format | Reason |
|--------|--------|--------|
| ✅ Valid | `+15551234567` | Correct E.164 format |
| ✅ Valid | `+447911123456` | Correct with country code |
| ❌ Invalid | `555-123-4567` | Missing +, country code, has dashes |
| ❌ Invalid | `(555) 123-4567` | Has parentheses and spaces |
| ❌ Invalid | `15551234567` | Missing + symbol |
| ❌ Invalid | `+1 555 123 4567` | Has spaces |

</details>

---

## 🎨 Customizing the Message

<details>
<summary><b>Change what the TTS voice says</b></summary>

The default TTS message automatically includes your raid alert:
```
"Raid alert: [Your Telegram message from IFTTT]"
```

### Custom Message Code

Edit the `message` parameter in `plugins/twilio_caller.py`:

```python
# Line ~180 in make_calls() method
message = f"Custom message here! {telegram_message}"

# Examples:
message = f"Wake up! You are being raided! {telegram_message}"
message = f"Alert! {telegram_message}. Get online now!"
message = "Emergency! Check your Rust base immediately!"
```

### Conditional Messages

```python
if "raiding" in telegram_message.lower():
    message = "You are being raided! Get online NOW!"
elif "cargo" in telegram_message.lower():
    message = "Cargo ship has arrived!"
else:
    message = f"Raid alert: {telegram_message}"
```

</details>

---

## 🔧 Troubleshooting

<details>
<summary><b>Common issues and solutions</b></summary>

### 🔑 "Invalid Account SID or Auth Token"

| Check | Solution |
|-------|----------|
| 📝 **Copy errors** | Ensure full Account SID copied (starts with `AC`, 34 chars)<br>Click "Show" to reveal Auth Token in Twilio Console<br>No extra spaces or line breaks |
| 🔄 **Regenerate** | Twilio Console → Settings → API Credentials → Create new API Key |

---

### 📞 "The 'To' number is not a valid phone number"

| Problem | Solution |
|---------|----------|
| 🌍 **Wrong format** | Must use E.164: `+[country][number]`<br>Start with `+`, include country code<br>NO spaces, dashes, parentheses |
| 🔢 **Country codes** | USA/Canada: `+1`<br>UK: `+44`<br>[Full list](https://en.wikipedia.org/wiki/List_of_country_calling_codes) |

**Example fix:**
- ❌ `555-123-4567` → ✅ `+15551234567`
- ❌ `07911 123456` → ✅ `+447911123456`

---

### 📱 "The 'From' number is not a valid Twilio phone number"

| Account Type | Solution |
|--------------|----------|
| 🆓 **Free trial** | Leave "From Number" field **empty**<br>Calls use generic Twilio caller ID |
| 💳 **Paid** | 1. Buy number in Twilio Console<br>2. Copy in E.164 format<br>3. Paste into "From Number" field |

---

### 🌍 "Permission to send SMS not enabled for region"

**🆓 Free trial restriction**: Can only call **verified** numbers

**Solutions:**

| Option | Steps |
|--------|-------|
| **Verify numbers** | Twilio Console → Verified Caller IDs → Add each number |
| **Upgrade account** | Add payment method to call any number |

---

### 🔇 Calls not going through

| Cause | Fix |
|-------|-----|
| 🚫 **Phone blocking** | Disable "Unknown Caller" blocking<br>Some phones block suspected spam<br>Add Twilio number to contacts |
| 💰 **No credit** | Check balance in Twilio Console<br>Free trial: Monitor $15 credit<br>Paid: Add payment method |
| 🔍 **Wrong number** | Test with your own verified number first<br>Verify E.164 format |

</details>

---

## 💰 Cost Management

<details>
<summary><b>Optimize your Twilio spending</b></summary>

### 🆓 Free Trial Tips

| Resource | Amount | Usage |
|----------|--------|-------|
| 🎁 Starting credit | $15 | ~100-150 calls |
| 📞 Each raid | 1 call × number of recipients | Example: 3 numbers = 3 calls |
| 📊 Monitor | Twilio Console → Usage | Real-time tracking |

### 💵 Reducing Costs

| Strategy | Savings | How |
|----------|---------|-----|
| 👥 **Fewer numbers** | ~$0.01/call saved | Only call essential people |
| 🗣️ **Shorter messages** | ~30% reduction | Less talk time = cheaper |
| ⏰ **Cooldown** | 50%+ reduction | Don't call for every raid (future feature) |
| 🆓 **Stay on trial** | Free testing | $15 enough for extensive testing |

### 📊 Monitoring Usage

1. Go to [Twilio Console](https://console.twilio.com/)
2. Click **Usage** → **Voice**
3. View call history and costs
4. Set up usage alerts to avoid surprises

**🔔 Recommended**: Set alert at $10 remaining to avoid unexpected charges

</details>

---

## 📝 Configuration

<details>
<summary><b>Config file format and storage</b></summary>

Plugin settings saved in `config.json`:

```json
{
  "twilio_account_sid": "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "twilio_auth_token": "your_auth_token_here",
  "twilio_from_number": "+15551234567",
  "twilio_phone_numbers": [
    "+15559876543",
    "+447911123456"
  ],
  "twilio_message": "Raid alert: {telegram_message}",
  "plugin_enabled_Twilio Caller": true
}
```

> ⚠️ **Security**: Never share your Auth Token! It's like your Twilio password.

</details>

---

## 🔒 Privacy & Security

<details>
<summary><b>How your data is protected</b></summary>

| Data | Storage | Security |
|------|---------|----------|
| 🔑 **Auth Token** | Local `config.json` only | Keep file secure, never commit to Git |
| 📞 **Phone Numbers** | Local `config.json` only | Used for calls only |
| 📊 **Twilio Logs** | Twilio servers | Kept 13 months ([privacy policy](https://www.twilio.com/legal/privacy)) |

### 🛡️ Best Practices

- ❌ **Never commit** `config.json` to GitHub
- 🗑️ **Delete config** before sharing project
- 🔄 **Rotate tokens** if accidentally exposed
- 💾 **Backup config** to secure location only

### 🚨 If Token Is Exposed

1. Immediately go to Twilio Console → Settings → API Credentials
2. Click "View" next to Auth Token
3. Click "Revoke" to invalidate old token
4. Generate new token and update plugin

</details>

---

## 🚀 Advanced: Multiple Messages

<details>
<summary><b>Conditional TTS based on alert type</b></summary>

Edit the plugin code in `plugins/twilio_caller.py` to customize messages:

```python
# In make_calls() method (~line 180)
def make_calls(self, telegram_message: str):
    # Custom logic based on message content
    if "raiding" in telegram_message.lower():
        message = "You are being raided! Get online NOW!"
    elif "cargo" in telegram_message.lower():
        message = "Cargo ship has arrived at your base!"
    elif "helicopter" in telegram_message.lower():
        message = "Patrol helicopter is circling your base!"
    else:
        message = f"Raid alert: {telegram_message}"
    
    # Rest of the calling logic...
```

### Use Cases

| Trigger Word | Custom Message | Urgency |
|--------------|----------------|----------|
| "RAID" | "WAKE UP! You are being raided!" | 🔴 Critical |
| "offline" | "Offline raid detected! Check now!" | 🔴 Critical |
| "cargo" | "Cargo ship arrived, FYI" | 🟡 Medium |
| "bradley" | "Bradley APC spawned" | 🟢 Low |

</details>

---

## 🔗 Support

| Resource | Link | Purpose |
|----------|------|----------|
| 📞 **Twilio Support** | [support.twilio.com](https://support.twilio.com) | Official Twilio help |
| 📖 **Twilio Docs** | [twilio.com/docs/voice](https://www.twilio.com/docs/voice) | API documentation |
| 🐛 **Plugin Issues** | GitHub Issues | Report bugs with error messages |

---

<div align="center">

**[⬅️ Back to Main README](../../README.md)** • **[📖 All Plugin Guides](../../README.md#-plugins)**

Made with ❤️ for the Rust community

</div>
