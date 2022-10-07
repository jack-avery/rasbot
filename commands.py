import importlib.util
import json
import os
import re
import threading
import time

from bot import TwitchBot
from definitions import VALID_COMMAND_REGEX,\
    MODULE_MENTION_REGEX,\
    CommandDoesNotExistError,\
    CommandGivenInvalidNameError,\
    CommandIsModOnlyError,\
    CommandMustHavePositiveCooldownError,\
    CommandStillOnCooldownError


class Command:
    def __init__(self, name: str, cooldown: int = 5, response: str = '', requires_mod: bool = False, hidden: bool = False):
        '''Creates a new command.

        :param name: The name of the command.

        :param cooldown: The cooldown of the command in seconds.

        :param response: The text response of the command. Encapsulate custom commands in &&.

        :param requires_mod: Whether the command requires the user to be a mod.

        :param hidden: Whether the command should be hidden from help.
        '''
        self.name = name.lower()
        self.cooldown = cooldown
        self.response = response
        self.requires_mod = requires_mod
        self.hidden = hidden

        self._last_used = 0

    def run(self, bot):
        """Code to be run when this command is called from chat.

        Runs all && codes found in the command and returns the result.
        """
        # Make sure the command is not on cooldown before doing anything
        if not time.time()-self._last_used > self.cooldown:
            raise CommandStillOnCooldownError(
                f"Command {self.name} called by {bot.author_name} while still on cooldown")

        # Do not allow non-moderators to use mod-only commands
        if not bot.author_ismod and self.requires_mod:
            raise CommandIsModOnlyError(
                f"Mod-only command {self.name} called by non-mod {bot.author_name}")

        # Apply any methods encased in &&
        returned_response = self.response
        for m in module_re.findall(returned_response):
            try:
                returned_response = returned_response.replace(
                    f'&{m}&',
                    str(modules[m].main())
                )
            except KeyError:
                raise KeyError(
                    f'Command {self.name} calls unimported/nonexistent module {m}')

        # Update the last usage time and return the response
        self._last_used = time.time()

        return returned_response


def command_modify(name: str, cooldown: int = 5, response: str = '', requires_mod: bool = False, hidden: bool = False, ignore_builtin_check: bool = False):
    '''Creates a new command (or modifies an existing one),
    and appends it to the commands dict.

    Automatically attempts to import any unimported modules.

    :param name: The name of the command.

    :param cooldown: The cooldown of the command in seconds.

    :param response: The text response of the command. Encapsulate custom commands in &&.

    :param requires_mod: Whether this command requires moderator access to use.

    :param hidden: Whether to hide this command from the 'help' module.

    :param ignore_builtin_check: Whether to ignore the built-in module check. Use at your own risk!
    '''
    bot.log_debug(
        f'Importing command "{name} {cooldown} {requires_mod} {hidden} {response}"')

    # Command cannot have a negative cooldown
    if cooldown < 0:
        raise CommandMustHavePositiveCooldownError(
            f"command {name} provided invalid cooldown length {cooldown}")

    # Command must match the regex defined by VALID_COMMAND_REGEX
    if not command_re.match(name):
        raise CommandGivenInvalidNameError(
            f"command provided invalid name {name}")

    if not response:
        bot.log_error(
            f"Command {name} might have imported incorrectly: empty response?")

    # Resolve any modules the command mentions and import new ones
    for m in module_re.findall(response):
        try:
            module_add(m)
        except ModuleNotFoundError as err:
            raise err

    commands[name] = Command(name, cooldown, response, requires_mod, hidden)


def command_del(name: str):
    '''Deletes a command and removes it from the dict.

    :param name: The name of the command.
    '''
    # Command must match the regex defined by VALID_COMMAND_REGEX
    if not command_re.match(name):
        raise CommandGivenInvalidNameError(
            f"command provided invalid name {name}")

    try:
        del (commands[name])
    except KeyError:
        raise CommandDoesNotExistError(f'command {name} does not exist')


class BaseModule(threading.Thread):
    """The base class for a Module, custom or not.

    Facilitates defaults for a Module so as to prevent errors.
    """
    helpmsg = 'No help message available for module.'

    def __init__(self, bot: TwitchBot, name, cfgdefault=None):
        """Initialize a module. If a `cfgdefault` is given,
        it will drop the given default into the user's config directory.
        """
        threading.Thread.__init__(self)
        self.bot = bot
        self._name = name

        # Persistent config loading: create base folder.
        if not os.path.exists("modules/config"):
            os.mkdir("modules/config")

        if not os.path.exists(f"modules/config/{self.bot.channel_id}"):
            os.mkdir(f"modules/config/{self.bot.channel_id}")

        self._cfg_path = f"modules/config/{self.bot.channel_id}/{name}.txt"

        # If no config found and a default provided, create it
        if not os.path.exists(self._cfg_path):
            if cfgdefault:
                with open(self._cfg_path, 'w') as cfg:
                    cfg.write(json.dumps(cfgdefault, indent=4))

        # Load config
        if os.path.exists(self._cfg_path):
            with open(self._cfg_path, 'r') as cfg:
                self.cfg = json.loads(cfg.read())

    def save_config(self):
        """Save the current form of this module's `self.cfg` attribute to file.
        """
        with open(f"modules/config/{self.bot.channel_id}/{self._name}.txt", 'w') as cfg:
            cfg.write(json.dumps(self.cfg, indent=4))

    def main(self):
        """Code to be run for the modules' && code.
        """
        pass

    def help(self):
        """The help message when used with the `help` module.
        """
        return self.helpmsg

    # Default per-message function.
    def on_pubmsg(self):
        """Code to be run for every message received.

        By default, does nothing.
        """
        pass


def module_add(name: str):
    '''Imports a new module and appends it to the modules dict.

    :param name: The name of the module. File must be visible in the modules folder.
    '''
    # Don't reimport a module already imported
    if name in modules:
        return

    bot.log_debug(f"Importing module {name}.py")

    try:
        # Create spec and import from directory.
        spec = importlib.util.spec_from_file_location(
            f"{name}", f"modules/{name}.py")
        module = importlib.util.module_from_spec(spec)

        # Execute it to fully import
        spec.loader.exec_module(module)

        # Give it its' own thread and start it up
        modules[name] = module.Module(bot, name)
        modules[name].start()
    except FileNotFoundError:
        raise ModuleNotFoundError(f"{name} does not exist in modules folder")


def do_on_pubmsg_methods():
    """Runs the on_pubmsg() of every Module imported from `./modules`.
    """
    for module in modules.values():
        module.on_pubmsg()


def pass_bot_ref(ref: TwitchBot):
    global bot
    """Set up this instance of commands
    """
    bot = ref


commands = dict()
commands_modules = list()
modules = dict()
bot = TwitchBot
command_re = re.compile(VALID_COMMAND_REGEX)
module_re = re.compile(MODULE_MENTION_REGEX)
