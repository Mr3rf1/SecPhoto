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
        from jdatetime import datetime
        from pytz import timezone
    except ImportError:
        print(' [!] Please install dependencies~> python3 -m pip install -r requirements.txt')
        exit(0)

    def get_phone_number():
        """Get phone number with validation for international format"""
        while True:
            phone = input(f" {Fore.YELLOW}[{Fore.GREEN}<{Fore.YELLOW}]{Fore.RESET} Enter your phone number (with country code, e.g., +1234567890): ").strip()
            
            # Basic validation for international phone number format
            if re.match(r'^\+[1-9]\d{1,14}$', phone):
                return phone
            else:
                print(f" {Fore.YELLOW}[{Fore.RED}!{Fore.YELLOW}]{Fore.RESET} Invalid phone number format. Please use international format (e.g., +1234567890)")

    async def authenticate_user(client):
        """Authenticate user with proper checking and interactive input"""
        try:
            # First check if user is already authenticated
            me = await client.get_me()
            if me:
                print(f" {Fore.YELLOW}[{Fore.GREEN}!{Fore.YELLOW}]{Fore.RESET} Already authenticated as: {me.first_name}")
                return True
        except Exception:
            # User is not authenticated, proceed with authentication
            pass
        
        print(f" {Fore.YELLOW}[{Fore.CYAN}!{Fore.YELLOW}]{Fore.RESET} Authentication required...")
        
        # Get phone number interactively
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

<<<<<<< HEAD
      This tool automatically monitors all chats for self-destructive media and saves them.
    ''')
        exit(0)

    print(f' {Fore.YELLOW}[{Fore.GREEN}!{Fore.YELLOW}]{Fore.RESET} Starting to monitor all chats for self-destructive media...')
    
    # Connect to Telegram first
    await client.connect()
    
    # Authenticate user
    if not await authenticate_user(client):
        print(f' {Fore.YELLOW}[{Fore.RED}ERROR{Fore.YELLOW}]{Fore.RESET} Authentication failed. Exiting...')
        await client.disconnect()
        return

    @client.on(events.NewMessage)
    async def handler(event):
        # Check if the message has self-destructive media
        if event.message.media and hasattr(event.message.media, 'ttl_seconds') and event.message.media.ttl_seconds:
            try:
                chat = await event.get_chat()
                chat_title = getattr(chat, 'title', getattr(chat, 'first_name', 'Unknown'))
                
                # Get username if available
                username = getattr(chat, 'username', None)
                
                # Create detailed caption
                caption = f"""
┏ᑕᕼᗩT Iᗪ ⤳ <a href="tg://user?id={event.chat_id}">{event.chat_id}</a>
┣ᑌՏᗴᖇᑎᗩᗰᗴ ⤳ {'@' + username if username else '✗'}
┣ᗰᗴՏՏᗩᘜᗴ Iᗪ ⤳ {event.message.id}
┣ᗪᗩTᗴ TIᗰᗴ ⤳ {datetime.now(timezone('Asia/Tehran')).strftime("%Y/%m/%d %H:%M:%S")}
┗ github.com/Mr3rf1
"""
                # Handle photos
                if hasattr(event.message.media, 'photo') and event.message.media.photo:
                    print(f' {Fore.YELLOW}[{Fore.RED}!{Fore.YELLOW}]{Fore.RESET} Found self-destructive photo in {chat_title}. Downloading...', end='')
                    file_path = await client.download_media(event.message.media, 'secret_photo.jpg')
                    if file_path:
                        with open(file_path, 'rb') as file:
                            await client.send_file('me', file, caption=caption, parse_mode='html')
                        print(f'\r {Fore.YELLOW}[{Fore.GREEN}!{Fore.YELLOW}]{Fore.RESET} Secret photo from {chat_title} saved to your messages')
                        # Clean up temporary file
                        os.remove(file_path)

                # Handle videos and other documents
                elif hasattr(event.message.media, 'document') and event.message.media.document:
                    print(f' {Fore.YELLOW}[{Fore.RED}!{Fore.YELLOW}]{Fore.RESET} Found self-destructive media in {chat_title}. Downloading...', end='')
                    file_path = await client.download_media(event.message.media, 'secret_media')
                    if file_path:
                        with open(file_path, 'rb') as file:
                            await client.send_file('me', file, caption=caption, parse_mode='html')
                        print(f'\r {Fore.YELLOW}[{Fore.GREEN}!{Fore.YELLOW}]{Fore.RESET} Secret media from {chat_title} saved to your messages')
                        # Clean up temporary file
                        os.remove(file_path)

            except Exception as e:
                print(f' {Fore.YELLOW}[{Fore.RED}ERROR{Fore.YELLOW}]{Fore.RESET} Failed to process self-destructive media: {str(e)}')

    await client.run_until_disconnected()

if '__main__' == __name__:
    try:
        import asyncio
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Bye :)')
