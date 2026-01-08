# 📞 Twilio Caller Plugin

Call multiple phone numbers when your base is raided! Perfect for waking you up during offline raids or alerting your team members.

## Features
- **Multiple Numbers** - Call up to 10+ phone numbers simultaneously
- **Custom Message** - TTS reads your raid alert message
- **Test Calls** - Verify setup before relying on it
- **Easy Setup** - Step-by-step guide built into the plugin

## Prerequisites

You need a Twilio account to use this plugin.

### Twilio Free Trial
- **Free credits**: $15 USD (about 100 calls)
- **Limitations**: Can only call verified phone numbers
- **Upgrade**: Remove limitations by adding payment method

### Costs (After Trial)
- **Voice calls**: ~$0.01-0.02 per minute
- **Phone number**: $1/month (optional, for caller ID)

## Setup

### Step 1: Create Twilio Account

1. Go to [twilio.com/try-twilio](https://www.twilio.com/try-twilio)
2. Sign up for free trial ($15 credit included)
3. Verify your email and phone number
4. Complete the "Get Started" wizard

### Step 2: Get Your Credentials

**📍 Click the ❓ button in the plugin for detailed help!**

1. Log in to [Twilio Console](https://console.twilio.com/)
2. On the dashboard, find:
   - **Account SID**: Long string starting with `AC...`
   - **Auth Token**: Click "Show" to reveal it
3. Copy both values

### Step 3: Get a Twilio Phone Number

**Free Trial**: Skip this step (uses generic caller ID)

**Paid Account**:
1. In Twilio Console, go to **Phone Numbers** → **Buy a Number**
2. Select your country
3. Choose any available number ($1/month)
4. Click "Buy"

### Step 4: Configure the Plugin

1. Open RustPlus Raid Alarms
2. Go to **Twilio Caller** plugin tab
3. Enter your credentials:
   - **Account SID**: Paste from Twilio dashboard
   - **Auth Token**: Paste from Twilio dashboard
   - **From Number**: Your Twilio number (format: `+12345678901`)

### Step 5: Add Phone Numbers to Call

1. Click **Add Phone Number**
2. Enter the number in E.164 format: `+[country code][number]`
   - ✅ Correct: `+15551234567` (USA)
   - ✅ Correct: `+447911123456` (UK)
   - ❌ Wrong: `555-123-4567`
   - ❌ Wrong: `(555) 123-4567`
3. Add multiple numbers if desired
4. Click the ❌ to remove numbers

### Step 6: Verify Phone Numbers (Free Trial Only)

**Paid accounts can skip this step.**

For free trial accounts, you must verify each number:
1. In Twilio Console, go to **Phone Numbers** → **Verified Caller IDs**
2. Click **Add a new number**
3. Enter the number you want to call
4. Twilio will call/text with a verification code
5. Enter the code to verify
6. Repeat for each number you want to call

### Step 7: Test It

1. Click **📞 Make Test Call** button
2. All configured numbers will receive a test call
3. Answer to hear: "This is a test call from your Raid Alarm system"
4. If it works, enable the plugin checkbox!

## How It Works

When a raid alert is received:
1. Plugin checks if it's enabled
2. Validates Twilio credentials and phone numbers
3. Makes simultaneous calls to all configured numbers
4. Plays TTS message: "Raid alert: [Your Telegram message]"
5. Calls last ~10-30 seconds depending on message length

## Phone Number Format (E.164)

**Always use E.164 format**: `+[country code][number]` with NO spaces, dashes, or parentheses.

### Examples by Country

| Country | Example | Format |
|---------|---------|--------|
| USA/Canada | `+15551234567` | +1 + 10 digits |
| UK | `+447911123456` | +44 + 9-10 digits |
| Australia | `+61412345678` | +61 + 9 digits |
| Germany | `+4915112345678` | +49 + 10-11 digits |
| France | `+33612345678` | +33 + 9 digits |

**Find your country code**: [Wikipedia - Country Calling Codes](https://en.wikipedia.org/wiki/List_of_country_calling_codes)

## Customizing the Message

The TTS message includes your raid alert automatically:
```
"Raid alert: [Your Telegram message from IFTTT]"
```

Want to customize? Edit the `message` parameter in `twilio_plugin/__init__.py`:
```python
message = f"Custom message here! {telegram_message}"
```

## Troubleshooting

### "Invalid Account SID or Auth Token"

**Check credentials:**
- Make sure you copied the full Account SID (starts with `AC`)
- Make sure you revealed and copied the Auth Token (click "Show")
- No extra spaces or characters

**Regenerate if needed:**
1. Go to Twilio Console → Settings → API Credentials
2. Click "Create new API Key" if token is compromised

### "The 'To' number is not a valid phone number"

**Check E.164 format:**
- Must start with `+`
- Must include country code
- No spaces, dashes, or parentheses
- Example: `+15551234567` not `555-123-4567`

**Country code lookup:**
- USA/Canada: `+1`
- UK: `+44`
- Use [Wikipedia](https://en.wikipedia.org/wiki/List_of_country_calling_codes) for others

### "The 'From' number is not a valid, SMS-capable, Twilio phone number"

**Free trial:**
- Leave "From Number" empty
- Calls will use generic Twilio caller ID

**Paid account:**
1. Buy a phone number in Twilio Console
2. Copy the number in E.164 format
3. Paste into "From Number" field

### "Permission to send an SMS has not been enabled for the region indicated by the 'To' number"

**Free trial restrictions:**
- You can only call verified phone numbers
- Verify numbers in Twilio Console → Verified Caller IDs

**Solution:**
- Verify each number you want to call, OR
- Upgrade to a paid account (add payment method)

### Calls not going through

**Check phone settings:**
- Make sure "Unknown Caller" blocking is off
- Some phones block suspected spam calls
- Add Twilio number to contacts to whitelist it

**Check Twilio balance:**
1. Log in to Twilio Console
2. Check balance on dashboard
3. Free trial: Should have credit remaining
4. Paid: Add payment method if balance is $0

## Cost Management

### Free Trial Tips
- $15 credit lasts ~100-150 calls
- Each raid = 1 call per phone number
- Monitor usage in Twilio Console

### Reducing Costs
- **Use fewer numbers** - Only call essential people
- **Shorter messages** - Less talk time = cheaper
- **Set cooldown** - Don't call for every single raid (future feature)
- **Upgrade strategically** - Free trial is enough for testing

### Monitoring Usage
1. Go to [Twilio Console](https://console.twilio.com/)
2. Check **Usage** → **Voice** to see call history
3. Set up usage alerts to avoid surprises

## Configuration

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

**⚠️ Never share your Auth Token!** It's like a password for your Twilio account.

## Privacy & Security

- **Auth Token** is stored locally in `config.json` (keep this file secure)
- **Phone numbers** are only used for calling, not stored elsewhere
- **Twilio logs** keep call history for 13 months (see Twilio privacy policy)
- **Delete config.json** before sharing your project with others

## Advanced: Multiple Messages

Want different messages for different alerts? Edit the plugin code:

```python
# In make_calls() method
if "raiding" in telegram_message.lower():
    message = "You are being raided! Get online NOW!"
elif "cargo" in telegram_message.lower():
    message = "Cargo ship has arrived at your base!"
else:
    message = f"Raid alert: {telegram_message}"
```

## Support

- **Twilio Help**: [support.twilio.com](https://support.twilio.com)
- **Twilio Docs**: [twilio.com/docs/voice](https://www.twilio.com/docs/voice)
- **Plugin Issues**: File a GitHub issue with error messages
