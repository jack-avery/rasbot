import click
import config
import irc.bot
import logging
import requests
import sys
import time
import traceback

import commands
import update
from authentication import Authentication
from definitions import NO_MESSAGE_SIGNAL,\
    CommandIsModOnlyError,\
    CommandStillOnCooldownError,\
    AuthenticationDeniedError

# TODO refactor this and on_pubmsg, probably. or at least make it look better


class TwitchBot(irc.bot.SingleServerIRCBot):
    def __init__(self, auth: Authentication, channel_id: int, channel: str, cfgpath: str = '', debug: bool = False):
        """Create a new instance of a Twitch bot.

        :param auth: The Authentication object to use.

        :param channel_id: The channel ID.

        :param channel: The channel name.

        :param cfginfo: The bot config file to read configuration from.

        :param debug: Whether the bot should be verbose about actions.
        """
        # Set up logging
        debug_init_time = time.perf_counter()
        if debug:
            logmode = logging.DEBUG
        else:
            logmode = logging.INFO

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logmode)

        stdout_formatter = logging.Formatter(
            "%(asctime)s %(levelname)s | %(message)s")
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(logmode)
        stdout_handler.setFormatter(stdout_formatter)
        self.logger.addHandler(stdout_handler)

        # Initialize authentication
        self.auth = auth
        self.channel_id = channel_id
        self.channel_name = channel

        self.logger.info(f"Starting as {self.auth.get('user_id')}...")

        # Import channel info
        self.cfgpath = cfgpath
        self.logger.info(f"Reading config from {self.cfgpath}...")

        cfg = config.read_channel(self.cfgpath)

        self.prefix = cfg['meta']['prefix']
        self.logger.info(f"Prefix set as '{self.prefix}'")

        # Set channel name
        self.channel = f"#{channel}"

        # Instantiate commands module
        self.commands = commands
        self.commands.pass_bot_ref(self)

        # Import commands from config
        for name, command in cfg["commands"].items():
            self.commands.command_modify(
                name, command['cooldown'], command['response'], command['requires_mod'], command['hidden'])

        self.logger.info(f"Imported {len(cfg['commands'])} command(s)")

        # Import additional modules
        if cfg["modules"]:
            for module in cfg["modules"]:
                self.commands.module_add(module)

            self.logger.info(f"Imported {len(cfg['modules'])} module(s)")

        if debug:
            self.logger.debug(
                f"init stats: {len(self.commands.modules)} modules, "
                + f"{len(self.commands.commands)} commands, "
                + f"{round(time.perf_counter()-debug_init_time,2)}s to init")

        # Create IRC bot connection
        server = 'irc.twitch.tv'
        port = 80
        self.logger.info('Connecting to ' + server +
                         ' on port ' + str(port) + '...')
        irc.bot.SingleServerIRCBot.__init__(self, [(
            server, port, f"oauth:{self.auth.get('irc_oauth')}")], self.auth.get('user_id'), self.auth.get('user_id'))

    def unimport_all_modules(self):
        """Teardown all modules in preparation for closing.
        """
        modules = [k for k in self.commands.modules.keys()]
        for module in modules:
            self.commands.module_del(module)

    def on_welcome(self, c, e):
        # You must request specific capabilities before you can use them
        c.cap('REQ', ':twitch.tv/membership')
        c.cap('REQ', ':twitch.tv/tags')
        c.cap('REQ', ':twitch.tv/commands')
        c.join(f"{self.channel}")

        self.logger.info(f'Joined {self.channel}! ({self.channel_id})\n')

    def on_pubmsg(self, c, e):
        """Code to be run when a message is sent.
        """
        # Recomprehend tags into something usable
        e.tags = {i["key"]: i["value"] for i in e.tags}

        # Grab display name, userid and mod status
        name = str.lower(e.tags["display-name"])
        uid = int(e.tags['user-id'])
        ismod = int(e.tags['mod'])

        # Giving broadcaster moderator priveleges
        if uid == self.channel_id:
            ismod = True
        else:  # Else just set it to a bool
            ismod = bool(ismod)

        # For use within modules
        self.author_name = name
        self.author_uid = uid
        self.author_ismod = ismod

        # Reading the message
        self.msg = e.arguments[0]
        self.msg_split = self.msg.split(' ')

        try:
            # Do per-message methods
            self.commands.do_on_pubmsg_methods()

            # Don't continue if the message doesn't start with the prefix.
            if not self.msg.startswith(self.prefix):
                return

            # Isolating command and command arguments
            cmd = self.msg_split[0][len(self.prefix):].lower()
            self.cmdargs = self.msg_split[1:]

            # Verify that it's actually a command before continuing.
            if cmd not in self.commands.commands:
                self.logger.debug(
                    f"Ignoring invalid command call '{cmd}' from {name} (mod: {ismod})")
                return

            try:
                # Run the command and string result message
                self.logger.info(
                    f"Running command call '{cmd}' from {name} (mod: {ismod}) (args:{self.cmdargs})")
                cmdresult = self.commands.commands[cmd].run(self)

                # If there is a string result message, print it to chat
                if cmdresult and not NO_MESSAGE_SIGNAL in cmdresult:
                    self.send_message(f"{cmdresult}")

            # If the command is still on cooldown, do nothing.
            # If the command is mod-only and a non-mod calls it, do nothing.
            except (CommandStillOnCooldownError, CommandIsModOnlyError) as err:
                self.logger.debug(f"{err}")

        except Exception as err:
            self.send_message(f'An error occurred in the processing of your request: {str(err)}. '
                              + 'A full stack trace has been output to the command window.')
            traceback.print_exc()

    def send_message(self, message: str):
        """Sends a message to the public chat. For easy use within modules.

        :param message: The message to send.
        """
        self.connection.privmsg(self.channel, f'{message}')

    def log_error(self, src: str, msg: str):
        """Log an error. For easy use within modules.

        :param src: The file/module this is coming from.

        :param msg: The error to log.
        """
        self.logger.error(f'{src} - {msg}')

    def log_info(self, src: str, msg: str):
        """Log an info-level string. For easy use within modules.

        :param src: The file/module this is coming from.

        :param message: The message to log.
        """
        self.logger.info(f'{src} - {msg}')

    def log_debug(self, src: str, msg: str):
        """Log debug information. For easy use within modules.

        :param src: The file/module this is coming from.

        :param message: The debug info to log.
        """
        self.logger.debug(f'{src} - {msg}')

    def write_config(self):
        """Write this bots' config file. For easy use within modules.
        """
        config.write_channel(self)


@click.command()
@click.option(
    "--channel",
    help="The twitch channel to target."
)
@click.option(
    "--auth",
    help="The path to the auth file."
)
@click.option(
    "--cfg",
    help="The path to the channel config file."
)
@click.option(
    "--debug/--normal",
    help="Have this instance be verbose about actions.",
    default=False
)
def main(channel=None, auth=None, cfg=None, debug=False):
    # Check for updates first!
    update.check(True)

    cfg_global = config.read_global()

    if cfg_global['always_debug']:
        debug = True

    if not auth:
        auth = cfg_global['default_authfile']

    auth = Authentication(auth)

    if not channel:
        channel = auth.get('user_id')

    # Resolve ID from channel name
    channel_id = False
    url = f"https://api.twitch.tv/helix/users?login={channel}"
    while not channel_id:
        r = requests.get(url, headers=auth.get_headers()).json()
        try:
            channel_id = int(f"{r['data'][0]['id']}")
        except KeyError:
            # If it errors with a 401 we try to refresh the oauth key
            if r['status'] == 401:
                print("OAuth key is invalid or expired. Attempting a refresh...")
                try:
                    auth.refresh_oauth()
                except AuthenticationDeniedError as err:
                    # If THAT fails, we throw our hands in the air and tell them to restart.
                    print(f"Authentication Denied: {err}")
                    print("Please ensure that your credentials are valid.")
                    print("You may need to re-run setup.py.\n")
                    input("This error is unrecoverable. rasbot will now exit.")
                    exit(1)

    if not cfg:
        cfg = f"config/{channel_id}.txt"

    # Start the bot
    try:
        tb = TwitchBot(auth, channel_id, channel, cfg, debug)
        tb.start()
    except KeyboardInterrupt:
        tb.unimport_all_modules()
        sys.exit(0)


if __name__ == "__main__":
    main()
