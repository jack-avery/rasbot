# This is a built-in function.
# Please do not modify this unless you really know what you're doing.

import config

def main(bot):
    if len(bot.cmdargs) == 0:
        newprefix = "r!"
    else:
        newprefix = bot.cmdargs[0]
    
    bot.prefix = newprefix
    config.write(bot)
    return f'Prefix updated to {newprefix}.'
