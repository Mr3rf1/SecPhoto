# t.me/Mr3rf1
# t.me/MrSMSBomber
# Nabinam Ski beri manba nazani
def main():
    try:
        from telethon import TelegramClient, events
        from colorama import Fore
        from socks import SOCKS5
        from argparse import ArgumentParser
        from sys import argv as name
    except: print(f' {Fore.YELLOW}[{Fore.RED}!{Fore.YELLOW}]{Fore.RESET} Please install dependencies~> {Fore.LIGHTYELLOW_EX}python3 {Fore.LIGHTMAGENTA_EX}-m{Fore.LIGHTYELLOW_EX} pip install {Fore.LIGHTMAGENTA_EX}-r {Fore.LIGHTCYAN_EX}requierments.txt{Fore.RESET}');exit(0)
    api_id = 1234567
    api_hash = "82bd7b44432f5cd24d165fgc39nh61352"

    parser = ArgumentParser(add_help=False)
    parser.add_argument('-p', '--proxy')
    parser.add_argument('-Sid', '--string-id')
    parser.add_argument('-Nid', '--numeric-id')
    parser.add_argument('-help', '--help', action='store_true')
    argv = parser.parse_args()

    if argv.proxy != None:
        ip = argv.proxy.split(':')[0]
        port = int(argv.proxy.split(':')[1])
        cli = TelegramClient('secret', api_id, api_hash, proxy=(SOCKS5, ip, port))
    else:
        cli = TelegramClient('secret', api_id, api_hash)
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

      {Fore.LIGHTMAGENTA_EX}-Sid{Fore.RESET} or {Fore.LIGHTMAGENTA_EX}--string-id {Fore.LIGHTCYAN_EX}USERNAME{Fore.RESET} ~> set chat of self destructing media
      {Fore.LIGHTMAGENTA_EX}-Nid{Fore.RESET} or {Fore.LIGHTMAGENTA_EX}--numeric-id {Fore.LIGHTCYAN_EX}USER CHAT ID{Fore.RESET} ~> set numeric id
      example: {Fore.LIGHTYELLOW_EX}python3 {name[0]} {Fore.LIGHTMAGENTA_EX}-Sid {Fore.LIGHTCYAN_EX}Mr3rf1{Fore.RESET}
      example2: {Fore.LIGHTYELLOW_EX}python3 {name[0]} {Fore.LIGHTMAGENTA_EX}-Nid {Fore.LIGHTCYAN_EX}12345678{Fore.RESET}
    ''')
        exit(0)
    if argv.string_id == None and argv.numeric_id == None:
        print(f' {Fore.YELLOW}[{Fore.RED}!{Fore.YELLOW}]{Fore.RESET} Please see help~> python3 {name[0]} --help')
        exit(0)
    elif argv.string_id != None and argv.numeric_id == None:
        id = argv.string_id
    elif argv.string_id == None and argv.numeric_id != None:
        id = int(argv.numeric_id)
    elif argv.string_id != None and argv.numeric_id != None:
        print(f' {Fore.YELLOW}[{Fore.RED}!{Fore.YELLOW}]{Fore.RESET} Please see help~> python3 {name[0]} --help')
        exit(0)
    print(f' {Fore.YELLOW}[{Fore.GREEN}!{Fore.YELLOW}]{Fore.RESET} Waiting for reply to a photo...')
    cli.start()
    @cli.on(events.NewMessage(chats=id, func=lambda e: e.reply_to != None))
    async def run(event):
        mes = await cli.get_messages(id, ids=event.reply_to_msg_id)
        # print(mes.media)
        try:
            if mes.media.photo != None:
                print(f' {Fore.YELLOW}[{Fore.RED}!{Fore.YELLOW}]{Fore.RESET} Downloading photo...', end='')
                await cli.download_media(mes.media, 'secret.jpg')
                await cli.send_file('me', open('secret.jpg', 'rb'))
                print(f'\r {Fore.YELLOW}[{Fore.GREEN}!{Fore.YELLOW}]{Fore.RESET} Secret photo sent in your saved messages')
        except AttributeError:
            try:
                if mes.media.document != None:
                    print(f' {Fore.YELLOW}[{Fore.RED}!{Fore.YELLOW}]{Fore.RESET} Downloading video...', end='')
                    await cli.download_media(mes.media, 'secret.mp4')
                    await cli.send_file('me', open('secret.mp4', 'rb'))
                    print(f'\r {Fore.YELLOW}[{Fore.GREEN}!{Fore.YELLOW}]{Fore.RESET} Secret video sent in your saved messages')
            except AttributeError:
                if mes.media.video != None:
                    print(f' {Fore.YELLOW}[{Fore.RED}!{Fore.YELLOW}]{Fore.RESET} Downloading video...', end='')
                    await cli.download_media(mes.media, 'secret.mp4')
                    await cli.send_file('me', open('hock.mp4', 'rb'))
                    print(f'\r {Fore.YELLOW}[{Fore.GREEN}!{Fore.YELLOW}]{Fore.RESET} Secret video sent in your saved messages')
    cli.run_until_disconnected()
if '__main__' == __name__:
    try: main()
    except KeyboardInterrupt: print('Bye :)')
