# SecPhoto

A powerful, privacy-focused tool designed to automatically capture and save Telegram self-destructing (disappearing) photos and videos before they expire.

SecPhoto offers both a **modern graphical desktop interface (PySide6)** and a **lightweight headless CLI**, providing flexible monitoring across private chats, groups, and channels.

---

## ✨ Key Features

- ⚡ **Automatic Real-Time Interception**: Listens in the background and immediately captures disappearing media with TTL timers as soon as they arrive.
- 💬 **Reply-to-Save**: Missed an incoming self-destructing photo or video? Simply **reply to the message** in Telegram, and SecPhoto will capture and preserve it on demand.
- 📦 **Grouped Album Support**: Automatically detects and groups multi-item albums, preserving order and delivering them as cohesive albums with complete metadata.
- 🖥️ **Modern Desktop GUI**: Sleek PySide6 interface featuring:
  - Interactive login with phone number, verification code, and 2FA password support.
  - Live monitoring dashboard with one-click Start/Stop controls.
  - Real-time statistics counters (Photos, Videos, and Albums captured).
  - Visual media stream with sender information, timestamp badges, and quick links.
  - Integrated live activity console with color-coded logs and instant clipboard copy.
  - Instant **Dark & Light Mode** theme switching with persistent preferences.
  - In-app proxy and storage settings configuration.
- 💻 **Lightweight Headless CLI**: Fast terminal-based execution ideal for low-resource environments, remote servers, or command-line workflows.
- 🔒 **Local-First & Zero Telemetry**: Operates strictly between your client and Telegram's official MTProto servers. No analytics, tracking, or remote servers.
- 🌐 **SOCKS5 Proxy Ready**: Built-in SOCKS5 proxy support (including Tor) for restricted networks.

---

## 📋 Prerequisites

- **Python 3.8** or higher
- A **Telegram account**
- Telegram **API credentials** (`api_id` and `api_hash`)

---

## 🔑 Getting Telegram API Credentials

Before running SecPhoto, you will need your own Telegram API credentials:

1. Visit **[my.telegram.org](https://my.telegram.org)** in your web browser.
2. Log in using your Telegram phone number (in international format, e.g., `+1234567890`).
3. Navigate to **API Development Tools**.
4. Fill out the application form:
   - **App title**: Choose any name (e.g., `SecPhoto`)
   - **Short name**: Choose a short identifier (e.g., `secphoto`)
   - **Platform**: Select `Desktop`
5. Click **Create application**.
6. Copy your **`api_id`** (numeric) and **`api_hash`** (alphanumeric string).

> **Note**: When using the Desktop GUI, you can enter your `api_id` and `api_hash` directly into the login screen without modifying any source files.

---

## 🚀 Installation & Downloads

### 📥 Pre-Built GUI Applications (Windows & Linux)

If you prefer not to install Python or manage dependencies manually, pre-built GUI packages for **Windows** and **Linux** are available directly on the **[GitHub Releases](https://github.com/Mr3rf1/SecPhoto/releases)** section. Simply download the latest release for your platform and launch it directly.

### 🛠️ Running from Source (Windows, macOS, Linux)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Mr3rf1/SecPhoto.git
   cd SecPhoto
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Termux (Android)

Run SecPhoto in headless CLI mode on Android via Termux:

1. **Update packages and install Python:**
   ```bash
   pkg update && pkg install python git
   ```

2. **Clone and install dependencies:**
   ```bash
   git clone https://github.com/Mr3rf1/SecPhoto.git
   cd SecPhoto
   pip install -r requirements.txt
   ```

---

## 📖 Usage Guide

SecPhoto provides two distinct interfaces to suit your workflow:

### 🖥️ Option 1: Modern Desktop GUI (Recommended)

You can run the pre-built desktop application directly from **[GitHub Releases](https://github.com/Mr3rf1/SecPhoto/releases)** (for Windows and Linux), or launch it from source:

```bash
python gui/run_gui.py
```

#### GUI Highlights:
- **Interactive Authentication**: Log in directly with your phone number, receive verification codes, and authenticate with 2FA passwords seamlessly.
- **Account Profiles**: Switch between authenticated accounts or log in with fresh credentials at any time.
- **Real-Time Dashboard**:
  - Click **Start Monitoring** to begin capturing disappearing media in real time.
  - Track live statistics for captured photos, videos, and albums.
  - Inspect incoming media cards displaying chat name, sender, date, time, and links.
- **Theme Switching**: Toggle between dark and light themes using the theme button in the top navigation bar.
- **Settings Dialog**: Configure proxy connections and delivery destinations with a single click.

---

### 💻 Option 2: Headless CLI Mode

Run the lightweight command-line interface directly in your terminal:

```bash
python SecPhoto.py
```

#### Command-Line Options:

| Option | Description | Example |
|---|---|---|
| `-p`, `--proxy IP:PORT` | Route traffic through a SOCKS5 proxy (e.g., Tor) | `python SecPhoto.py -p 127.0.0.1:9050` |
| `-v`, `--version` | Display application version | `python SecPhoto.py --version` |
| `-help`, `--help` | Show available options and help banner | `python SecPhoto.py --help` |

---

## 💡 How Interception Works

1. **Automatic Monitoring**: When monitoring is active, SecPhoto listens for incoming messages containing self-destructing (TTL) photos or videos across all active chats.
2. **Reply-to-Save Feature**: If you miss a disappearing message before it is captured, simply **reply to that message** in Telegram. SecPhoto will detect the reply, download the original media, and save it.
3. **Saved Messages Delivery**: Intercepted media is automatically forwarded to your Telegram **"Saved Messages"** chat, complete with a structured caption including:
   - Origin Chat ID
   - Sender Username
   - Message ID
   - Exact Timestamp

---

## 🛡️ Privacy & Security

- **Zero Telemetry**: SecPhoto contains no remote telemetry, crash reporters, or analytics. Your activity is strictly between your machine and Telegram.
- **Credential Protection**: Never share your API credentials, phone verification codes, or authorization data with anyone.
- **Safe Operation**: SecPhoto operates non-intrusively. It does not alter, delete, or send unprompted messages in origin chats.

---

## 🐛 Troubleshooting

### "Please install dependencies"
Ensure all required Python packages are installed:
```bash
pip install -r requirements.txt
```

### Two-Factor Authentication (2FA) Prompt
If your account has Two-Step Verification enabled, both the GUI and CLI will prompt you for your 2FA password during sign-in. Enter your account password to complete authentication.

### Network or Connection Timeouts
If you are operating behind a restricted network or firewall:
- In the **GUI**: Open **Settings** and enable the SOCKS5 proxy with your proxy host and port.
- In the **CLI**: Pass the `-p` parameter (e.g., `python SecPhoto.py -p 127.0.0.1:9050`).

---

## 📄 License

This project is intended for personal and educational use. Please respect Telegram's Terms of Service and use responsibly.

---

## 👨‍💻 Author

- GitHub: [@Mr3rf1](https://github.com/Mr3rf1)
- Telegram: [@Mr3rf1](https://t.me/Mr3rf1)
