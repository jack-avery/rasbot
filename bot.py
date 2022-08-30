import click
import config
import irc.bot
import logging
import requests
import sys
import traceback

import commands
import update
from authentication import Authentication
from definitions import CommandIsModOnlyError,\
    CommandStillOnCooldownError,\
    AuthenticationDeniedError


class TwitchBot(irc.bot.SingleServerIRCBot):
    def __init__(self, auth, channel_id: int, channel: str = None, cfgid: int = None, debug: bool = False):
        """Create a new instance of a Twitch bot.

        :param auth: The Authentication object to use.

        :param channel_id: The channel ID.

        :param channel: The channel name.

        :param cfginfo: The bot config file to read configuration from.

        :param debug: Whether the bot should be verbose about actions.
        """
        # Set up logging
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

        self.auth = auth
        self.authkeys = self.auth.get_auth()
        self.channel_id = channel_id

        self.logger.info(f"Starting as {self.authkeys['user_id']}...")

        # Import channel info
        if cfgid is None:
            self.cfgid = f"_{self.channel_id}.txt"
        else:
            self.cfgid = cfgid

        self.logger.info(f"Reading config from {self.cfgid}...")

        cfg = config.read(self.cfgid)
        self.prefix = cfg["prefix"]

        self.logger.info(f"Prefix set as '{self.prefix}'")

        # Instantiate commands module
        self.commands = commands
        self.commands.setup(self)

        # Import commands
        for command in cfg["commands"]:
            # Evaluate modonly/hidden flags
            for i in range(2):
                if command[i+2] == "False":
                    command[i+2] = False
                elif command[i+2] == "True":
                    command[i+2] = True
                else:
                    self.logger.error(
                        f"Command {command[0]} might have imported incorrectly: invalid flag?")

            self.commands.command_modify(command[0], command[1], " ".join(
                command[4:]), command[2], command[3])

        self.logger.info(f"Imported {len(cfg['commands'])} custom command(s)")

        # Resolve channel name
        if channel is None:
            self.channel = self.authkeys['user_id']
        else:
            self.channel = f"#{channel}"

        # Create IRC bot connection
        server = 'irc.twitch.tv'
        port = 80
        self.logger.info('Connecting to ' + server +
                         ' on port ' + str(port) + '...')
        irc.bot.SingleServerIRCBot.__init__(self, [(
            server, port, f"oauth:{self.authkeys['irc_oauth']}")], self.authkeys['user_id'], self.authkeys['user_id'])

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
        # Resolving username and mod status
        for i in e.tags:
            if i['key'] == "display-name":
                name = str.lower(i['value'])

            if i['key'] == "mod":
                ismod = i['value']

        # Setting mod status to a bool and giving broadcaster moderator priveleges
        if ismod == '1' or name.lower() == self.channel.lower()[1:]:
            ismod = True
        else:
            ismod = False

        self.caller_name = name
        self.caller_ismod = ismod

        # Reading the message
        self.msg = str(e.arguments)
        self.msg_split = self.msg[2:-2].split(' ')

        try:
            # Do per-message methods
            self.commands.do_on_pubmsg_methods(self)

            # If the message starts with the command prefix...
            if self.msg_split[0][:len(self.prefix)].lower() == self.prefix:
                # Isolating command and command arguments
                # Verify that it's actually a command before continuing.
                cmd = self.msg_split[0][len(self.prefix):].lower()
                if cmd not in self.commands.commands:
                    self.logger.debug(
                        f"Ignoring invalid command call '{cmd}' from {self.caller_name} (mod:{self.caller_ismod})")
                    return

                # Isolate command arguments from command
                self.cmdargs = self.msg_split[1:]

                try:
                    # Run the command and string result message
                    self.logger.info(
                        f"Running command call '{cmd}' from {self.caller_name} (mod:{self.caller_ismod}) (args:{self.cmdargs})")
                    cmdresult = self.commands.commands[cmd].run(self)

                    # If there is a string result message, print it to chat
                    if cmdresult and cmdresult != "None":
                        self.send_message(f"{cmdresult}")

                # If the command is still on cooldown, do nothing.
                # If the command is mod-only and a non-mod calls it, do nothing.
                except (CommandStillOnCooldownError, CommandIsModOnlyError) as err:
                    self.logger.info(f"{err}")

        except Exception as err:
            self.send_message(f'An error occurred in the processing of your request: {str(err)}. '
                              + 'A full stack trace has been output to the command window.')
            traceback.print_exc()

    def send_message(self, message: str):
        """Sends a message. For easy use within modules.

        :param message: The message to send.
        """
        self.connection.privmsg(self.channel, f'{message}')

    def log_error(self, message: str):
        """Log an error. For easy use within modules.

        :param message: The error to log.
        """
        self.logger.error(f'{message}')

    def log_info(self, message: str):
        """Log an info-level string. For easy use within modules.

        :param message: The message to log.
        """
        self.logger.info(f'{message}')

    def log_debug(self, message: str):
        """Log debug information. For easy use within modules.

        :param message: The debug info to log.
        """
        self.logger.debug(f'{message}')


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
def run(channel=None, auth=None, cfg=None, debug=False):
    # Check for updates first!
    update.check(True)

    auth = Authentication(auth)

    if channel is None:
        channel = auth.get_auth()['user_id']

    # Resolve ID from channel name
    channel_id = False
    while not channel_id:
        url = f"https://api.twitch.tv/helix/users?login={channel}"
        r = requests.get(url, headers=auth.get_headers()).json()
        try:
            channel_id = int(f"{r['data'][0]['id']}")
        except KeyError:
            if r['status'] == 401:
                print("OAuth key is invalid or expired. Attempting a refresh...")
                try:
                    auth.auth['oauth'] = auth.request_oauth()
                    auth.write_authfile()
                except AuthenticationDeniedError as err:
                    print(f"Authentication Denied: {err}")
                    print("Please ensure that your credentials are valid.")
                    print("You may need to re-run setup.py.\n")
                    input("This error is unrecoverable. rasbot will now exit.")
                    exit(1)

    # Start the bot
    tb = TwitchBot(auth, channel_id, channel, cfg, debug)
    tb.start()


if __name__ == "__main__":
    run()
