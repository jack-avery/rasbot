# This is a sample module. Feel free to fiddle with this to learn how rasbot modules work.
#
# It's important to note that modules are only imported (and have on_pubmsg run) if they are referenced in a command,
# or if they are added to the "modules" array in your config as a string,
# e.g. "modules": ["sample"]
#
# You can test out this module by adding it in a command as %sample%
# e.g. "r!cmd add sample %sample%"

from src.plugins import BaseModule
from src.definitions import Message


class Module(BaseModule):
    # You can give your module a special help message when used with !help like this:
    helpmsg = "Sample module! Usage: sample <message?>"

    # You can save parameters for your module using a config.
    # Adding a default will let users know what will be stored:
    default_config = {"savedmessage": ""}

    # Set "consumes" to how many arguments your module intends to consume for more predictable interactions with other modules.
    # You can set it to a negative value to consume ALL (remaining) arguments.
    consumes = -1

    def __init__(self, bot, name):
        # Make sure you call BaseModule init if overriding __init__!
        BaseModule.__init__(self, bot, name)
        self.count = 0

    # This runs if the module is part of a command which gets called.
    def main(self, message: Message):
        # Use self.cfg_get(key) to get items from the module config.
        last_time = self.cfg_get("savedmessage")

        # Use self.get_args(message) to consume the designated amount of arguments and continue.
        args = self.get_args(message)

        # You can save things using self.cfg_set(key, value):
        self.cfg_set("savedmessage", " ".join(args))

        # You can get the author's name, UID, and mod status like so!
        return (
            f"@{message.author.name} ({message.author.uid}, mod: {message.author.is_mod}), "
            + f"{self.count} messages have been sent so far, "
            + f"and last time you also said '{last_time}'."
        )

    # This runs on all messages regardless of whether the command is called.
    def on_pubmsg(self, message: Message):
        self.count += 1
