import json
import os
from pathlib import Path
from typing import Dict, Any, List

# Default API Credentials (can be overridden by user in GUI)
DEFAULT_API_ID = 1234567
DEFAULT_API_HASH = "82bd7b4562f7ju24d182bdc38huj9352"

APP_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = APP_DIR / "secphoto_config.json"
SESSIONS_DIR = APP_DIR / "sessions"

DEFAULT_CONFIG: Dict[str, Any] = {
    "api_id": DEFAULT_API_ID,
    "api_hash": DEFAULT_API_HASH,
    "last_session": "secret",
    "proxy_enabled": False,
    "proxy_type": "SOCKS5",
    "proxy_host": "127.0.0.1",
    "proxy_port": 9050,
    "proxy_user": "",
    "proxy_password": "",
    "save_local_backup": True,
    "local_backup_dir": str(APP_DIR / "saved_media"),
    "forward_to_saved_messages": True,
    "timezone": "Asia/Tehran",
    "auto_login": True
}


def ensure_directories():
    """Ensure sessions and saved media directories exist."""
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    Path(DEFAULT_CONFIG["local_backup_dir"]).mkdir(parents=True, exist_ok=True)


def load_config() -> Dict[str, Any]:
    """Load settings from JSON config file or return defaults."""
    ensure_directories()
    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Merge with defaults to ensure all keys exist
            merged = DEFAULT_CONFIG.copy()
            merged.update(data)
            return merged
    except Exception:
        return DEFAULT_CONFIG.copy()


def save_config(config_data: Dict[str, Any]) -> None:
    """Save settings to JSON config file."""
    ensure_directories()
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving config: {e}")


def list_saved_sessions() -> List[Dict[str, Any]]:
    """List all available .session files in the app directory and sessions directory."""
    sessions = []
    seen = set()

    # Search in main directory
    for f in APP_DIR.glob("*.session"):
        session_name = f.stem
        if session_name not in seen and not session_name.endswith("-journal"):
            seen.add(session_name)
            sessions.append({
                "name": session_name,
                "path": str(f),
                "is_active": False,
                "size_bytes": f.stat().st_size,
                "modified": f.stat().st_mtime
            })

    # Search in sessions/ directory
    if SESSIONS_DIR.exists():
        for f in SESSIONS_DIR.glob("*.session"):
            session_name = f.stem
            if session_name not in seen and not session_name.endswith("-journal"):
                seen.add(session_name)
                sessions.append({
                    "name": session_name,
                    "path": str(f),
                    "is_active": False,
                    "size_bytes": f.stat().st_size,
                    "modified": f.stat().st_mtime
                })

    return sessions
