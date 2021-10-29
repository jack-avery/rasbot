# This is a test function. Feel free to use it as a template.

from commands import BaseMethod

class Method(BaseMethod):
    def __init__(self):
        self.count = 0

    def main(self,bot):
        self.increase_count()

        return f"{self.count}, {' '.join(bot.cmdargs)}"

    def increase_count(self):
        self.count+=1