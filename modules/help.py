# This is a built-in function.
# Please do not modify this unless you really know what you're doing.

import re

from commands import BaseModule
from definitions import MODULE_MENTION_REGEX


class Module(BaseModule):
    helpmsg = 'Prints all available commands, or, if provided a method, prints the help message for that method. Usage: help <method?>'

    def __init__(self, bot, name):
        BaseModule.__init__(self, bot, name)
        self.module_re = re.compile(MODULE_MENTION_REGEX)

    def main(self):
        # If no command is provided, just run the base help message.
        if not self.bot.cmdargs:
            user_commands_list = ', '.join(
                [n for n, c in self.bot.commands.commands.items() if not c.hidden and not c.requires_mod])
            mod_commands_list = ', '.join(
                [n for n, c in self.bot.commands.commands.items() if not c.hidden and c.requires_mod])
            return f"Available commands are: {user_commands_list} (mod-only: {mod_commands_list})"

        # If a command is provided, run the help for it.
        else:
            name = self.bot.cmdargs[0].lower()

            if name in self.bot.commands.modules:
                return str(self.bot.commands.modules[name].help())

            elif name in self.bot.commands.commands:
                command_modules = self.module_re.findall(self.bot.commands.commands[name].response)

                if command_modules:
                    return str(f"Module '{name}' not found, but the matching command uses module(s): "
                            + f"{', '.join(command_modules)}")
                
                else:
                    return str(f"Command {name} does not mention any modules.")

            else:
                return "No matching command or module."
