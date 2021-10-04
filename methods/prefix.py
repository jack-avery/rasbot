# This is a built-in function.
# Please do not modify this unless you really know what you're doing.

import config
from definitions import DEFAULT_PREFIX

def main(bot):
    if len(bot.cmdargs) == 0:
        newprefix = DEFAULT_PREFIX
    else:
        newprefix = bot.cmdargs[0]
    
    bot.prefix = newprefix
    config.write(bot)
    return f'Prefix updated to {newprefix}.'
