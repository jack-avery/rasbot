# This is a sample module. Feel free to fiddle with this to learn how rasbot modules work.
# It's important to note that modules are only imported (and have on_pubmsg run) if they are referenced in a command.
# You can test out this module by adding it in a command as &sample&
# e.g. "r!cmdadd sample &sample&"

from commands import BaseModule


class Module(BaseModule):
    def __init__(self):
        # Make sure you call BaseModule init if overriding __init__!
        BaseModule.__init__(self)

        self.count = 0

    # This runs if the module is part of a command which gets called.
    def main(self, bot):
        return f"Sample! {self.count} messages have been sent so far."

    # This runs on all messages regardless of whether the command is called.
    def on_pubmsg(self, bot):
        self.count += 1