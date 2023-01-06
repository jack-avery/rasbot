# This is a built-in function.
# Please do not modify this unless you really know what you're doing.

import re

from src.commands import BaseModule
from src.definitions import Message

VALID_COMMAND_RE = re.compile(r'[a-z0-9_]+')
"""Regex to compare given command names to for validation."""


class Module(BaseModule):
    helpmsg = "Adds a new command, or modifies an existing one. Usage: cmdadd <name> <cooldown?> <params?> <response>."

    default_config = {
        # The parameters to be given, after cooldown, before response
        # to indicate this command should be mod-only or hidden from !help
        "modonly_arg": "-modonly",
        "hidden_arg": "-hidden",
        # The default cooldown to apply to a command if none is specified
        "default_cooldown": 5,
    }

    consumes = -1

    def __init__(self, bot, name):
        BaseModule.__init__(self, bot, name)

        self.log_e(
            "This module will be removed soon! Remove it and add the 'cmd' command instead.")

        self.MODONLY_ARG = self.cfg_get('modonly_arg')
        self.HIDDEN_ARG = self.cfg_get('hidden_arg')
        self.DEFAULT_COOLDOWN = self.cfg_get('default_cooldown')

    def main(self, message: Message):
        cmd = self.get_args(message)

        if not cmd:
            return "No command information given."

        if len(cmd) < 2:
            return "Not enough parameters! You must pass at least a name and a response."

        # use lower of next item as name
        cmd_name = cmd.pop(0).lower()

        # try to use next item as cooldown in seconds
        # if it can't convert to int, use default
        try:
            cmd_cooldown = int(cmd[0])
            cmd.pop(0)
        except ValueError:
            cmd_cooldown = self.DEFAULT_COOLDOWN

        # check for parameters and consume if found
        params = {
            self.MODONLY_ARG: False,
            self.HIDDEN_ARG: False
        }
        for _ in params:
            for param in params:
                if (cmd[0].lower() == param):
                    params[param] = True
                    cmd.pop(0)

        # verify all parameters are valid
        if not VALID_COMMAND_RE.match(cmd_name):
            return "Command name can only use alphanumeric characters and underscores (_)."

        if cmd_cooldown < 0:
            return "Command cooldown must be a positive integer."

        try:
            # add command and write config
            self._bot.commands.command_add(cmd_name,
                                           cmd_cooldown,
                                           " ".join(cmd),
                                           params[self.MODONLY_ARG],
                                           params[self.HIDDEN_ARG])
            self._bot.save()

            return f'Command {cmd_name} added successfully.'

        except ModuleNotFoundError as mod:
            return f'Module {mod} does not exist in the modules folder..'

        except AttributeError as mod:
            return f'Module {mod} does not have a "Module" class to import.'

        except IndexError:
            return 'Command is missing required information.'
