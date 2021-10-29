# This is a built-in function.
# Please do not modify this unless you really know what you're doing.

from commands import BaseMethod
import config
from definitions import DEFAULT_PREFIX

class Method(BaseMethod):
    def main(self, bot):
        if len(bot.cmdargs) == 0:
            newprefix = DEFAULT_PREFIX
        else:
            newprefix = bot.cmdargs[0].lower()
        
        if newprefix.startswith('/'):
            return f'Prefix start with Twitch reserved character /.'
        
        bot.prefix = newprefix
        config.write(bot)
        return f'Prefix updated to {newprefix}.'

    def help(self):
        return f'Sets a new prefix for the bot. Default is {DEFAULT_PREFIX}. Usage: prefix <prefix?>'
