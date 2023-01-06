# This is a built-in function.
# Please do not modify this unless you really know what you're doing.

from src.commands import BaseModule
from src.definitions import Message


class Module(BaseModule):
    helpmsg = "Deletes an existing command. Usage: cmddel <name>."

    consumes = 1

    def __init__(self, bot, name):
        BaseModule.__init__(self, bot, name)

        self.log_e(
            "This module will be removed soon! Remove it and add the 'cmd' command instead.")

    def main(self, message: Message):
        cmd = self.get_args_lower(message)

        if not cmd:
            return "No command provided."
        cmd = cmd[0]

        if cmd not in self._bot.commands.commands:
            return "Command does not exist."

        # to delete and write config
        self._bot.commands.command_del(cmd)
        self._bot.save()

        return f'Command removed successfully.'
