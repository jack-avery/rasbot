import irc.bot
import logging
import traceback

import src.commands as commands
from src.config import write, read_channel
from src.authentication import TwitchOAuth2Helper
from src.definitions import Author, Message

log = logging.getLogger("rasbot")


class TwitchBot(irc.bot.SingleServerIRCBot):
    auth: TwitchOAuth2Helper
    channel_id: int
    channel_name: str
    channel: str
    commands: commands
    cfgpath: str
    """Path to the currently used channel config file."""
    prefix: str
    always_import_list: list
    """List of modules to always import, regardless of whether they're used in commands."""

    def __init__(self, auth: TwitchOAuth2Helper, channel_name: str):
        """Create a new `TwitchBot`.

        :param auth: The Authentication object to use.
        :param channel_name: The channel name. Channel ID is resolved in `__init__`.
        """
        # Grab channels
        self.channel_name = channel_name
        self.channel = f"#{channel_name}"

        # Initialize authentication
        self.auth = auth
        log.info(f"Starting as {self.auth.user_id}...")

        # Import channel info
        self.channel_id = self.auth.get_user_id(channel_name)

        self.user_id = self.channel_id
        if channel_name != self.auth.user_id:
            self.user_id = self.auth.get_user_id(self.auth.user_id)

        self.cfgpath = f"{self.channel_id}/config.txt"
        self.reload()

        # Create IRC bot connection
        server = "irc.twitch.tv"
        port = 80
        log.info("Connecting to " + server + " on port " + str(port) + "...")
        irc.bot.SingleServerIRCBot.__init__(
            self,
            [(server, port, f"oauth:{self.auth.irc_oauth}")],
            self.auth.user_id,
            self.auth.user_id,
        )

    def reload(self):
        """Reload the config for the current channel."""
        log.info(f"Reading config from {self.cfgpath}...")
        cfg = read_channel(self.cfgpath)

        self.prefix = cfg["meta"]["prefix"]
        log.info(f"Prefix set as '{self.prefix}'")

        # Instantiate commands module
        self.commands = commands
        self.commands.pass_bot_ref(self)

        # Import commands from config
        for name, command in cfg["commands"].items():
            try:
                self.commands.command_add(
                    name,
                    command["cooldown"],
                    command["response"],
                    command["requires_mod"],
                    command["hidden"],
                )
            except ModuleNotFoundError as mod:
                log.error(
                    f"command '{name}' attempts to use non-existent module '{mod}': ignoring..."
                )

        log.info(f"Imported {len(cfg['commands'])} command(s)")

        # Import additional modules
        self.always_import_list = cfg["modules"]
        if cfg["modules"]:
            for module in cfg["modules"]:
                if module in self.commands.modules:
                    continue

                try:
                    self.commands.module_add(module)
                except ModuleNotFoundError as mod:
                    log.error(
                        f"always_import_list ('modules' in config) contains non-existent module '{mod}'"
                    )

            log.info(f"Imported {len(cfg['modules'])} additional module(s)")

    def save(self):
        """Write this bots' config file. For easy use within modules."""
        # Construct skeleton
        data = {
            "meta": {"prefix": self.prefix},
            "commands": {},
            "modules": self.always_import_list,
        }

        # Adding commands
        for name, command in self.commands.commands.items():
            data["commands"][name] = {
                "cooldown": command.cooldown,
                "requires_mod": command.requires_mod,
                "hidden": command.hidden,
                "response": command.response,
            }

        write(self.cfgpath, data)

    def unimport_all_modules(self):
        """Teardown all modules in preparation for closing."""
        modules = [k for k in self.commands.modules.keys()]
        for module in modules:
            self.commands.module_del(module)

    def on_welcome(self, c, e):
        # You must request specific capabilities before you can use them
        c.cap("REQ", ":twitch.tv/membership")
        c.cap("REQ", ":twitch.tv/tags")
        c.cap("REQ", ":twitch.tv/commands")
        c.join(f"{self.channel}")

        log.info(f"Joined {self.channel}! ({self.channel_id})\n")

    def on_pubmsg(self, c, e):
        """Code to be run when a message is sent."""
        # Recomprehend tags into something usable
        e.tags = {i["key"]: i["value"] for i in e.tags}

        # Grab user info
        name = str.lower(e.tags["display-name"])
        uid = int(e.tags["user-id"])
        ismod = dict.get(e.tags, "mod", "0") == "1"
        issub = dict.get(e.tags, "subscriber", "0") == "1"
        isvip = dict.get(e.tags, "vip", "0") == "1"
        ishost = False

        # Gauranteeing broadcaster all traits
        if uid == self.channel_id:
            ismod = True
            issub = True
            isvip = True
            ishost = True

        # Create author object
        author = Author(name, uid, ismod, issub, isvip, ishost)

        # Create message object
        msg = e.arguments[0]
        message = Message(author, msg)

        try:
            # Don't continue if the message doesn't start with the prefix.
            if not msg.startswith(self.prefix):
                self.commands.do_on_pubmsg(message)
                return

            split = msg.split(" ")

            # Isolating command and command arguments
            cmd = split[0][len(self.prefix) :].lower()
            args = split[1:]
            message.attach_command(cmd, args)

            self.commands.do_on_pubmsg(message)

            # Verify that it's actually a command before continuing.
            if cmd not in self.commands.commands:
                log.debug(
                    f"Ignoring invalid command call '{cmd}' from {name} ({author.user_status()})"
                )
                return

            # Run the command and string result message
            log.info(
                f"Running command call '{cmd}' from {name} ({author.user_status()}) (args:{message.args})"
            )
            cmdresult = self.commands.commands[cmd].run(message)

            # If there is a string result message, print it to chat
            if cmdresult:
                self.send_message(f"{cmdresult}")

        except Exception as err:
            self.send_message(
                f"An error occurred in the processing of your request: {str(err)}. "
                + "A full stack trace has been output to the command window."
            )
            traceback.print_exc()

    def send_message(self, msg: str):
        """Sends a message to the public chat. For easy use within modules.

        :param msg: The message to send.
        """
        self.connection.privmsg(self.channel, f"{msg}")