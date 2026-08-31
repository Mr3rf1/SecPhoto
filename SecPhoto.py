# t.me/Mr3rf1

api_id = 1234567  # set your own api_id
api_hash = "82bd7b4562f7ju24d182bdc38huj9352"  # set your own api_key

async def main():
    try:
        from telethon import TelegramClient, events
        from telethon.errors import SessionPasswordNeededError
        from colorama import Fore
        from socks import SOCKS5
        from argparse import ArgumentParser
        import os
        import getpass
        import re
        import asyncio
        from jdatetime import datetime
        from pytz import timezone
        import sqlite3
    except ImportError:
        print(' [!] Please install dependencies~> python3 -m pip install -r requirements.txt')
        exit(0)

    # Album buffer: grouped_id -> list of messages, keyed per chat
    # Structure: { (chat_id, grouped_id): [msg, ...] }
    album_buffer = {}
    album_tasks = {}

    def get_phone_number():
        """Get phone number with validation for international format"""
        while True:
            phone = input(f" {Fore.YELLOW}[{Fore.GREEN}<{Fore.YELLOW}]{Fore.RESET} Enter your phone number (with country code, e.g., +1234567890): ").strip()
            if re.match(r'^\+[1-9]\d{1,14}$', phone):
                return phone
            else:
                print(f" {Fore.YELLOW}[{Fore.RED}!{Fore.YELLOW}]{Fore.RESET} Invalid phone number format. Please use international format (e.g., +1234567890)")

    async def authenticate_user(client):
        """Authenticate user with proper checking and interactive input"""
        try:
            me = await client.get_me()
            if me:
                print(f" {Fore.YELLOW}[{Fore.GREEN}!{Fore.YELLOW}]{Fore.RESET} Already authenticated as: {me.first_name}")
                return True
        except Exception:
            pass

        print(f" {Fore.YELLOW}[{Fore.CYAN}!{Fore.YELLOW}]{Fore.RESET} Authentication required...")
        phone_number = get_phone_number()

        try:
            sent_code_request = await client.send_code_request(phone=phone_number)
            code = input(f" {Fore.YELLOW}[{Fore.GREEN}<{Fore.YELLOW}]{Fore.RESET} Enter your verification code: ")
            try:
                await client.sign_in(
                    phone=phone_number,
                    code=code,
                    phone_code_hash=sent_code_request.phone_code_hash,
                )
                print(f" {Fore.YELLOW}[{Fore.GREEN}!{Fore.YELLOW}]{Fore.RESET} Successfully authenticated!")
                return True
            except SessionPasswordNeededError:
                password = getpass.getpass(f" {Fore.YELLOW}[{Fore.GREEN}<{Fore.YELLOW}]{Fore.RESET} Enter your 2FA password: ")
                await client.sign_in(password=password)
                print(f" {Fore.YELLOW}[{Fore.GREEN}!{Fore.YELLOW}]{Fore.RESET} Successfully authenticated with 2FA!")
                return True
        except Exception as e:
            print(f" {Fore.YELLOW}[{Fore.RED}ERROR{Fore.YELLOW}]{Fore.RESET} Authentication failed: {str(e)}")
            return False

    parser = ArgumentParser(add_help=False)
    parser.add_argument('-p', '--proxy')
    parser.add_argument('-help', '--help', action='store_true')
    argv = parser.parse_args()

    if argv.proxy is not None:
        ip = argv.proxy.split(':')[0]
        port = int(argv.proxy.split(':')[1])
        client = TelegramClient('secret', api_id, api_hash, proxy=(SOCKS5, ip, port))
    else:
        client = TelegramClient('secret', api_id, api_hash)

    if argv.help:
        print(rf'''  ____            ____  _           _
 / ___|  ___  ___|  _ \| |__   ___ | |_ ___
 \___ \ / _ \/ __| |_) | '_ \ / _ \| __/ _ \
  ___) |  __/ (__|  __/| | | | (_) | || (_) |
 |____/ \___|\___|_|   |_| |_|\___/ \__\___/

      a tool for save telegram {Fore.GREEN}self destructing photo/video{Fore.RESET}
      github.com/{Fore.BLUE}Mr3rf1                        {Fore.RESET}t.me/{Fore.BLUE}Mr3rf1{Fore.RESET}

      {Fore.LIGHTMAGENTA_EX}-p{Fore.RESET} or {Fore.LIGHTMAGENTA_EX}--proxy {Fore.LIGHTCYAN_EX}IP:PORT{Fore.RESET} ~> set socks5 proxy (tor)
      example: {Fore.LIGHTMAGENTA_EX}-p {Fore.LIGHTCYAN_EX}127.0.0.1:9050{Fore.RESET}

      This tool automatically monitors all chats for self-destructive media and saves them.
      It also checks replied messages for self-destructive media and saves those too.
      Albums (grouped media) are fully supported and forwarded as a single album.
    ''')
        exit(0)

    print(f' {Fore.YELLOW}[{Fore.GREEN}!{Fore.YELLOW}]{Fore.RESET} Starting to monitor all chats for self-destructive media...')

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
        print(f' {Fore.YELLOW}[{Fore.RED}ERROR{Fore.YELLOW}]{Fore.RESET} Authentication failed. Exiting...')
        await client.disconnect()
        return

    def build_filename(username, chat_id, timestamp, index=None, message_id=None):
        """Build a filename stem as USERNAME(or id)_TIMESTAMP[_msgID][_index]"""
        name = username if username else str(chat_id)
        # Sanitize for filesystem
        name = re.sub(r'[\\/:*?"<>|]', '_', name)
        msg_part = f"_msg{message_id}" if message_id is not None else ""
        stem = f"{name}_{timestamp}{msg_part}"
        if index is not None:
            stem = f"{stem}_{index}"
        return stem

    def build_caption(message, chat_id, username, is_reply=False, is_album=False):
        """Build the formatted caption for a saved media message"""
        prefix = '┏' if not is_reply else '┣'
        album_line = f"┣ᗩᒪᗷᑌᗰ ⤳ ✓{chr(10)}" if is_album else ""
        caption = (
            f"{prefix}ᑕᕼᗩT Iᗪ ⤳ <a href=\"tg://user?id={chat_id}\">{chat_id}</a>\n"
            f"{album_line}"
            f"┣ᑌՏᗴᖇᑎᗩᗰᗴ ⤳ {'@' + username if username else '✗'}\n"
            f"┣ᗰᗴՏՏᗩᘜᗴ Iᗪ ⤳ {message.id}\n"
            f"┣ᗪᗩTᗴ TIᗰᗴ ⤳ {datetime.now(timezone('Asia/Tehran')).strftime('%Y/%m/%d %H:%M:%S')}\n"
            f"┗ github.com/Mr3rf1\n"
        )
        if is_reply:
            caption = f"┏ᖇᗴᑭᒪIᗴᗴᗪ TO ᗰᗴՏՏᗩᘜᗴ\n" + caption
        return caption

    async def process_album(messages, chat_title, chat_id, username, is_reply=False):
        """Download and forward an album (grouped media) as a single album"""
        try:
            file_paths = []
            for msg in messages:
                if not msg.media:
                    continue
                ext = 'jpg' if hasattr(msg.media, 'photo') and msg.media.photo else 'media'
                ts = datetime.now(timezone('Asia/Tehran')).strftime('%Y%m%d_%H%M%S')
                stem = build_filename(username, chat_id, ts, index=len(file_paths))
                path = await client.download_media(msg.media, f'{stem}.{ext}')
                if path:
                    file_paths.append(path)

            if not file_paths:
                return

            caption = build_caption(messages[0], chat_id, username, is_reply=is_reply, is_album=True)
            label = f"{chat_title}{' (replied message)' if is_reply else ''}"
            print(f' {Fore.YELLOW}[{Fore.RED}!{Fore.YELLOW}]{Fore.RESET} Saving album ({len(file_paths)} items) from {label}...', end='')

            file_handles = [open(p, 'rb') for p in file_paths]
            try:
                await client.send_file('me', file_handles, caption=caption, parse_mode='html')
            finally:
                for fh in file_handles:
                    fh.close()

            print(f'\r {Fore.YELLOW}[{Fore.GREEN}!{Fore.YELLOW}]{Fore.RESET} Album ({len(file_paths)} items) from {label} saved to your messages')

            for p in file_paths:
                try:
                    os.remove(p)
                except Exception:
                    pass
        except Exception as e:
            print(f' {Fore.YELLOW}[{Fore.RED}ERROR{Fore.YELLOW}]{Fore.RESET} Failed to process album: {str(e)}')

    async def process_single_media(message, chat_title, chat_id, username, is_reply=False):
        """Process a single self-destructive media message"""
        try:
            caption = build_caption(message, chat_id, username, is_reply=is_reply, is_album=False)
            label = f"{chat_title}{' (replied message)' if is_reply else ''}"

            ts = datetime.now(timezone('Asia/Tehran')).strftime('%Y%m%d_%H%M%S')
            stem = build_filename(username, chat_id, ts, message_id=message.id)

            if hasattr(message.media, 'photo') and message.media.photo:
                print(f' {Fore.YELLOW}[{Fore.RED}!{Fore.YELLOW}]{Fore.RESET} Found self-destructive photo in {label}. Downloading...', end='')
                file_path = await client.download_media(message.media, f'{stem}.jpg')
                media_type = 'photo'
            elif hasattr(message.media, 'document') and message.media.document:
                print(f' {Fore.YELLOW}[{Fore.RED}!{Fore.YELLOW}]{Fore.RESET} Found self-destructive media in {label}. Downloading...', end='')
                file_path = await client.download_media(message.media, f'{stem}.media')
                media_type = 'media'
            else:
                return

            if file_path:
                with open(file_path, 'rb') as file:
                    await client.send_file('me', file, caption=caption, parse_mode='html')
                print(f'\r {Fore.YELLOW}[{Fore.GREEN}!{Fore.YELLOW}]{Fore.RESET} Secret {media_type} from {label} saved to your messages')
                os.remove(file_path)
        except Exception as e:
            print(f' {Fore.YELLOW}[{Fore.RED}ERROR{Fore.YELLOW}]{Fore.RESET} Failed to process self-destructive media: {str(e)}')

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
        try:
            chat = await event.get_chat()
            chat_title = getattr(chat, 'title', getattr(chat, 'first_name', 'Unknown'))
            username = getattr(chat, 'username', None)
        except Exception as e:
            print(f' {Fore.YELLOW}[{Fore.RED}ERROR{Fore.YELLOW}]{Fore.RESET} Could not get chat info: {str(e)}')
            return

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
                print(f' {Fore.YELLOW}[{Fore.RED}ERROR{Fore.YELLOW}]{Fore.RESET} Failed to process replied message: {str(e)}')

    await client.run_until_disconnected()

if '__main__' == __name__:
    try:
        import asyncio
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Bye :)')
