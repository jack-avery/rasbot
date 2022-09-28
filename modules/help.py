# This is a built-in function.
# Please do not modify this unless you really know what you're doing.

import re
import threading

from commands import BaseModule
from definitions import MODULE_MENTION_REGEX


class Module(BaseModule):
    helpmsg = 'Prints all available commands, or, if provided a method, prints the help message for that method. Usage: help <method?>'

    def __init__(self):
        threading.Thread.__init__(self)
        self.module_re = re.compile(MODULE_MENTION_REGEX)

    def main(self, bot):
        # If no command is provided, just run the base help message.
        if not bot.cmdargs:
            user_commands_list = ', '.join(
                [n for n, c in bot.commands.commands.items() if not c.hidden and not c.requires_mod])
            mod_commands_list = ', '.join(
                [n for n, c in bot.commands.commands.items() if not c.hidden and c.requires_mod])
            return f"Available commands are: {user_commands_list} (mod-only: {mod_commands_list})"

        # If a command is provided, run the help for it.
        else:
            module = bot.cmdargs[0].lower()

            if module in bot.commands.modules:
                return str(bot.commands.modules[module].help())

            if module in bot.commands.commands:
                return str(f"Module '{module}' not found, but the matching command uses module(s): "
                           + f"{', '.join(self.module_re.findall(bot.commands.commands[module].response))}")
