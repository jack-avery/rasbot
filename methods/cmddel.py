# This is a built-in function.
# Please do not modify this unless you really know what you're doing.

from definitions import CommandDoesNotExistError,\
    CommandIsBuiltInError
import config

def main(bot):
    cmd = bot.cmdargs

    try:
        bot.commands.command_del(cmd[0].lower())
        config.write(bot)
        
        return f'Command {cmd[0]} removed successfully.'

    except CommandIsBuiltInError:
        return 'You cannot modify built-in commands.'

    except CommandDoesNotExistError:
        return f'Command {cmd[0]} does not exist.'
