# This is a built-in function.
# Please do not modify this unless you really know what you're doing.

from commands import BaseModule
from definitions import CommandDoesNotExistError


class Module(BaseModule):
    helpmsg = 'Deletes an existing command. Usage: cmddel <name>.'

    def main(self):
        if not self.bot.cmdargs:
            return "No command provided."

        # convert argument to lower
        cmd = self.bot.cmdargs[0].lower()

        try:
            # try to delete and write config
            self.bot.commands.command_del(cmd)
            self.bot.write_config()

            return f'Command {cmd} removed successfully.'

        except CommandDoesNotExistError:
            return f'Command {cmd} does not exist.'
