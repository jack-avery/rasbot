# This is a built-in function.
# Please do not modify this unless you really know what you're doing.

from src.commands import BaseModule


class Module(BaseModule):
    helpmsg = "Returns the display name of the last messages' author."

    def main(self):
        return self.bot.author.name
