# This module contains debug commands mostly used for development purposes.
# This will likely grow as more cases for admin commands are needed.

import semantic_version

from src.commands import BaseModule, NO_MESSAGE_SIGNAL
from src.definitions import Message


class Module(BaseModule):
    helpmsg = "Perform an administrative action on the currently running rasbot intance. Usage: admin <command>"

    consumes = -1

    default_config = {
        "grant_uids": [],
        # A list of User IDs to grant `admin` module access to.
        # Mostly for debugging.
    }

    def main(self, message: Message):
        # only the channel owner can run admin commands
        if not message.author.is_host or str(message.author.uid) not in self.cfg_get(
            "grant_uids"
        ):
            return NO_MESSAGE_SIGNAL

        args = self.get_args_lower(message)

        if not args:
            return NO_MESSAGE_SIGNAL

        match args[0]:
            case "grant":
                if not message.author.is_host:
                    return "only broadcaster can grant admin privileges"

                admins = self.cfg_get("grant_uids")
                admins.append(args[1])
                self.cfg_set("grant_uids", admins)

                return f"added {args[1]} to admins"

            case "revoke":
                if not message.author.is_host:
                    return "only broadcaster can revoke admin privileges"

                admins = self.cfg_get("grant_uids")
                if args[1] not in admins:
                    return "user not in admins"

                del admins[admins.index(args[1])]
                self.cfg_set("grant_uids", admins)

                return f"removed {args[1]} from admins"

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

            case "version":
                with open("version", "r") as verfile:
                    try:
                        return semantic_version.Version(verfile.read())
                    except ValueError:
                        return "version file is invalid?"

            case "save":
                self._bot.save()
                return "saved current config"

            case "reload":
                self._bot.reload()
                return "reloaded"
