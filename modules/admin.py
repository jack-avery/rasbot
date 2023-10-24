# This module contains debug commands mostly used for development purposes.
# This will likely grow as more cases for admin commands are needed.

import json

from src.plugins import BaseModule
from src.definitions import Message, NO_MESSAGE_SIGNAL
from update import RASBOT_BASE_MANIFEST


class Module(BaseModule):
    helpmsg = "Perform an administrative action on the currently running rasbot intance. Usage: admin <command>"

    consumes = -1

    default_config = {
        "grant_uids": [],
        # A list of User IDs to grant `admin` module access to.
        # Mostly for debugging.
    }

    def __init__(self, bot, name):
        BaseModule.__init__(self, bot, name)

        # Add channel owner to admin enabled UIDs
        grant_uids = self.cfg_get("grant_uids")
        if self._bot.channel_id not in grant_uids:
            grant_uids.append(self._bot.channel_id)
            self.cfg_set("grant_uids", grant_uids)

    def main(self, message: Message):
        # only permitted users may use debug commands
        if message.author.uid not in self.cfg_get("grant_uids"):
            return NO_MESSAGE_SIGNAL

        args = self.get_args_lower(message)

        if not args:
            return NO_MESSAGE_SIGNAL

        match args[0]:
            case "uid":
                user = args[1]
                if user.startswith("@"):
                    user = user[1:]

                return self._bot.auth.get_user_id(user)

            case "grant":
                if not message.author.is_host:
                    return "only broadcaster can grant admin privileges"

                uid = int(args[1])

                admins = self.cfg_get("grant_uids")
                admins.append(uid)
                self.cfg_set("grant_uids", admins)

                return f"added {uid} to admins"

            case "revoke":
                if not message.author.is_host:
                    return "only broadcaster can revoke admin privileges"

                uid = int(args[1])

                admins = self.cfg_get("grant_uids")
                if uid not in admins:
                    return "user not in admins"

                del admins[admins.index(uid)]
                self.cfg_set("grant_uids", admins)

                return f"removed {uid} from admins"

            case "import":
                self._bot.modules_handler.add(args[1])
                return f"imported {args[1]}"

            case "unimport":
                self._bot.modules_handler.delete(args[1])
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
                with open(RASBOT_BASE_MANIFEST, "r") as manifestfile:
                    manifest = json.loads(manifestfile.read())
                    return manifest["version"]

            case "save":
                self._bot.save()
                return "saved current config"

            case "reload":
                self._bot.reload()
                return "reloaded"
