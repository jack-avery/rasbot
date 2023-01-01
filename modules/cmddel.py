# This is a built-in function.
# Please do not modify this unless you really know what you're doing.

from src.commands import BaseModule
from src.definitions import Message,\
    CommandDoesNotExistError


class Module(BaseModule):
    helpmsg = "Deletes an existing command. Usage: cmddel <name>."

    consumes = 1

    def main(self, message: Message):
        cmd = self.get_args_lower(message)

        if not cmd:
            return "No command provided."

        try:
            # try to delete and write config
            self._bot.commands.command_del(cmd[0])
            self._bot.save()

            return f'Command {cmd[0]} removed successfully.'

        except CommandDoesNotExistError:
            return f'Command {cmd[0]} does not exist.'
