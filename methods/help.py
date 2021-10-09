# This is a built-in function.
# Please do not modify this unless you really know what you're doing.

def main(bot):
    # If no command is provided, just run the base help message.
    if len(bot.cmdargs) == 0:
        return f"Available commands are: {', '.join(bot.commands.commands)}"
    
    # If a command is provided, run the help for it.
    else:
        method = bot.cmdargs[0].lower()

        if method in bot.commands.methods.keys():
            return str(bot.commands.methods[method].help())
        
        else:
            return f'Method {method} not found.'

def help():
    return 'Prints all available commands, or, if provided a method, prints the help message for that method. Usage: help <method?>'
