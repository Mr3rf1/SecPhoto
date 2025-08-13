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

### Basic Usage

1. **Start the tool with a chat username:**
   ```bash
   python3 SecPhoto.py -Sid <username>
   ```
   Example:
   ```bash
   python3 SecPhoto.py -Sid john_doe
   ```

2. **Or use a numeric chat ID:**
   ```bash
   python3 SecPhoto.py -Nid <chat_id>
   ```
   Example:
   ```bash
   python3 SecPhoto.py -Nid 123456789
   ```

### With Proxy (Tor/SOCKS5)

If you need to use a proxy:
```bash
python3 SecPhoto.py -p 127.0.0.1:9050 -Sid <username>
```

### How It Works

1. Run the command with the target chat ID or username
2. The tool will start monitoring the specified chat
3. Go to the Telegram chat and **reply** to any self-destructing photo/video
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
| `-Sid`, `--string-id` | Chat username | `-Sid john_doe` |
| `-Nid`, `--numeric-id` | Numeric chat ID | `-Nid 123456789` |
| `-p`, `--proxy` | SOCKS5 proxy (IP:PORT) | `-p 127.0.0.1:9050` |
| `--help` | Show help message | `--help` |

## 📁 Dependencies

- `telethon` - Telegram client library
- `colorama` - Colored terminal output
- `pysocks` - SOCKS proxy support

## ⚡ Features

- ✅ Save self-destructing photos
- ✅ Save self-destructing videos
- ✅ SOCKS5 proxy support
- ✅ Works with both usernames and numeric IDs
- ✅ Automatic delivery to Saved Messages
- ✅ Cross-platform compatibility
- ✅ Auto-deletion of Database  lock (New)
- ✅ Duplicate photo detection for current session (New) 
- ✅ Save Notification to multiple IDs (New)

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
- 
  ## 👨‍💻 Contributor

- Telegram: [Britz] @rickmorti12
