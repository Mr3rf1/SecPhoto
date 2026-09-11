# SecPhoto

A Python tool to save Telegram self-destructing photos and videos. This tool allows you to capture and save disappearing media from Telegram chats before they expire.

## ⚠️ Important Notice

**Before using this tool, you MUST obtain your own Telegram API credentials.** The current code contains hardcoded API credentials which should be replaced with your own for security and functionality reasons.

## 📋 Prerequisites

- Python 3.6 or higher
- A Telegram account
- Telegram API credentials (api_id and api_hash)

## 🔑 Getting Telegram API Credentials

### Step 1: Create a Telegram Application

1. Go to [my.telegram.org](https://my.telegram.org)
2. Log in with your phone number (the same number you use for Telegram)
3. Click on "API Development Tools"

### Step 2: Create a New Application

1. Fill out the form with the following information:
   - **App title**: Choose any name (e.g., "SecPhoto Tool")
   - **Short name**: Choose a short name (e.g., "secphoto")
   - **URL**: Leave empty or add your website
   - **Platform**: Choose "Desktop"
   - **Description**: Brief description of your app
2. Click "Create application"

### Step 3: Get Your Credentials

After creating the application, you'll see:
- **api_id**: A numeric ID (e.g., 1234567)
- **api_hash**: A 32-character hash (e.g., "abcdef1234567890abcdef1234567890")

### Step 4: Update the Code

1. Open `SecPhoto.py` in a text editor
2. Find these lines (around line 11-12):
   ```python
   api_id = 1234567
   api_hash = "82bd7b4562teujin24d18rfayt39b2d9352"
   ```
3. Replace them with your own credentials:
   ```python
   api_id = YOUR_API_ID_HERE
   api_hash = "YOUR_API_HASH_HERE"
   ```

## 🚀 Installation

### For Windows/Linux/macOS

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Mr3rf1/SecPhoto
   cd SecPhoto
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

   Or if you're using Python 3 specifically:
   ```bash
   python3 -m pip install -r requirements.txt
   ```

### For Termux (Android)

1. **Update packages:**
   ```bash
   apt update && apt upgrade
   ```

2. **Install required packages:**
   ```bash
   pkg install python3 python3-pip git
   ```

3. **Clone and setup:**
   ```bash
   git clone https://github.com/Mr3rf1/SecPhoto
   cd SecPhoto
   python3 -m pip install -r requirements.txt
   ```

## 📖 Usage

### Saving Deleted Messages

When Telegram reports deleted messages, SecPhoto sends one count-only notification to Saved Messages. It identifies the chat and number of deleted messages. Telegram does not provide the identity of the user who deleted them. The private archive channel remains responsible for preserving the deleted content.

### Basic Usage

1. **Start the tool simply**
   ```bash
   python3 SecPhoto.py
   ```

### Private Chat Archive

The Docker version creates a private `SecPhoto Commands` channel on first startup. Send commands there:

```text
/archive @username-or-chat-id
/archive-adopt <archive-channel-id> <source-chat>
/archive-status
/archive-stop
```

`/archive` creates a private channel, copies the source chat's existing messages in chronological order, and mirrors new messages afterward. If a source message is deleted, the archive retains the copy and adds a deletion notice. The command and archive channel IDs are stored in `/app/data/archive_state.json`, so restarts reuse them. Set `TG_COMMAND_CHANNEL_ID` when an existing private command channel should be used instead.

For an older archive channel created outside SecPhoto, use `/archive-adopt` with both channel IDs. Telegram does not expose the original source chat for an arbitrary channel, so the source must be supplied explicitly; the existing messages are retained and only future source messages are mirrored.

The logged-in account must be able to read the source chat. Protected messages that cannot be forwarded are copied by downloading and uploading their media when Telegram permits it; some service messages and restricted media cannot be copied.

### Reply-to-Save Feature

The tool now supports a convenient reply-to-save feature:

1. **Automatic Detection**: The tool automatically monitors all chats and saves self-destructing media as soon as it appears
2. **Reply Method**: If you missed a self-destructing message, simply **reply to it** and the tool will save the media
3. **Works Everywhere**: This feature works in all types of chats (private, groups, channels)
4. **Real-time Processing**: Both automatic detection and reply-based saving happen in real-time

### With Proxy (Tor/SOCKS5)

If you need to use a proxy:
```bash
python3 SecPhoto.py -p 127.0.0.1:9050
```

### How It Works

1. Run the command to start monitoring all chats
2. The tool will automatically detect and save self-destructing media in real-time
3. **New Feature**: You can also save self-destructing media by **replying** to any message containing such media
4. The tool will automatically download and save the media
5. The saved media will be sent to your "Saved Messages" in Telegram

### Getting Help

To see all available options:
```bash
python3 SecPhoto.py --help
```

## 🔧 Command Line Options

| Option | Description | Example |
|--------|-------------|---------|
| `-p`, `--proxy` | SOCKS5 proxy (IP:PORT) | `-p 127.0.0.1:9050` |
| `--help` | Show help message | `--help` |

## 📁 Dependencies

- `telethon` - Telegram client library
- `colorama` - Colored terminal output
- `pysocks` - SOCKS proxy support

## ⚡ Features

- ✅ Save self-destructing photos
- ✅ Save self-destructing videos
- ✅ **Reply-to-save feature** - Reply to any message to save its self-destructing media
- ✅ Real-time monitoring of all chats
- ✅ SOCKS5 proxy support
- ✅ Works with both usernames and numeric IDs
- ✅ Automatic delivery to Saved Messages
- ✅ Cross-platform compatibility

## 🛡️ Security Notes

- Keep your API credentials private and never share them
- The tool creates a session file (`secret.session`) - keep this secure
- Downloaded media is temporarily saved as `secret.jpg` or `secret.mp4`

## 🐛 Troubleshooting

### "Please install dependencies" error
Make sure you've installed all requirements:
```bash
pip install -r requirements.txt
```

### Authentication errors
1. Verify your API credentials are correct
2. Make sure you're using your own api_id and api_hash
3. Delete the `secret.session` file and try again

### Permission errors
Make sure the script has write permissions in the current directory.

## 📄 License

This project is for educational purposes. Please respect Telegram's Terms of Service and use responsibly.

## 👨‍💻 Author

- GitHub: [@Mr3rf1](https://github.com/Mr3rf1)
- Telegram: [@Mr3rf1](https://t.me/Mr3rf1)
