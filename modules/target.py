# This is a built-in function.
# Please do not modify this unless you really know what you're doing.

from commands import BaseModule

class Module(BaseModule):
    helpmsg = 'Returns a mentioned user. If no user is mentioned, returns the caller.'

    def main(self,bot):
        if len(bot.cmdargs) == 0:
            return bot.caller_name

        user = bot.cmdargs[0]
        if user[0] == "@":
            user = user[1:]

        return user
