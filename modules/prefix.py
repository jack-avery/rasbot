# This is a built-in function.
# Please do not modify this unless you really know what you're doing.

from commands import BaseModule

DEFAULT_CONFIG = {
    "default": "r!"
}

class Module(BaseModule):
    helpmsg = f'Sets a new prefix for the bot. Usage: prefix <prefix?>'

    def __init__(self, bot, name):
        BaseModule.__init__(self, bot, name, DEFAULT_CONFIG)

    def main(self):
        if not self.bot.cmdargs:
            newprefix = self.cfg_get('default')
        else:
            newprefix = self.bot.cmdargs[0].lower()

        if newprefix.startswith('/'):
            return f'Prefix cannot start with Twitch reserved character /.'

        self.bot.prefix = newprefix
        self.bot.write_config()
        return f'Prefix updated to {newprefix}.'
