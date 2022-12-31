# This module contains debug commands mostly used for development purposes.
# This will likely grow as more cases for admin commands are needed.

from src.commands import BaseModule
from src.definitions import Message,\
    NO_MESSAGE_SIGNAL


class Module(BaseModule):

    consumes = -1

    def main(self, message: Message):
        # only the channel owner can run admin commands
        if not message.author.host:
            return NO_MESSAGE_SIGNAL

        args = self.get_args_lower(message)

        if not args:
            return NO_MESSAGE_SIGNAL

        match args[0]:
            case "import":
                self._bot.commands.module_add(args[1])
                return f"imported {args[1]}"

            case "unimport":
                self._bot.commands.module_del(args[1])
                return f"unimported {args[1]}"

            case "alwaysimportadd":
                if args[1] in self._bot.always_import_list:
                    return "already present"

                self._bot.always_import_list.append(args[1])
                self._bot.save()
                return f"{args[1]} added to always import list (restart or use 'admin reload' to take effect)"

            case "alwaysimportdel":
                if args[1] not in self._bot.always_import_list:
                    return "not present"

                self._bot.always_import_list.remove(args[1])
                self._bot.save()
                return f"{args[1]} removed from always import list (restart or use 'admin reload' to take effect)"

            case "save":
                self._bot.save()
                return "saved current config"

            case "reload":
                self._bot.reload()
                return "reloaded"
