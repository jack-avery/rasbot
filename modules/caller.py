# This is a built-in function.
# Please do not modify this unless you really know what you're doing.

from src.plugins import BaseModule
from src.definitions import Message


class Module(BaseModule):
    helpmsg = "Returns the display name of the last messages' author."

    def main(self, message: Message):
        return message.author.name
