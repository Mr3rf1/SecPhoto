# https://github.com/Dr-Muh/SecPhoto

import os
import json
from pathlib import Path
api_id = int(os.environ["TG_API_ID"])
api_hash = os.environ["TG_API_HASH"]
excluded_users_raw = os.environ.get("TG_EXCLUDED_USERS", "")
excluded_users = {
    entry.strip().lower()
    for entry in excluded_users_raw.split(",")
    if entry.strip()
}
timezone_name = os.environ.get("TZ", "Europe/Berlin")
archive_state_path = Path(
    os.environ.get("TG_ARCHIVE_STATE_PATH", "/app/data/archive_state.json")
)

async def main():
    try:
        from telethon import TelegramClient, events
        from telethon.errors import FloodWaitError, SessionPasswordNeededError
        from socks import SOCKS5
        from argparse import ArgumentParser
        import os
        import getpass
        import re
        import asyncio
        from datetime import datetime
        from zoneinfo import ZoneInfo
        import sqlite3
        from telethon.tl.functions.channels import CreateChannelRequest
        from telethon.tl.types import User
        from telethon.utils import get_peer_id
    except ImportError:
        print(' [!] Please install dependencies~> python3 -m pip install -r requirements.txt')
        exit(0)

    try:
        app_timezone = ZoneInfo(timezone_name)
    except Exception as e:
        print(f"Invalid TG_TIMEZONE value '{timezone_name}': {str(e)}")
        exit(0)

    # Album buffer: grouped_id -> list of messages, keyed per chat
    # Structure: { (chat_id, grouped_id): [msg, ...] }
    album_buffer = {}
    album_tasks = {}

    def get_phone_number():
        """Get phone number with validation for international format"""
        while True:
            phone = input("Enter your phone number with country code, e.g., +1234567890: ").strip()
            if re.match(r'^\+[1-9]\d{1,14}$', phone):
                return phone
            else:
                print("Invalid phone number format. Please use international format, for example +1234567890.")

    async def authenticate_user(client):
        """Authenticate user with proper checking and interactive input"""
        try:
            me = await client.get_me()
            if me:
                print(f"Already authenticated as: {me.first_name}")
                return True
        except Exception:
            pass

        print("Authentication required...")
        phone_number = get_phone_number()

        try:
            sent_code_request = await client.send_code_request(phone=phone_number)
            code = input("Enter your verification code: ")
            try:
                await client.sign_in(
                    phone=phone_number,
                    code=code,
                    phone_code_hash=sent_code_request.phone_code_hash,
                )
                print("Successfully authenticated!")
                return True
            except SessionPasswordNeededError:
                password = getpass.getpass("Enter your 2FA password: ")
                await client.sign_in(password=password)
                print("Successfully authenticated with 2FA!")
                return True
        except Exception as e:
            print(f"Authentication failed: {str(e)}")
            return False

    parser = ArgumentParser(add_help=False)
    parser.add_argument('-p', '--proxy')
    parser.add_argument('-help', '--help', action='store_true')
    argv = parser.parse_args()

    if argv.proxy is not None:
        ip = argv.proxy.split(':')[0]
        port = int(argv.proxy.split(':')[1])
        client = TelegramClient('/app/data/session', api_id, api_hash, proxy=(SOCKS5, ip, port))
    else:
        client = TelegramClient('/app/data/session', api_id, api_hash)

    if argv.help:
        print("Saves Telegram self-destructing photos and videos.")
        print("-p or --proxy IP:PORT sets a SOCKS5 proxy.")
        print("Example: -p 127.0.0.1:9050")
        print("TG_EXCLUDED_USERS can hold comma-separated usernames or user IDs to skip.")
        print("The tool monitors chats for self-destructing media and saves it.")
        print("It also checks replied messages and supports grouped media.")
        exit(0)

    print('Starting to monitor all chats for self-destructive media...')

    # Connect to Telegram with database lock fix
    try:
        await client.connect()
    except sqlite3.OperationalError as e:
        if "database is locked" in str(e).lower():
            print("[!] Session database is locked. Deleting and creating a new one...")
            session_file = f"{client.session.filename}.session"
            journal_file = f"{client.session.filename}.session-journal"
            for f in [session_file, journal_file]:
                if os.path.exists(f):
                    try:
                        os.remove(f)
                        print(f"Deleted: {f}")
                    except Exception as err:
                        print(f"Could not delete {f}: {err}")
            client = TelegramClient(client.session.filename, api_id, api_hash)
            await client.connect()
        else:
            raise

    if not await authenticate_user(client):
        print('Authentication failed. Exiting...')
        await client.disconnect()
        return

    def load_archive_state():
        if not archive_state_path.exists():
            return {}
        try:
            return json.loads(archive_state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            print(f"Could not read archive state: {str(e)}")
            return {}

    def save_archive_state(state):
        archive_state_path.parent.mkdir(parents=True, exist_ok=True)
        archive_state_path.write_text(
            json.dumps(state, ensure_ascii=True, indent=2), encoding="utf-8"
        )

    archive_state = load_archive_state()
    archive_lock = asyncio.Lock()

    async def create_private_channel(title, about):
        result = await client(CreateChannelRequest(
            title=title,
            about=about,
            broadcast=True,
            megagroup=False,
        ))
        return result.chats[0]

    async def discover_archive_state():
        """Recover state from a metadata message in an existing archive channel."""
        if archive_state.get("archive"):
            return
        async for dialog in client.iter_dialogs():
            channel = dialog.entity
            title = getattr(channel, "title", "")
            if not getattr(channel, "broadcast", False) or not title.startswith("SecPhoto Archive - "):
                continue
            async for message in client.iter_messages(channel, limit=20):
                marker = message.raw_text or ""
                if marker.startswith("[SecPhoto metadata] source_id="):
                    source_id = marker.split("source_id=", 1)[1].split(" ", 1)[0]
                    archive_state["archive"] = {
                        "source_id": int(source_id),
                        "archive_id": get_peer_id(channel),
                        "source": marker.split(" source=", 1)[-1],
                    }
                    save_archive_state(archive_state)
                    print(f"Recovered archive state from {title}")
                    return

    async def get_command_channel():
        channel_id = os.environ.get("TG_COMMAND_CHANNEL_ID")
        if channel_id:
            return await client.get_entity(int(channel_id))

        saved_id = archive_state.get("command_channel_id")
        if saved_id:
            try:
                return await client.get_entity(int(saved_id))
            except Exception:
                print("Saved command channel is unavailable; creating a new one")

        channel = await create_private_channel(
            "SecPhoto Commands",
            "Private command channel for SecPhoto chat archives.",
        )
        archive_state["command_channel_id"] = get_peer_id(channel)
        save_archive_state(archive_state)
        print(f"Created private command channel: {get_peer_id(channel)}")
        return channel

    command_channel = await get_command_channel()
    command_channel_id = get_peer_id(command_channel)
    await discover_archive_state()

    async def notify_command(text):
        try:
            await client.send_message(command_channel, text)
        except FloodWaitError as e:
            print(f"Could not notify command channel; flood wait is {e.seconds} seconds")
        except Exception as e:
            print(f"Could not notify command channel: {e}")

    def archive_config():
        return archive_state.get("archive")

    async def copy_message_to_archive(message, source, archive_channel):
        """Copy one message, falling back when forwarding is restricted."""
        try:
            copied = await client.forward_messages(
                archive_channel, message, from_peer=source
            )
            return copied[0] if isinstance(copied, list) else copied
        except FloodWaitError:
            raise
        except Exception:
            temp_dir = Path("/app/data/archive_tmp")
            temp_dir.mkdir(parents=True, exist_ok=True)
            temp_path = await client.download_media(message, str(temp_dir)) if message.media else None
            try:
                if temp_path:
                    return await client.send_file(
                        archive_channel, temp_path, caption=message.message or ""
                    )
                if message.message:
                    return await client.send_message(archive_channel, message.message)
                return await client.send_message(archive_channel, "[Message without text]")
            finally:
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)

    async def backfill_archive(source, archive_channel):
        count = 0
        last_message_id = archive_config().get("last_source_message_id", 0)
        async for message in client.iter_messages(source, reverse=True):
            if message.id <= last_message_id:
                continue
            try:
                await copy_message_to_archive(message, source, archive_channel)
            except FloodWaitError as e:
                save_archive_state(archive_state)
                print(
                    f"Telegram flood wait: pause for {e.seconds} seconds. "
                    "Archive progress was saved; run the archive command again later."
                )
                return count, True
            archive_state["archive"]["last_source_message_id"] = message.id
            save_archive_state(archive_state)
            count += 1
            if count % 100 == 0:
                print(f"Archived {count} messages...")
        return count, False

    async def report_command_error(message):
        print(f"Command failed: {message}")
        await notify_command(message)

    async def create_or_sync_archive(chat_spec):
        async with archive_lock:
            source = await client.get_entity(chat_spec)
            source_id = get_peer_id(source)
            existing = archive_config()
            if existing and existing.get("source_id") == source_id:
                archive_channel = await client.get_entity(int(existing["archive_id"]))
                await notify_command(f"Syncing existing archive for {chat_spec}...")
            else:
                title = getattr(source, "title", None) or getattr(source, "first_name", None) or str(chat_spec)
                archive_channel = await create_private_channel(
                    f"SecPhoto Archive - {title}"[:128],
                    f"Private copy of {title} created by SecPhoto.",
                )
                archive_state["archive"] = {
                    "source_id": source_id,
                    "archive_id": get_peer_id(archive_channel),
                    "source": str(chat_spec),
                    "last_source_message_id": 0,
                }
                save_archive_state(archive_state)
                await client.send_message(
                    archive_channel,
                    f"[SecPhoto metadata] source_id={source_id} source={chat_spec}",
                )

            count, paused = await backfill_archive(source, archive_channel)
            if paused:
                print(f"Archive paused after copying {count} messages. Run /archive {chat_spec} later to resume.")
                return
            await notify_command(
                f"Archive ready for {chat_spec}. Copied {count} new messages. "
                "New messages will be mirrored automatically."
            )

    async def handle_command(event):
        command = (event.raw_text or "").strip()
        if command.startswith("/archive "):
            try:
                await create_or_sync_archive(command.split(None, 1)[1].strip())
            except Exception as e:
                await report_command_error(f"Archive failed: {str(e)}")
        elif command.startswith("/archive-adopt "):
            try:
                archive_spec, source_spec = command.split(None, 2)[1:]
                source = await client.get_entity(source_spec)
                archive_channel = await client.get_entity(archive_spec)
                latest_source = await client.get_messages(source, limit=1)
                archive_state["archive"] = {
                    "source_id": get_peer_id(source),
                    "archive_id": get_peer_id(archive_channel),
                    "source": str(source_spec),
                    "last_source_message_id": latest_source[0].id if latest_source else 0,
                }
                save_archive_state(archive_state)
                await notify_command(
                    "Existing archive adopted. New source messages will be mirrored."
                )
            except Exception as e:
                await report_command_error(f"Adoption failed: {str(e)}")
        elif command == "/archive-status":
            config = archive_config()
            if config:
                await notify_command(
                    f"Source: {config['source']}\nArchive channel ID: {config['archive_id']}\n"
                    f"Last source message: {config.get('last_source_message_id', 0)}"
                )
            else:
                await notify_command("No archive configured. Use /archive <chat>.")
        elif command == "/archive-stop":
            archive_state.pop("archive", None)
            save_archive_state(archive_state)
            await notify_command("Live archive mirroring stopped.")

    def build_filename(username, chat_id, timestamp, index=None):
        """Build a filename stem as USERNAME(or id)_TIMESTAMP[_index]"""
        name = username if username else str(chat_id)
        # Sanitize for filesystem
        name = re.sub(r'[\\/:*?"<>|]', '_', name)
        stem = f"{name}_{timestamp}"
        if index is not None:
            stem = f"{stem}_{index}"
        return stem

    def is_excluded_user(chat_id, username):
        """Return True when the chat user matches TG_EXCLUDED_USERS."""
        if username and username.lower() in excluded_users:
            return True

        chat_id_text = str(chat_id)
        return chat_id_text in excluded_users or f"@{chat_id_text}" in excluded_users

    def build_caption(message, chat_id, username, is_reply=False, is_album=False):
        """Build the formatted caption for a saved media message"""
        lines = []
        if is_reply:
            lines.append("Replied Message")

        lines.append(f'Chat ID: <a href="tg://user?id={chat_id}">{chat_id}</a>')
        if is_album:
            lines.append('Album: YES')
        lines.append(f"Username: {'@' + username if username else 'None'}")
        lines.append(f"Message ID: {message.id}")
        lines.append(f"Date Time: {datetime.now(app_timezone).strftime('%Y/%m/%d %H:%M:%S')}")
        return '\n'.join(lines) + '\n'

    async def process_album(messages, chat_title, chat_id, username, is_reply=False):
        """Download and forward an album (grouped media) as a single album"""
        try:
            file_paths = []
            for msg in messages:
                if not msg.media:
                    continue
                ext = 'jpg' if hasattr(msg.media, 'photo') and msg.media.photo else 'media'
                ts = datetime.now(app_timezone).strftime('%Y%m%d_%H%M%S')
                stem = build_filename(username, chat_id, ts, index=len(file_paths))
                path = await client.download_media(msg.media, f'{stem}.{ext}')
                if path:
                    file_paths.append(path)

            if not file_paths:
                return

            caption = build_caption(messages[0], chat_id, username, is_reply=is_reply, is_album=True)
            label = chat_title + (' (replied message)' if is_reply else '')
            print(f'Saving album ({len(file_paths)} items) from {label}...', end='')

            file_handles = [open(p, 'rb') for p in file_paths]
            try:
                await client.send_file('me', file_handles, caption=caption, parse_mode='html')
            finally:
                for fh in file_handles:
                    fh.close()

            print(f'\rAlbum ({len(file_paths)} items) from {label} saved to Saved Messages')

            for p in file_paths:
                try:
                    os.remove(p)
                except Exception:
                    pass
        except Exception as e:
            print(f'Failed to process album: {str(e)}')

    async def process_single_media(message, chat_title, chat_id, username, is_reply=False):
        """Process a single self-destructive media message"""
        try:
            caption = build_caption(message, chat_id, username, is_reply=is_reply, is_album=False)
            label = chat_title + (' (replied message)' if is_reply else '')

            ts = datetime.now(app_timezone).strftime('%Y%m%d_%H%M%S')
            stem = build_filename(username, chat_id, ts)

            if hasattr(message.media, 'photo') and message.media.photo:
                print(f'Found self-destructing photo in {label}. Downloading...', end='')
                file_path = await client.download_media(message.media, f'{stem}.jpg')
                media_type = 'photo'
            elif hasattr(message.media, 'document') and message.media.document:
                print(f'Found self-destructing media in {label}. Downloading...', end='')
                file_path = await client.download_media(message.media, f'{stem}.media')
                media_type = 'media'
            else:
                return

            if file_path:
                with open(file_path, 'rb') as file:
                    await client.send_file('me', file, caption=caption, parse_mode='html')
                print(f'\rSaved {media_type} from {label} to Saved Messages')
                os.remove(file_path)
        except Exception as e:
            print(f'Failed to process self-destructive media: {str(e)}')

    def is_self_destructive(message):
        """Return True if the message contains self-destructive (ttl) media"""
        return (
            message.media is not None
            and hasattr(message.media, 'ttl_seconds')
            and message.media.ttl_seconds
        )

    async def flush_album(key, chat_title, chat_id, username, is_reply=False):
        """Wait briefly to collect all album parts, then process them together"""
        await asyncio.sleep(0.6)  # short debounce to gather all grouped messages
        messages = album_buffer.pop(key, [])
        album_tasks.pop(key, None)
        if messages:
            # Sort by message id to preserve order
            messages.sort(key=lambda m: m.id)
            await process_album(messages, chat_title, chat_id, username, is_reply=is_reply)

    async def handle_message(message, chat_title, chat_id, username, is_reply=False):
        """Route a message to single or album processing based on grouped_id"""
        if not is_self_destructive(message):
            return

        grouped_id = getattr(message, 'grouped_id', None)

        if grouped_id:
            key = (chat_id, grouped_id)
            if key not in album_buffer:
                album_buffer[key] = []
            album_buffer[key].append(message)

            # Cancel existing flush task and restart debounce timer
            if key in album_tasks and not album_tasks[key].done():
                album_tasks[key].cancel()
            album_tasks[key] = asyncio.ensure_future(
                flush_album(key, chat_title, chat_id, username, is_reply=is_reply)
            )
        else:
            await process_single_media(message, chat_title, chat_id, username, is_reply=is_reply)

    @client.on(events.NewMessage)
    async def handler(event):
        if event.chat_id == command_channel_id:
            await handle_command(event)
            return

        try:
            chat = await event.get_chat()
            chat_title = getattr(chat, 'title', getattr(chat, 'first_name', 'Unknown'))
            username = getattr(chat, 'username', None)
        except Exception as e:
            print(f'Could not get chat info: {str(e)}')
            return

        if is_excluded_user(event.chat_id, username):
            print(f'Skipping excluded user or chat: {chat_title}')
            return

        config = archive_config()
        if config and event.chat_id == config["source_id"]:
            try:
                archive_channel = await client.get_entity(int(config["archive_id"]))
                await copy_message_to_archive(event.message, chat, archive_channel)
            except Exception as e:
                print(f"Failed to mirror message {event.message.id}: {str(e)}")

        # Handle current message (single or album)
        if event.message.media:
            await handle_message(event.message, chat_title, event.chat_id, username, is_reply=False)

        # Handle replied-to message if present
        if event.message.reply_to_msg_id:
            try:
                replied_message = await event.get_reply_message()
                if replied_message and replied_message.media:
                    await handle_message(replied_message, chat_title, event.chat_id, username, is_reply=True)
            except Exception as e:
                print(f'Failed to process replied message: {str(e)}')

    @client.on(events.MessageDeleted)
    async def deleted_handler(event):
        """Notify Saved Messages when Telegram reports deleted messages."""
        if event.chat_id is None:
            return

        try:
            chat = await event.get_chat()
            chat_title = getattr(chat, "title", None) or getattr(chat, "first_name", None) or str(event.chat_id)
        except Exception:
            chat = None
            chat_title = str(event.chat_id)

        if isinstance(chat, User):
            deleted_count = len(event.deleted_ids)
            await client.send_message(
                "me",
                f"{deleted_count} message{'s' if deleted_count != 1 else ''} deleted in {chat_title}. "
                "Telegram did not provide the deleting user's identity.",
            )
            print(f"Notified Saved Messages about {deleted_count} deleted message(s) in {chat_title}")

        config = archive_config()
        if config and event.chat_id == config["source_id"]:
            try:
                archive_channel = await client.get_entity(int(config["archive_id"]))
                for message_id in event.deleted_ids:
                    await client.send_message(
                        archive_channel,
                        f"Source message {message_id} was deleted. The archived copy is retained.",
                    )
            except Exception as e:
                print(f"Failed to record deleted archive messages: {str(e)}")


    await client.run_until_disconnected()

if '__main__' == __name__:
    try:
        import asyncio
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Bye :)')
