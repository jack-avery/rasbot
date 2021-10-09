# This is a built-in function.
# Please do not modify this unless you really know what you're doing.

def main(bot):
    # If no command is provided, just run the base help message.
    if len(bot.cmdargs) == 0:
        return f"Available commands are: {', '.join(bot.commands.commands)}"
    
    # If a command is provided, run the help for it.
    else:
        cmd = bot.cmdargs[0].lower()

        if cmd in bot.commands.methods.keys():
            return str(bot.commands.methods[cmd].help())
        
        else:
            return f'Command {cmd} not found.'

def help():
    return 'Prints all available commands, or, if provided a command, prints the help message for that command. Usage: help <command?>'
