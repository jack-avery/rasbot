# This is a built-in function.
# Please do not modify this unless you really know what you're doing.

from src.plugins import BaseModule
from src.definitions import Message


class Module(BaseModule):
    helpmsg = "Returns a mentioned user. If no user is mentioned, returns the last messages' author."

    consumes = 1

    def main(self, message: Message):
        args = self.get_args(message)

        if not args:
            return message.author.name

        user = args[0]
        if user.startswith("@"):
            return user[1:]

        return user
