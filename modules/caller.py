# This is a built-in function.
# Please do not modify this unless you really know what you're doing.

from commands import BaseModule


class Module(BaseModule):
    helpmsg = 'Returns the name of the caller.'

    def main(self, bot):
        return bot.caller_name
