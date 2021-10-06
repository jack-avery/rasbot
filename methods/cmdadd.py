# This is a built-in function.
# Please do not modify this unless you really know what you're doing.

import config
from definitions import VALID_COMMAND_REGEX,\
    MODONLY_ARG,\
    CommandGivenInvalidNameError,\
    CommandIsBuiltInError,\
    CommandMustHavePositiveCooldownError

def main(bot):
    try:
        cmd = bot.cmdargs[:]

        cmd_name = cmd.pop(0).lower()
        cmd_cooldown = int(cmd.pop(0))
        if(cmd[0].lower() == MODONLY_ARG):
            modonly = True
        else:
            modonly = False

        cmd.pop(0)

        bot.commands.command_modify(cmd_name,
                                    cmd_cooldown,
                                    " ".join(cmd),
                                    modonly)
        config.write(bot)
        
        return f'Command {cmd_name} added successfully.'

    except CommandIsBuiltInError:
        return 'You cannot modify built-in commands.'

    except CommandMustHavePositiveCooldownError:
        return 'Command must have a positive cooldown.'

    except CommandGivenInvalidNameError:
        return f'Command name must fit the regular expression {VALID_COMMAND_REGEX}.'

    except IndexError:
        return f'Please specify the name, cooldown in seconds, and response. Add {MODONLY_ARG} after the cooldown if you wish for the command to be mod-only.'

    except ValueError:
        return 'Cooldown must be a positive integer.'
