import asyncio
import os
import re
import shutil
import sqlite3
from datetime import datetime as dt
from pathlib import Path
from typing import Callable, Optional, List, Dict, Any

from telethon import TelegramClient, events
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneCodeInvalidError,
    PhoneCodeExpiredError,
    PasswordHashInvalidError,
    PhoneNumberInvalidError
)

try:
    from jdatetime import datetime as jdatetime
    import pytz
except ImportError:
    jdatetime = None
    pytz = None


try:
    from colorama import Fore, init as colorama_init
    colorama_init(autoreset=True)
except ImportError:
    class _Fore:
        GREEN = RED = YELLOW = CYAN = MAGENTA = RESET = ""
    Fore = _Fore()


class TelethonEngine:
    """Encapsulates Telethon client operations, event listeners, and media capture."""

    def __init__(
        self,
        session_name_or_path: str,
        api_id: int,
        api_hash: str,
        proxy: Optional[tuple] = None,
        save_local_backup: bool = True,
        local_backup_dir: str = "saved_media",
        album_debounce_sec: float = 0.7,
        timezone_str: str = "Asia/Tehran"
    ):
        self.session_path = session_name_or_path
        self.api_id = int(api_id)
        self.api_hash = str(api_hash)
        self.proxy = proxy
        self.save_local_backup = save_local_backup
        self.local_backup_dir = Path(local_backup_dir)
        self.local_backup_dir.mkdir(parents=True, exist_ok=True)
        self.album_debounce_sec = album_debounce_sec
        self.timezone_str = timezone_str

        self.client: Optional[TelegramClient] = None
        self.is_monitoring: bool = False

        # Album debouncing structures
        self.album_buffer: Dict[tuple, List[Any]] = {}
        self.album_tasks: Dict[tuple, asyncio.Task] = {}

        # Auth state storage
        self.phone_number: Optional[str] = None
        self.phone_code_hash: Optional[str] = None

        # Callbacks for GUI events
        self.on_log: Optional[Callable[[str, str], None]] = None  # (level, message)
        self.on_media_captured: Optional[Callable[[Dict[str, Any]], None]] = None
        self.on_status_changed: Optional[Callable[[str], None]] = None

    def log(self, level: str, message: str):
        """Log message to both stdout terminal and GUI callback."""
        lvl = level.lower()
        if lvl == "success":
            color = Fore.GREEN
            tag = "SUCCESS"
        elif lvl in ("warning", "warn"):
            color = Fore.YELLOW
            tag = "WARN"
        elif lvl in ("error", "fatal"):
            color = Fore.RED
            tag = "ERROR"
        elif lvl == "special":
            color = Fore.MAGENTA
            tag = "MEDIA"
        else:
            color = Fore.CYAN
            tag = "INFO"

        print(f" {color}[{tag}]{Fore.RESET} {message}", flush=True)

        if self.on_log:
            try:
                self.on_log(level, message)
            except Exception:
                pass

    def create_client(self) -> TelegramClient:
        """Instantiate TelegramClient with proxy if configured."""
        if self.proxy:
            self.log("info", f"Using proxy: {self.proxy}")
            self.client = TelegramClient(self.session_path, self.api_id, self.api_hash, proxy=self.proxy)
        else:
            self.client = TelegramClient(self.session_path, self.api_id, self.api_hash)
        return self.client

    async def connect_client(self) -> bool:
        """Connect to Telegram network with sqlite lock recovery."""
        if not self.client:
            self.create_client()

        try:
            if not self.client.is_connected():
                self.log("info", "Connecting to Telegram servers...")
                await self.client.connect()
                self.log("success", "Connected to Telegram servers.")
            return True
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e).lower():
                self.log("warning", "Session database was locked. Recovering...")
                session_base = self.client.session.filename
                for ext in [".session", ".session-journal"]:
                    fpath = f"{session_base}{ext}"
                    if os.path.exists(fpath):
                        try:
                            os.remove(fpath)
                            self.log("info", f"Cleaned locked file: {fpath}")
                        except Exception as err:
                            self.log("error", f"Could not remove {fpath}: {err}")
                self.create_client()
                await self.client.connect()
                return True
            else:
                self.log("error", f"Database error on connect: {e}")
                raise

    async def check_is_authorized(self) -> Optional[Dict[str, Any]]:
        """Check if current session is authorized. Return user info dict if authorized."""
        await self.connect_client()
        if await self.client.is_user_authorized():
            me = await self.client.get_me()
            self.log("success", f"Session authorized for: {me.first_name} (@{me.username or me.id})")
            return {
                "id": me.id,
                "first_name": me.first_name or "",
                "last_name": me.last_name or "",
                "username": me.username or "",
                "phone": me.phone or ""
            }
        return None

    async def request_login_code(self, phone: str) -> Dict[str, Any]:
        """Send verification code to phone number."""
        await self.connect_client()
        self.phone_number = phone.strip()
        try:
            self.log("info", f"Requesting Telegram code for {self.phone_number}...")
            sent_code = await self.client.send_code_request(phone=self.phone_number)
            self.phone_code_hash = sent_code.phone_code_hash
            self.log("success", f"Verification code sent to {self.phone_number}")
            return {
                "success": True,
                "phone_code_hash": self.phone_code_hash,
                "timeout": getattr(sent_code, "timeout", None)
            }
        except PhoneNumberInvalidError:
            self.log("error", "The phone number is invalid. Please include international country code (e.g. +1234567890)")
            return {"success": False, "error": "Invalid phone number format."}
        except Exception as e:
            self.log("error", f"Failed to send code: {str(e)}")
            return {"success": False, "error": str(e)}

    async def complete_sign_in_code(self, code: str) -> Dict[str, Any]:
        """Complete sign in with code. Returns status or prompts for 2FA password."""
        if not self.client or not self.phone_number:
            self.log("error", "Client or phone number missing. Request code first.")
            return {"success": False, "error": "Login session not initialized. Request code first."}

        clean_code = re.sub(r'[\s\-]', '', str(code).strip())
        self.log("info", f"Submitting verification code '{clean_code}' for {self.phone_number}...")

        try:
            if self.phone_code_hash:
                await self.client.sign_in(
                    phone=self.phone_number,
                    code=clean_code,
                    phone_code_hash=self.phone_code_hash
                )
            else:
                await self.client.sign_in(
                    phone=self.phone_number,
                    code=clean_code
                )
            me = await self.client.get_me()
            self.log("success", f"Successfully logged in as {me.first_name} (@{me.username or me.id})")
            return {
                "success": True,
                "requires_2fa": False,
                "user": {
                    "id": me.id,
                    "first_name": me.first_name or "",
                    "last_name": me.last_name or "",
                    "username": me.username or "",
                    "phone": me.phone or ""
                }
            }
        except SessionPasswordNeededError:
            self.log("warning", "Two-step verification (2FA) password required for this account.")
            return {"success": False, "requires_2fa": True, "error": "2FA Password Required"}
        except (PhoneCodeInvalidError, PhoneCodeExpiredError) as e:
            self.log("error", f"Verification code error: {str(e)}")
            return {"success": False, "requires_2fa": False, "error": f"Invalid or expired code: {str(e)}"}
        except Exception as e:
            self.log("error", f"Sign in failed: {str(e)}")
            return {"success": False, "requires_2fa": False, "error": str(e)}

    async def complete_sign_in_2fa(self, password: str) -> Dict[str, Any]:
        """Complete sign in with 2FA password."""
        if not self.client:
            return {"success": False, "error": "Client not initialized."}

        self.log("info", "Submitting 2FA password...")
        try:
            await self.client.sign_in(password=str(password).strip())
            me = await self.client.get_me()
            self.log("success", f"Successfully authenticated with 2FA as {me.first_name}!")
            return {
                "success": True,
                "user": {
                    "id": me.id,
                    "first_name": me.first_name or "",
                    "last_name": me.last_name or "",
                    "username": me.username or "",
                    "phone": me.phone or ""
                }
            }
        except PasswordHashInvalidError:
            self.log("error", "Incorrect 2FA password.")
            return {"success": False, "error": "Incorrect 2FA password."}
        except Exception as e:
            self.log("error", f"2FA verification failed: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_formatted_timestamp(self) -> str:
        """Return formatted date time in Asia/Tehran or local."""
        if pytz and jdatetime:
            try:
                tz = pytz.timezone(self.timezone_str)
                return jdatetime.now(tz).strftime('%Y/%m/%d %H:%M:%S')
            except Exception:
                pass
        return dt.now().strftime('%Y-%m-%d %H:%M:%S')

    def build_filename_stem(self, username: Optional[str], chat_id: int, timestamp_str: str, index: Optional[int] = None) -> str:
        """Build safe filename stem."""
        name = username if username else str(chat_id)
        name = re.sub(r'[\\/:*?"<>|]', '_', name)
        stem = f"{name}_{timestamp_str}"
        if index is not None:
            stem = f"{stem}_{index}"
        return stem

    def build_caption(self, message: Any, chat_id: int, username: Optional[str], is_reply: bool = False, is_album: bool = False) -> str:
        """Build formatted HTML caption."""
        prefix = '┏' if not is_reply else '┣'
        album_line = f"┣ᗩᒪᗷᑌᗰ ⤳ ✓\n" if is_album else ""
        caption = (
            f"{prefix}ᑕᕼᗩT Iᗪ ⤳ <a href=\"tg://user?id={chat_id}\">{chat_id}</a>\n"
            f"{album_line}"
            f"┣ᑌՏᗴᖇᑎᗩᗰᗴ ⤳ {'@' + username if username else '✗'}\n"
            f"┣ᗰᗴՏՏᗩᘜᗴ Iᗪ ⤳ {message.id}\n"
            f"┣ᗪᗩTᗴ TIᗰᗴ ⤳ {self.get_formatted_timestamp()}\n"
            f"┗ github.com/Mr3rf1\n"
        )
        if is_reply:
            caption = f"┏ᖇᗴᑭᒪIᗴᗴᗪ TO ᗰᗴՏՏᗩᘜᗴ\n" + caption
        return caption

    def is_self_destructive(self, message: Any) -> bool:
        """Check if message contains self-destructing media (TTL)."""
        return (
            message.media is not None
            and hasattr(message.media, 'ttl_seconds')
            and bool(message.media.ttl_seconds)
        )

    async def process_album(self, messages: List[Any], chat_title: str, chat_id: int, username: Optional[str], is_reply: bool = False):
        """Download and forward album media."""
        try:
            file_paths = []
            backup_paths = []
            ts_str = dt.now().strftime('%Y%m%d_%H%M%S')
            ttl_val = getattr(messages[0].media, 'ttl_seconds', None) if messages[0].media else None

            for idx, msg in enumerate(messages):
                if not msg.media:
                    continue
                ext = 'jpg' if (hasattr(msg.media, 'photo') and msg.media.photo) else 'mp4'
                stem = self.build_filename_stem(username, chat_id, ts_str, index=idx)
                temp_filename = f"{stem}.{ext}"

                path = await self.client.download_media(msg.media, temp_filename)
                if path:
                    file_paths.append(path)
                    if self.save_local_backup:
                        dest = self.local_backup_dir / Path(path).name
                        shutil.copy2(path, dest)
                        backup_paths.append(str(dest))

            if not file_paths:
                return

            caption = self.build_caption(messages[0], chat_id, username, is_reply=is_reply, is_album=True)
            label = f"{chat_title}{' (replied message)' if is_reply else ''}"
            self.log("info", f"Intercepted secret album ({len(file_paths)} items) from {label}. Saving to Saved Messages...")

            file_handles = [open(p, 'rb') for p in file_paths]
            try:
                await self.client.send_file('me', file_handles, caption=caption, parse_mode='html')
            finally:
                for fh in file_handles:
                    fh.close()

            self.log("success", f"Saved secret album ({len(file_paths)} items) from {label} to your Telegram Saved Messages.")

            # Notify GUI of intercepted media
            if self.on_media_captured:
                self.on_media_captured({
                    "type": "album",
                    "count": len(file_paths),
                    "chat_title": chat_title,
                    "chat_id": chat_id,
                    "username": username,
                    "is_reply": is_reply,
                    "ttl_seconds": ttl_val,
                    "timestamp": self.get_formatted_timestamp(),
                    "local_files": backup_paths,
                    "message_id": messages[0].id
                })

            # Cleanup temp files
            for p in file_paths:
                try:
                    if os.path.exists(p):
                        os.remove(p)
                except Exception:
                    pass

        except Exception as e:
            self.log("error", f"Failed to process album: {str(e)}")

    async def process_single_media(self, message: Any, chat_title: str, chat_id: int, username: Optional[str], is_reply: bool = False):
        """Process single self-destructing photo or video."""
        try:
            caption = self.build_caption(message, chat_id, username, is_reply=is_reply, is_album=False)
            label = f"{chat_title}{' (replied message)' if is_reply else ''}"
            ts_str = dt.now().strftime('%Y%m%d_%H%M%S')
            stem = self.build_filename_stem(username, chat_id, ts_str)
            ttl_val = getattr(message.media, 'ttl_seconds', None)

            if hasattr(message.media, 'photo') and message.media.photo:
                media_type = 'photo'
                ext = 'jpg'
            elif hasattr(message.media, 'document') and message.media.document:
                media_type = 'video'
                ext = 'mp4'
            else:
                media_type = 'media'
                ext = 'dat'

            self.log("info", f"Intercepted secret {media_type} (TTL: {ttl_val}s) from {label}. Downloading...")
            temp_path = await self.client.download_media(message.media, f"{stem}.{ext}")

            if temp_path:
                backup_path = None
                if self.save_local_backup:
                    dest = self.local_backup_dir / Path(temp_path).name
                    shutil.copy2(temp_path, dest)
                    backup_path = str(dest)

                with open(temp_path, 'rb') as file:
                    await self.client.send_file('me', file, caption=caption, parse_mode='html')

                self.log("success", f"Secret {media_type} from {label} saved to Saved Messages!")

                if self.on_media_captured:
                    self.on_media_captured({
                        "type": media_type,
                        "count": 1,
                        "chat_title": chat_title,
                        "chat_id": chat_id,
                        "username": username,
                        "is_reply": is_reply,
                        "ttl_seconds": ttl_val,
                        "timestamp": self.get_formatted_timestamp(),
                        "local_files": [backup_path] if backup_path else [],
                        "message_id": message.id
                    })

                try:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                except Exception:
                    pass

        except Exception as e:
            self.log("error", f"Failed to process secret {media_type}: {str(e)}")

    async def flush_album(self, key: tuple, chat_title: str, chat_id: int, username: Optional[str], is_reply: bool = False):
        """Wait debounce interval then process grouped album messages."""
        await asyncio.sleep(self.album_debounce_sec)
        messages = self.album_buffer.pop(key, [])
        self.album_tasks.pop(key, None)
        if messages:
            messages.sort(key=lambda m: m.id)
            await self.process_album(messages, chat_title, chat_id, username, is_reply=is_reply)

    async def handle_incoming_message(self, message: Any, chat_title: str, chat_id: int, username: Optional[str], is_reply: bool = False):
        """Route message to single handler or album buffer."""
        if not self.is_self_destructive(message):
            return

        grouped_id = getattr(message, 'grouped_id', None)
        if grouped_id:
            key = (chat_id, grouped_id)
            if key not in self.album_buffer:
                self.album_buffer[key] = []
            self.album_buffer[key].append(message)

            if key in self.album_tasks and not self.album_tasks[key].done():
                self.album_tasks[key].cancel()

            self.album_tasks[key] = asyncio.create_task(
                self.flush_album(key, chat_title, chat_id, username, is_reply=is_reply)
            )
        else:
            await self.process_single_media(message, chat_title, chat_id, username, is_reply=is_reply)

    def register_listeners(self):
        """Register Telethon event listeners."""
        @self.client.on(events.NewMessage)
        async def on_new_message(event):
            try:
                chat = await event.get_chat()
                chat_title = getattr(chat, 'title', getattr(chat, 'first_name', 'Unknown Chat'))
                username = getattr(chat, 'username', None)
            except Exception as e:
                self.log("warning", f"Could not get chat info: {e}")
                chat_title = f"Chat {event.chat_id}"
                username = None

            # Handle direct media
            if event.message.media:
                await self.handle_incoming_message(event.message, chat_title, event.chat_id, username, is_reply=False)

            # Handle replied message media
            if event.message.reply_to_msg_id:
                try:
                    replied_msg = await event.get_reply_message()
                    if replied_msg and replied_msg.media:
                        await self.handle_incoming_message(replied_msg, chat_title, event.chat_id, username, is_reply=True)
                except Exception as e:
                    self.log("error", f"Failed inspecting reply message: {e}")

    async def start_monitoring(self):
        """Start listening for incoming self-destructive media."""
        if not self.client or not await self.client.is_user_authorized():
            self.log("error", "Client is not authorized. Cannot start monitoring.")
            return

        self.is_monitoring = True
        self.register_listeners()
        if self.on_status_changed:
            self.on_status_changed("listening")
        self.log("success", "🚀 Interceptor engine ACTIVE. Listening for secret photos, videos & albums...")
        await self.client.run_until_disconnected()

    async def stop_monitoring(self):
        """Stop listening and disconnect."""
        self.is_monitoring = False
        if self.on_status_changed:
            self.on_status_changed("idle")
        if self.client and self.client.is_connected():
            await self.client.disconnect()
            self.log("info", "Disconnected from Telegram.")
