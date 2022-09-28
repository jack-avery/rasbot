# This is a built-in function.
# Please do not modify this unless you really know what you're doing.

from commands import BaseModule
import config
from definitions import VALID_COMMAND_REGEX,\
    DEFAULT_COOLDOWN,\
    MODONLY_ARG,\
    HIDDEN_ARG,\
    CommandGivenInvalidNameError,\
    CommandIsBuiltInError,\
    CommandMustHavePositiveCooldownError


class Module(BaseModule):
    helpmsg = 'Adds a new command, or modifies an existing one. Usage: cmdadd <name> <cooldown?> <mod-only?> <hidden?> <response>.'

    def main(self, bot):
        try:
            cmd = bot.cmdargs[:]

            cmd_name = cmd.pop(0).lower()

            try:
                cmd_cooldown = int(cmd[0])
                cmd.pop(0)
            except ValueError:
                cmd_cooldown = DEFAULT_COOLDOWN

            if (cmd[0].lower() == MODONLY_ARG):
                modonly = True
                cmd.pop(0)
            else:
                modonly = False

            if (cmd[0].lower() == HIDDEN_ARG):
                hidden = True
                cmd.pop(0)
            else:
                hidden = False

            bot.commands.command_modify(cmd_name,
                                        cmd_cooldown,
                                        " ".join(cmd),
                                        modonly,
                                        hidden)
            config.write(bot)

            return f'Command {cmd_name} added successfully.'

        except CommandIsBuiltInError:
            return 'You cannot modify built-in commands.'

        except CommandMustHavePositiveCooldownError:
            return 'Command must have a positive cooldown.'

        except CommandGivenInvalidNameError:
            return f'Command name must fit the regular expression {VALID_COMMAND_REGEX}.'

        except IndexError:
            return f'Invalid usage.'

        except ValueError:
            return 'Cooldown must be a positive integer.'

        except ModuleNotFoundError as err:
            return f'Module {err} does not exist.'
