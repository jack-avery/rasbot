# This module contains debug commands mostly used for development purposes.
# This will likely grow as more cases for admin commands are needed.

from commands import BaseModule
from definitions import NO_MESSAGE_SIGNAL


class Module(BaseModule):

    consumes = -1

    def main(self):
        # only the channel owner can run admin commands
        if not self.bot.author.host:
            return NO_MESSAGE_SIGNAL

        args = self.get_args_lower()

        if not args:
            return NO_MESSAGE_SIGNAL

        match args[0]:
            case "import":
                self.bot.commands.module_add(args[1])
                return f"imported {args[1]}"

            case "unimport":
                self.bot.commands.module_del(args[1])
                return f"unimported {args[1]}"
