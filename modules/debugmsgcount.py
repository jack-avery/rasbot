# This is a test method. Feel free to use it as a template.

from commands import BaseModule


class Module(BaseModule):
    def __init__(self):
        # Make sure you call BaseModule init if overriding!
        BaseModule.__init__(self)
        self.count = 0

    # Show the amount of messages since the bot started
    def main(self, bot):
        return self.count

    # Count messages since the bot started
    def on_pubmsg(self, bot):
        self.count += 1
