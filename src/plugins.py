from importlib.util import spec_from_file_location, module_from_spec
import logging
import threading
import traceback

from src.config import ConfigHandler
from src.definitions import Message


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

    def __init__(self, bot, name: str):
        """Initialize a module. If a `cfgdefault` is given,
        it will drop the given default into the user's config directory.
        """
        threading.Thread.__init__(self)
        self._bot = bot
        self._name = name

        self._cfghandler = ConfigHandler(
            f"{self._bot.channel_id}/modules/{name}.txt", self.default_config
        )

        self.reload_config()

    def __del__(self):
        """Destroy this module. Does nothing by default.

        Used in `xp` to teardown the thread for faster closing through Ctrl+C.
        """
        pass

    def reload_config(self):
        """Completely reload this module's config from file."""
        self._cfg = self._cfghandler.read()

    def save_config(self):
        """Save the current form of this module's `self.cfg` attribute to file."""
        self._cfghandler.write(self._cfg)

    def cfg_get(self, key: str):
        """Read the given config dict key. If it fails to read it will fill it in with the default.

        :param key: The key to grab the value of

        :return: The value of `self._cfg[key]`
        """
        try:
            return self._cfg.setdefault(key, self.default_config[key])

        except KeyError:
            self.log_e(f"attempt to grab invalid key {key}? ignoring")
            return None

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

        :param msg: The error to logging.
        """
        logging.error(f"({self._name}) - {msg}")

    def log_w(self, msg: str):
        """Log a warning alongside the module's name to the window.

        :param msg: The warning to logging.
        """
        logging.warning(f"{self._name} - {msg}")

    def log_i(self, msg: str):
        """Log info alongside the module's name to the window.

        :param msg: The message to logging.
        """
        logging.info(f"({self._name}) - {msg}")

    def log_d(self, msg: str):
        """Log a debug message alongside the module's name to the window.

        :param msg: The debug info to logging.
        """
        logging.debug(f"({self._name}) - {msg}")

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


class ModulesHandler:
    modules: dict[str, BaseModule]
    """List of available modules."""

    def __init__(self, bot):
        self.bot = bot
        self.modules = {}

    def get(self, module: str) -> BaseModule:
        return self.modules.get(module, None)

    def add(self, name: str):
        """Imports a new module and appends it to the modules dict.

        :param name: The path to the module. Path is relative to the `modules` folder.
        """
        logging.debug(f"importing module {name}")

        try:
            # Create spec and import from directory.
            spec = spec_from_file_location(f"{name}", f"modules/{name}.py")
            module = module_from_spec(spec)
            spec.loader.exec_module(module)

            # Give it its' own thread and start it up
            self.modules[name] = module.Module(self.bot, name)
            self.modules[name].start()

        except FileNotFoundError:
            raise ModuleNotFoundError(name)

        except Exception:
            err_str = traceback.format_exc()
            logging.error(f"failed to import module {name} with error trace:")
            logging.error(err_str)
            raise ModuleNotFoundError(name)

    def delete(self, name: str):
        """Call `module.__del__()` and remove it from `modules`.

        :param name: The name of the module.
        """
        logging.debug(f"unimporting module {name}")

        if name not in self.modules:
            return

        self.modules[name].__del__()
        del self.modules[name]

    def run(self, name: str, message: Message) -> str | None:
        module: BaseModule = self.modules.get(name, None)
        if not module:
            return None

        return module.main(message)

    def do_on_pubmsg(self, message: Message):
        """Runs the on_pubmsg() of every `Module` imported.

        :param message: The message this is acting on.
        """
        for module in self.modules.values():
            module.on_pubmsg(message)
