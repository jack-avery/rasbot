# This is a built-in function.
# Please do not modify this unless you really know what you're doing.

from src.commands import BaseModule
from src.definitions import CommandDoesNotExistError


class Module(BaseModule):
    helpmsg = 'Deletes an existing command. Usage: cmddel <name>.'

    consumes = 1

    def main(self):
        args = self.get_args_lower()

        if not args:
            return "No command provided."

        # convert argument to lower
        cmd = args[0]

        try:
            # try to delete and write config
            self.bot.commands.command_del(cmd)
            self.bot.write_config()

            return f'Command {cmd} removed successfully.'

        except CommandDoesNotExistError:
            return f'Command {cmd} does not exist.'
