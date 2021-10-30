# This is a test method. Feel free to use it as a template.

from commands import BaseMethod

class Method(BaseMethod):
    # Echo the user's message back to them
    def main(self, bot):
        return ' '.join(bot.cmdargs)
