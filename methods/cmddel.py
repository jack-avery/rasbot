# This is a built-in function.
# Please do not modify this unless you really know what you're doing.

from commands import BaseMethod
from definitions import VALID_COMMAND_REGEX,\
    CommandDoesNotExistError,\
    CommandIsBuiltInError,\
    CommandGivenInvalidNameError
import config

class Method(BaseMethod):
    def main(self,bot):
        cmd = bot.cmdargs

        try:
            bot.commands.command_del(cmd[0].lower())
            config.write(bot)
            
            return f'Command {cmd[0]} removed successfully.'

        except CommandIsBuiltInError:
            return 'You cannot modify built-in commands.'

        except CommandDoesNotExistError:
            return f'Command {cmd[0]} does not exist.'

        except CommandGivenInvalidNameError:
            return f'Command name must fit the regular expression {VALID_COMMAND_REGEX}.'

    def help(self):
        return 'Deletes an existing command. Usage: cmddel <name>.'
