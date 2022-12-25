# This is a built-in function.
# Please do not modify this unless you really know what you're doing.

from src.commands import BaseModule


class Module(BaseModule):
    helpmsg = "Returns a mentioned user. If no user is mentioned, returns the last messages' author."

    consumes = 1

    def main(self):
        args = self.get_args()

        if not args:
            return self.bot.author.name

        user = args[0]
        if user[0] == "@":
            user = user[1:]

        return user
