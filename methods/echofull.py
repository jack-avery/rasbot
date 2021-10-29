# This is a test function. Feel free to use it as a template.

from commands import BaseMethod

class Method(BaseMethod):
    def __init__(self):
        self.count = 0

    # Show the amount of messages since the bot started
    # and echo the user's message back to them
    def main(self, bot):
        return f"{self.count}, {' '.join(bot.cmdargs)}"

    # Count messages since the bot started
    def per_message(self, bot):
        self.count+=1