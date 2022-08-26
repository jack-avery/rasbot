# This is a test method. Feel free to use it as a template.

from commands import BaseModule
import threading


class Module(BaseModule):
    def __init__(self):
        # Make sure you call BaseModule init if overriding!
        BaseModule.__init__(self)
        self.count = 0
        timer = RepeatTimer(1, self.tick)
        timer.start()

    def tick(self):
        self.count += 1

    # Show the amount of seconds since the bot started
    def main(self, bot):
        return self.count

# See https://stackoverflow.com/a/48741004


class RepeatTimer(threading.Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)
