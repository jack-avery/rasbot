import irc.bot
import logging
from threading import Timer
import traceback

from src.commands import CommandsHandler
from src.plugins import ModulesHandler
from src.config import ConfigHandler, DEFAULT_CHANNEL
from src.authentication import TwitchOAuth2Helper
from src.definitions import Author, Message, status_from_user_privilege
from src.telemetry import report_exception


class TwitchBot(irc.bot.SingleServerIRCBot):
    auth: TwitchOAuth2Helper
    channel_id: int
    channel_name: str
    channel: str
    commands_handler: CommandsHandler
    modules_handler: ModulesHandler
    cfgpath: str
    """Path to the currently used channel config file."""
    prefix: str
    always_import_list: list
    """List of modules to always import, regardless of whether they're used in commands."""

    CONNECTION_ATTEMPT_LIMIT = 3
    """Maximum number of connection attempts before giving up."""
    CONNECTION_ATTEMPT_TIMER = 5
    """Time between connection attempts, in seconds."""

    def __init__(
        self, auth: TwitchOAuth2Helper, channel_name: str, channel_id: int = None
    ):
        """Create a new `TwitchBot`.

        :param auth: The Authentication object to use.
        :param channel_name: The channel name. Channel ID is resolved in `__init__`.
        """
        self.__joined = False
        self.__connection_tries = 0

        # Grab channels
        self.channel_name = channel_name
        self.channel = f"#{channel_name}"

        # Initialize authentication
        self.auth = auth
        logging.info(f"Starting as {self.auth.user_id}...")

        # Import channel info
        self.channel_id = channel_id
        if not channel_id:
            self.channel_id = self.auth.get_user_id(channel_name)

        self.user_id = self.channel_id
        if channel_name != self.auth.user_id:
            self.user_id = self.auth.get_user_id(self.auth.user_id)

        self.cfg_handler = ConfigHandler(
            f"{self.channel_id}/config.txt", DEFAULT_CHANNEL
        )
        self.reload()

        self.attempt_connect()

    def attempt_connect(self):
        """Connect to the chat.

        Wait `CONNECTION_ATTEMPT_TIMER` seconds between attempts, to a maximum of `CONNECTION_ATTEMPT_LIMIT`.
        """
        if self.__connection_tries > self.CONNECTION_ATTEMPT_LIMIT:
            logging.error(
                f"Connection attempts exceeded limit of {self.CONNECTION_ATTEMPT_LIMIT}. Exiting..."
            )
            self.__del__()

        if not self.__joined:
            # Create IRC bot connection
            server = "irc.twitch.tv"
            port = 80
            logging.info("Connecting to " + server + " on port " + str(port) + "...")
            irc.bot.SingleServerIRCBot.__init__(
                self,
                [(server, port, f"oauth:{self.auth.irc_oauth}")],
                self.auth.user_id,
                self.auth.user_id,
            )

            self.__connection_tries += 1
            Timer(self.CONNECTION_ATTEMPT_TIMER, function=self.attempt_connect).start()

    def reload(self):
        """Reload the config for the current channel."""
        logging.info(f"Reading config from {self.cfg_handler._path}...")
        cfg = self.cfg_handler.read()

        self.prefix = cfg["meta"]["prefix"]
        logging.info(f"Prefix set as '{self.prefix}'")

        # Instantiate handler modules
        self.commands_handler = CommandsHandler(self)
        self.modules_handler = ModulesHandler(self)

        # Import commands from config
        for name, command in cfg["commands"].items():
            try:
                self.commands_handler.add(
                    name,
                    command=command,
                )
            except ModuleNotFoundError as mod:
                logging.error(
                    f"command '{name}' attempts to use non-existent module '{mod}': ignoring..."
                )

        logging.info(f"Imported {len(cfg['commands'])} command(s)")

        # Import additional modules
        self.always_import_list = cfg["modules"]
        if cfg["modules"]:
            for module in cfg["modules"]:
                if module in self.modules_handler.modules:
                    continue

                try:
                    self.modules_handler.add(module)
                except ModuleNotFoundError as mod:
                    logging.error(
                        f"always_import_list ('modules' in config) contains non-existent module '{mod}'"
                    )

            logging.info(f"Imported {len(cfg['modules'])} additional module(s)")

    def save(self):
        """Write this bots' config file. For easy use within modules."""
        # Construct skeleton
        data = {
            "meta": {"prefix": self.prefix},
            "commands": {},
            "modules": self.always_import_list,
        }

        # Adding commands
        for name, command in self.commands_handler.commands.items():
            data["commands"][name] = command.jsonify()

        self.cfg_handler.write(data)

    def __del__(self):
        """Teardown all modules in preparation for closing."""
        modules = [k for k in self.modules_handler.modules.keys()]
        for module in modules:
            self.modules_handler.delete(module)

        del self

    def on_welcome(self, c, e):
        # You must request specific capabilities before you can use them
        c.cap("REQ", ":twitch.tv/membership")
        c.cap("REQ", ":twitch.tv/tags")
        c.cap("REQ", ":twitch.tv/commands")
        c.join(f"{self.channel}")

        self.__joined = True
        logging.info(f"Joined {self.channel}! ({self.channel_id})\n")

    def on_pubmsg(self, c, e):
        """Code to be run when a message is sent."""
        # Recomprehend tags into something usable
        e.tags: dict = {i["key"]: i["value"] for i in e.tags}

        # Grab user info
        name = str(e.source)
        name = str.lower(name[: name.find("!")])
        display_name = str.lower(e.tags["display-name"])
        uid = int(e.tags["user-id"])
        ismod = e.tags.get("mod", "0") == "1"
        issub = e.tags.get("subscriber", "0") == "1"
        isvip = e.tags.get("vip", "0") == "1"
        ishost = False

        # Gauranteeing broadcaster all traits
        if uid == self.channel_id:
            ishost = True

        # Create author object
        author = Author(name, display_name, uid, ismod, issub, isvip, ishost)

        # Create message object
        msg: str = e.arguments[0].replace(" \U000e0000", "")
        message = Message(author, msg, e)

        try:
            # Don't continue if the message doesn't start with the prefix.
            if not msg.startswith(self.prefix):
                self.modules_handler.do_on_pubmsg(message)
                return

            split = msg.split(" ")

            # Isolating command and command arguments
            cmd = split[0][len(self.prefix) :].lower()
            args = split[1:]
            message.attach_command(cmd, args)

            self.modules_handler.do_on_pubmsg(message)

            # Verify that it's actually a command before continuing.
            if cmd not in self.commands_handler.commands:
                logging.debug(
                    f"Ignoring invalid command call '{cmd}' from {name} ({status_from_user_privilege(author.priv)})"
                )
                return

            # Run the command and string result message
            logging.info(
                f"Running command call '{cmd}' from {name} ({status_from_user_privilege(author.priv)}) (args:{message.args})"
            )
            cmdresult = self.commands_handler.run(cmd, message)

            # If there is a string result message, print it to chat
            if cmdresult:
                self.send_message(f"{cmdresult}")

        except Exception as err:
            self.send_message(
                f"An error occurred in the processing of your request: {str(err)}. "
                + "A full stack trace has been output to the command window."
            )
            traceback.print_exc()
            # report the error to the webhook as well for debugging
            report_exception(traceback.format_exc())

    def send_message(self, msg: str):
        """Sends a message to the public chat. For easy use within modules.

        :param msg: The message to send.
        """
        self.connection.privmsg(self.channel, f"{msg}")
