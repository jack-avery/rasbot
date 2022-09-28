# This is a built-in function.
# Please do not modify this unless you really know what you're doing.

from commands import BaseModule
import config
from definitions import DEFAULT_CONFIG


class Module(BaseModule):
    helpmsg = f'Sets a new prefix for the bot. Usage: prefix <prefix?>'

    def main(self, bot):
        if not bot.cmdargs:
            newprefix = DEFAULT_CONFIG['meta']['prefix']
        else:
            newprefix = bot.cmdargs[0].lower()

        if newprefix.startswith('/'):
            return f'Prefix cannot start with Twitch reserved character /.'

        bot.prefix = newprefix
        config.write(bot)
        return f'Prefix updated to {newprefix}.'
