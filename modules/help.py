# This is a built-in function.
# Please do not modify this unless you really know what you're doing.

from src.plugins import BaseModule
from src.definitions import Author, Message


class Module(BaseModule):
    helpmsg = "Prints all available commands, or, if provided a module, prints the help message for that module. Usage: help <module?>"

    consumes = 1

    def main(self, message: Message):
        args = self.get_args_lower(message)

        # If no command is provided, just run the base help message.
        if not args:
            # list of all commands (not hidden, not mod-only)
            user_commands_list = ", ".join(
                [
                    n
                    for n, c in self._bot.commands_handler.commands.items()
                    if not c.hidden and not c.privilege > Author.Privilege.VIP
                ]
            )
            # list of all commands (not hidden, mod-only)
            mod_commands_list = ", ".join(
                [
                    n
                    for n, c in self._bot.commands_handler.commands.items()
                    if not c.hidden and c.privilege > Author.Privilege.VIP
                ]
            )

            return f"Available commands are: {user_commands_list} (mod-only: {mod_commands_list})"

        # If a command is provided, run the help for it.
        else:
            name = args[0]

            # if the name resolves to a module, give the module's helpmsg
            if name in self._bot.modules_handler.modules:
                return self._bot.modules_handler.modules[name].help()

            # if not a module and resolves to a command...
            elif name in self._bot.commands_handler.commands:
                # see if it mentions any modules
                command_modules = self._bot.commands_handler.get(
                    name
                ).get_used_modules()

                # if it does, give the modules it mentions
                if command_modules:
                    return str(
                        f"Module '{name}' not found, but the matching command uses module(s): "
                        + f"{', '.join(command_modules)}"
                    )

                else:
                    return str(f"Command {name} does not mention any modules.")

            else:
                return "No matching command or module."
