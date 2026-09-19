# t.me/Mr3rf1  |  @rickmorti12

import os
import re
import shutil
import sqlite3
import getpass
import hashlib
import tempfile
import html as htmllib
from argparse import ArgumentParser

# Credentials can be set via environment variables:
#   export TG_API_ID=123456
#   export TG_API_HASH=your_real_hash
API_ID = int(os.environ.get("TG_API_ID", "1234567"))  # set your own api_id
API_HASH = os.environ.get("TG_API_HASH", "82bd7b4562f7ju24d182bdc38huj9352")  # set your own api_hash

SESSION_NAME = "secret"

try:
    from telethon import TelegramClient, events
    from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError
    from colorama import Fore
    from socks import SOCKS5
    import jdatetime
    from pytz import timezone
except ImportError:
    print(" [!] Please install dependencies~> python3 -m pip install -r requirements.txt")
    raise SystemExit(0)

HELP_TEXT = rf"""  ____            ____  _           _
 / ___|  ___  ___|  _ \| |__   ___ | |_ ___
 \___ \ / _ \/ __| |_) | '_ \ / _ \| __/ _ \
  ___) |  __/ (__|  __/| | | | (_) | || (_) |
 |____/ \___|\___|_|   |_| |_|\___/ \__\___/

      a tool for save telegram {Fore.GREEN}self destructing photo/video{Fore.RESET}
      github.com/{Fore.BLUE}Mr3rf1                        {Fore.RESET}t.me/{Fore.BLUE}Mr3rf1{Fore.RESET}

      {Fore.LIGHTMAGENTA_EX}-p{Fore.RESET} or {Fore.LIGHTMAGENTA_EX}--proxy {Fore.LIGHTCYAN_EX}IP:PORT{Fore.RESET} ~> set socks5 proxy (tor)
      example: {Fore.LIGHTMAGENTA_EX}-p {Fore.LIGHTCYAN_EX}127.0.0.1:9050{Fore.RESET}

      {Fore.LIGHTMAGENTA_EX}-d{Fore.RESET} or {Fore.LIGHTMAGENTA_EX}--save-dir {Fore.LIGHTCYAN_EX}DIR{Fore.RESET} ~> also keep a local copy in DIR
      example: {Fore.LIGHTMAGENTA_EX}-d {Fore.LIGHTCYAN_EX}./saved{Fore.RESET}

      This tool monitors incoming chats for self-destructive media and saves them
      to your Saved Messages.
    """


def get_file_hash(file_path):
    """Compute SHA256 hash for a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def get_phone_number():
    """Get phone number with validation for international format."""
    while True:
        phone = input(
            f" {Fore.YELLOW}[{Fore.GREEN}<{Fore.YELLOW}]{Fore.RESET} "
            "Enter your phone number (with country code, e.g., +1234567890): "
        ).strip()
        if re.match(r"^\+[1-9]\d{1,14}$", phone):
            return phone
        print(
            f" {Fore.YELLOW}[{Fore.RED}!{Fore.YELLOW}]{Fore.RESET} "
            "Invalid phone number format. Please use international format (e.g., +1234567890)"
        )


def parse_proxy(value):
    """Parse 'IP:PORT' safely. Returns (ip, port) or exits with a clear message."""
    try:
        ip, port = value.rsplit(":", 1)
        port = int(port)
        if not ip or not (0 < port < 65536):
            raise ValueError
        return ip, port
    except ValueError:
        print(f" {Fore.YELLOW}[{Fore.RED}ERROR{Fore.YELLOW}]{Fore.RESET} Invalid proxy. Use IP:PORT, e.g. 127.0.0.1:9050")
        raise SystemExit(1)


async def authenticate_user(client):
    """Authenticate the user (skips login if the saved session is still valid)."""
    if await client.is_user_authorized():
        me = await client.get_me()
        print(f" {Fore.YELLOW}[{Fore.GREEN}!{Fore.YELLOW}]{Fore.RESET} Already authenticated as: {me.first_name}")
        return True

    print(f" {Fore.YELLOW}[{Fore.CYAN}!{Fore.YELLOW}]{Fore.RESET} Authentication required...")
    phone_number = get_phone_number()

    try:
        sent = await client.send_code_request(phone=phone_number)

        for attempt in range(3):  # allow a couple of typos in the code
            code = input(f" {Fore.YELLOW}[{Fore.GREEN}<{Fore.YELLOW}]{Fore.RESET} Enter your verification code: ").strip()
            try:
                await client.sign_in(phone=phone_number, code=code, phone_code_hash=sent.phone_code_hash)
                break
            except PhoneCodeInvalidError:
                print(f" {Fore.YELLOW}[{Fore.RED}!{Fore.YELLOW}]{Fore.RESET} Wrong code, try again ({2 - attempt} left).")
            except SessionPasswordNeededError:
                password = getpass.getpass(f" {Fore.YELLOW}[{Fore.GREEN}<{Fore.YELLOW}]{Fore.RESET} Enter your 2FA password: ")
                await client.sign_in(password=password)
                break
        else:
            print(f" {Fore.YELLOW}[{Fore.RED}ERROR{Fore.YELLOW}]{Fore.RESET} Too many wrong codes.")
            return False

        print(f" {Fore.YELLOW}[{Fore.GREEN}!{Fore.YELLOW}]{Fore.RESET} Successfully authenticated!")
        return True
    except Exception as e:
        print(f" {Fore.YELLOW}[{Fore.RED}ERROR{Fore.YELLOW}]{Fore.RESET} Authentication failed: {e}")
        return False


async def main():
    parser = ArgumentParser(add_help=False)
    parser.add_argument("-p", "--proxy")
    parser.add_argument("-d", "--save-dir")
    parser.add_argument("-help", "--help", action="store_true")
    argv = parser.parse_args()

    # Show help before touching the network or session file.
    if argv.help:
        print(HELP_TEXT)
        return

    if API_ID == 1234567:
        print(f" {Fore.YELLOW}[{Fore.RED}ERROR{Fore.YELLOW}]{Fore.RESET} Set your own api_id/api_hash "
              "(https://my.telegram.org) via TG_API_ID / TG_API_HASH env vars or in the file.")
        return

    if argv.save_dir:
        os.makedirs(argv.save_dir, exist_ok=True)

    proxy = None
    if argv.proxy:
        ip, port = parse_proxy(argv.proxy)
        proxy = (SOCKS5, ip, port)

    seen_hashes = set()  # duplicate detection (this run only)

    # Create client and connect. A locked DB usually means another instance is running.
    try:
        client = TelegramClient(SESSION_NAME, API_ID, API_HASH, proxy=proxy)
        await client.connect()
    except sqlite3.OperationalError as e:
        if "locked" in str(e).lower():
            print(f" {Fore.YELLOW}[{Fore.RED}ERROR{Fore.YELLOW}]{Fore.RESET} Session database is locked. "
                  "Another SecPhoto instance is probably running - close it and try again.")
            return
        raise

    try:
        if not await authenticate_user(client):
            print(f" {Fore.YELLOW}[{Fore.RED}ERROR{Fore.YELLOW}]{Fore.RESET} Authentication failed. Exiting...")
            return

        # incoming=True: ignore our own outgoing messages (including Saved Messages)
        @client.on(events.NewMessage(incoming=True))
        async def handler(event):
            media = event.message.media
            if not media or not getattr(media, "ttl_seconds", None):
                return

            is_photo = bool(getattr(media, "photo", None))
            is_document = bool(getattr(media, "document", None))
            if not (is_photo or is_document):
                return
            kind = "photo" if is_photo else "media"

            # Separate temp dir per message so parallel downloads don't collide.
            tmp_dir = tempfile.mkdtemp(prefix="secphoto_")
            chat_title = "Unknown"
            try:
                chat = await event.get_chat()
                chat_title = getattr(chat, "title", None) or getattr(chat, "first_name", None) or "Unknown"
                username = getattr(chat, "username", None)

                # tg://user?id= only works for private chats; escape everything for HTML mode.
                chat_id_html = (
                    f'<a href="tg://user?id={event.chat_id}">{event.chat_id}</a>'
                    if event.is_private else str(event.chat_id)
                )
                now = jdatetime.datetime.now(timezone("Asia/Tehran")).strftime("%Y/%m/%d %H:%M:%S")
                caption = (
                    f"┏ᑕᕼᗩT Iᗪ ⤳ {chat_id_html}\n"
                    f"┣ᑌՏᗴᖇᑎᗩᗰᗴ ⤳ {'@' + htmllib.escape(username) if username else '✗'}\n"
                    f"┣ᗰᗴՏՏᗩᘜᗴ Iᗪ ⤳ {event.message.id}\n"
                    f"┣ᗪᗩTᗴ TIᗰᗴ ⤳ {now}\n"
                    f"┗ github.com/Mr3rf1"
                )

                print(f" {Fore.YELLOW}[{Fore.RED}!{Fore.YELLOW}]{Fore.RESET} Found self-destructive {kind} in {chat_title}. Downloading...")
                file_path = await client.download_media(event.message, file=tmp_dir)

                if not file_path:
                    print(f" {Fore.YELLOW}[{Fore.RED}!{Fore.YELLOW}]{Fore.RESET} Download failed (media may have already expired).")
                    return

                media_hash = get_file_hash(file_path)
                if media_hash in seen_hashes:
                    print(f" {Fore.YELLOW}[{Fore.RED}!{Fore.YELLOW}]{Fore.RESET} Duplicate {kind} detected - skipping.")
                    return
                seen_hashes.add(media_hash)

                # Pass the path (not an open handle) so Telegram keeps the real filename/extension.
                await client.send_file("me", file_path, caption=caption, parse_mode="html")

                if argv.save_dir:
                    ext = os.path.splitext(file_path)[1]
                    dest = os.path.join(argv.save_dir, f"{event.chat_id}_{event.message.id}{ext}")
                    shutil.copy2(file_path, dest)

                print(f" {Fore.YELLOW}[{Fore.GREEN}!{Fore.YELLOW}]{Fore.RESET} Secret {kind} from {chat_title} saved to your messages")

            except Exception as e:
                print(f" {Fore.YELLOW}[{Fore.RED}ERROR{Fore.YELLOW}]{Fore.RESET} Failed to process self-destructive media from {chat_title}: {e}")
            finally:
                shutil.rmtree(tmp_dir, ignore_errors=True)  # always clean up, even on errors/skips

        print(f" {Fore.YELLOW}[{Fore.GREEN}!{Fore.YELLOW}]{Fore.RESET} Monitoring incoming chats for self-destructive media... (Ctrl+C to stop)")
        await client.run_until_disconnected()
    finally:
        await client.disconnect()


if __name__ == "__main__":
    try:
        import asyncio
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bye :)")
