# This is a built-in function.
# Please do not modify this unless you really know what you're doing.

from commands import BaseModule
from definitions import VALID_COMMAND_REGEX,\
    CommandDoesNotExistError,\
    CommandGivenInvalidNameError
import config


class Module(BaseModule):
    helpmsg = 'Deletes an existing command. Usage: cmddel <name>.'

    def main(self):
        cmd = self.bot.cmdargs

        try:
            self.bot.commands.command_del(cmd[0].lower())
            config.write(self.bot)

            return f'Command {cmd[0]} removed successfully.'

        except CommandDoesNotExistError:
            return f'Command {cmd[0]} does not exist.'

        except CommandGivenInvalidNameError:
            return f'Command name must fit the regular expression {VALID_COMMAND_REGEX}.'
