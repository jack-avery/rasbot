import importlib.util
import logging
import re
import threading
import time
import traceback

from src.config import read, write
from src.definitions import Message

log = logging.getLogger("rasbot")

MODULE_MENTION_RE = re.compile(r"(%([\/a-z0-9_]+)%)")
"""Regex to search command responses with to apply modules."""

NO_MESSAGE_SIGNAL = "%NOMSG%"
"""Signal for a module to return for there to be no message sent no matter what."""


class Command:
    name: str
    cooldown: int
    response: str
    requires_mod: bool
    hidden: bool
    """Whether this command is hidden from the `help` module."""

    def __init__(
        self,
        name: str,
        cooldown: int = 5,
        response: str = "",
        requires_mod: bool = False,
        hidden: bool = False,
    ):
        """Create a new `Command`.

        :param name: The name of the command.
        :param cooldown: The cooldown of the command in seconds.
        :param response: The text response of the command. Encapsulate custom commands in %, e.g. `%module%`.
        :param requires_mod: Whether the command requires the user to be a mod.
        :param hidden: Whether the command should be hidden from the `help` module.
        """
        self.name = name.lower()
        self.cooldown = cooldown
        self.response = response
        self.requires_mod = requires_mod
        self.hidden = hidden

        self._last_used = 0

    def run(self, message: Message):
        """Code to be run when this command is called from chat.

        Runs all %% codes found in the command and returns the result.
        """
        if not time.time() - self._last_used > self.cooldown:
            return False

        if not message.author.is_mod and self.requires_mod:
            return False

        # Apply the main function for any modules found
        returned_response = self.response
        for mention, module in MODULE_MENTION_RE.findall(returned_response):
            returned_response = returned_response.replace(
                mention, str(modules[module].main(message))
            )

        if NO_MESSAGE_SIGNAL in returned_response:
            return False

        self._last_used = time.time()
        return returned_response

    def get_used_modules(self) -> list:
        """Get the list of modules that are mentioned in `self.response`.

        :return: The list of modules used.
        """
        return [m[1] for m in MODULE_MENTION_RE.findall(self.response)]


def command_add(
    name: str,
    cooldown: int = 5,
    response: str = "",
    requires_mod: bool = False,
    hidden: bool = False,
):
    """Create a new command (or modifies an existing one).
    Automatically attempts to import any unimported modules.

    :param name: The name of the command.
    :param cooldown: The cooldown of the command in seconds.
    :param response: The text response of the command. Encapsulate custom commands in %%.
    :param requires_mod: Whether this command requires moderator access to use.
    :param hidden: Whether to hide this command from the `help` module.
    """
    log.debug(
        f"adding {name} (cd:{cooldown}s mo:{requires_mod} h:{hidden} res:{response})"
    )

    # Resolve any modules the command mentions and import new ones
    for _, module in MODULE_MENTION_RE.findall(response):
        if module not in modules:
            try:
                module_add(module)
            except ModuleNotFoundError as err:
                raise err

    commands[name] = Command(name, cooldown, response, requires_mod, hidden)


def command_mod(name: str, key: str, value):
    """Modify `key` for `name`.

    :param name: The name of the command.
    :param key: The field of the command to modify.
    :param value: The value to set the field to.
    """
    log.debug(f"modifying {key} of {name} to {value}")
    if key == "cooldown":
        commands[name].cooldown = value

    elif key == "response":
        commands[name].response = value

    elif key == "requires_mod":
        commands[name].requires_mod = value

    elif key == "hidden":
        commands[name].hidden = value

    else:
        raise ValueError(f"{key} is not a valid field to modify")


def command_del(name: str):
    """Delete a command if it exists.

    :param name: The name of the command.
    """
    log.debug(f"removing {name}")
    del commands[name]


class BaseModule(threading.Thread):
    """The base class for a Module.

    Facilitates defaults for a Module so as to prevent errors.
    """

    helpmsg = "No help message available for module."
    """Help message to display when used with the `help` module."""

    default_config = False
    """Default configuration to save to-file."""

    consumes = 0
    """How many message arguments to consume. Any negative value for all remaining."""

    def __init__(self, bot, name):
        """Initialize a module. If a `cfgdefault` is given,
        it will drop the given default into the user's config directory.
        """
        threading.Thread.__init__(self)
        self._bot = bot
        self._name = name

        self._cfg_path = f"{self._bot.channel_id}/modules/{name}.txt"

        self.reload_config()

    def __del__(self):
        """Destroy this module. Does nothing by default.

        Used in `xp` to teardown the thread for faster closing through Ctrl+C.
        """
        pass

    def reload_config(self):
        """Completely reload this module's config from file."""
        self._cfg = read(self._cfg_path, self.default_config)

    def save_config(self):
        """Save the current form of this module's `self.cfg` attribute to file."""
        write(self._cfg_path, self._cfg)

    def cfg_get(self, key: str):
        """Read the given config dict key. If it fails to read it will fill it in with the default.

        :param key: The key to grab the value of

        :return: The value of `self._cfg[key]`
        """
        if key not in self._cfg:
            if key not in self.default_config:
                self.log_e(f"attempt to grab invalid key {key}? ignoring")
                return False

            self.log_w(
                f"config missing searched key '{key}', saving default '{self.default_config[key]}'"
            )

            self.cfg_set(key, self.default_config[key])

        return self._cfg[key]

    def cfg_set(self, key: str, value):
        """Set the value of a given config dict key, and save the config.

        :param key: The key to set
        :param value: The value to set `key` to
        """
        self._cfg[key] = value
        self.save_config()

    def main(self, message: Message):
        """Code to be run for the modules' %% code.

        :return: The message to replace the message module mention with.
        """
        pass

    def help(self):
        """The help message when used with the `help` module.

        :return: The message to show when used as an argument for the `help` module.
        """
        return self.helpmsg

    def on_pubmsg(self, message: Message):
        """Code to be run for every message received.

        By default, does nothing.
        """
        pass

    def log_e(self, msg: str):
        """Log an error alongside the module's name to the window.

        :param msg: The error to log.
        """
        log.error(f"({self._name}) - {msg}")

    def log_w(self, msg: str):
        """Log a warning alongside the module's name to the window.

        :param msg: The warning to log.
        """
        log.warning(f"{self._name} - {msg}")

    def log_i(self, msg: str):
        """Log info alongside the module's name to the window.

        :param msg: The message to log.
        """
        log.info(f"({self._name}) - {msg}")

    def log_d(self, msg: str):
        """Log a debug message alongside the module's name to the window.

        :param msg: The debug info to log.
        """
        log.debug(f"({self._name}) - {msg}")

    def get_args(self, message: Message) -> list:
        """Consume `self.consumes` arguments from `message` for use as command arguments.

        :return: A list of every argument consumed, as `str`, or `None` if there's nothing to consume.
        """
        return message.consume(self.consumes)

    def get_args_lower(self, message: Message) -> list:
        """Consume `self.consumes` arguments from `message` for use as command arguments.

        :return: A list of every argument consumed (in lowercase), or False if there's nothing to consume.
        """
        args = self.get_args(message)

        if args:
            return [a.lower() for a in args]
        else:
            return False


def module_add(name: str):
    """Imports a new module and appends it to the modules dict.

    :param name: The path to the module. Path is relative to the `modules` folder.
    """
    log.debug(f"importing module {name}")

    try:
        # Create spec and import from directory.
        spec = importlib.util.spec_from_file_location(f"{name}", f"modules/{name}.py")
        module = importlib.util.module_from_spec(spec)

        # Execute it to fully import
        spec.loader.exec_module(module)

        # Give it its' own thread and start it up
        modules[name] = module.Module(bot, name)
        modules[name].start()

    except FileNotFoundError:
        raise ModuleNotFoundError(name)

    except Exception:
        log.error(f"failed to import module {name} with error trace:")
        traceback.print_exc()
        raise ModuleNotFoundError(name)


def module_del(name: str):
    """Call `module.__del__()` and remove it from `modules`.

    :param name: The name of the module.
    """
    log.debug(f"unimporting module {name}")

    if name not in modules:
        return

    modules[name].__del__()
    del modules[name]


def do_on_pubmsg(message: Message):
    """Runs the on_pubmsg() of every `Module` imported.

    :param message: The message this is acting on.
    """
    for module in modules.values():
        module.on_pubmsg(message)


def pass_bot_ref(ref):
    """Pass the bot reference so that modules can have a reference to it"""
    global bot
    bot = ref


commands = dict()
"""All commands for this `commands` module."""

modules = dict()
"""All currently imported modules."""

bot = object
"""The TwitchBot to pass to modules"""
