# This is a test method. Feel free to use it as a template.

from commands import BaseModule


class Module(BaseModule):
    # Echo the user's message back to them
    def main(self, bot):
        return ' '.join(bot.cmdargs)
