# This is a built-in function.
# Please do not modify this unless you really know what you're doing.

from commands import BaseModule

class Module(BaseModule):
    def main(self,bot):
        # If no command is provided, just run the base help message.
        if len(bot.cmdargs) == 0:
            user_commands_list = ', '.join( [n for n,c in bot.commands.commands.items() if not c.hidden and not c.requires_mod] )
            mod_commands_list  = ', '.join( [n for n,c in bot.commands.commands.items() if not c.hidden and c.requires_mod] )
            return f"Available commands are: {user_commands_list} (mod-only: {mod_commands_list})"
        
        # If a command is provided, run the help for it.
        else:
            method = bot.cmdargs[0].lower()

            if method in bot.commands.methods.keys():
                return str(bot.commands.methods[method].help())
            
            else:
                return f'Method {method} not found.'

    def help(self):
        return 'Prints all available commands, or, if provided a method, prints the help message for that method. Usage: help <method?>'
