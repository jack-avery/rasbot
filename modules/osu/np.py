# 'np' code for a Now Playing function. To get this to work:
# Create an output pattern in osu!StreamCompanion with the info you want (default is for a pattern called np)
# Replace the path in the config file in `userdata/[id]/modules/osu` with the path to the file
#   (default value is default path for Windows StreamCompanion, might not need to change it)
# Create a command using cmd with %osu/np% as the response.

# TODO: refactor this to use new osu! APIv2 "Now Playing" once it drops
# will remove dependency on using StreamCompanion

from src.commands import BaseModule


class Module(BaseModule):
    helpmsg = 'Prints "Now Playing" information from a configured file. Usage: np'

    default_config = {"path": "C:/Program Files (x86)/StreamCompanion/Files/np.txt"}
    """Path to osu!StreamCompanion NP info file."""

    def main(self, message):
        try:
            with open(self.cfg_get("path"), "r") as file:
                return f"{file.readlines()[0]}"
        except (FileNotFoundError, IndexError):
            return "No NP data found."
