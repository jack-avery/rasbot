# This is a test method. Feel free to use it as a template.

from commands import BaseMethod

class Method(BaseMethod):
    def __init__(self):
        self.count = 0

    # Show the amount of messages since the bot started
    def main(self, bot):
        return self.count

    # Count messages since the bot started
    def per_message(self, bot):
        self.count+=1
