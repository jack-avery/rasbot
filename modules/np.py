# 'np' code for a Now Playing function. To get this to work:
# Create an output pattern in osu!StreamCompanion with the info you want (default is for a pattern called np)
# Replace the path below with the path to the file (below is default, might not need to change it)
# Create a command using cmdadd with &np& as the response.

from commands import BaseModule

PATH_TO_STREAMCOMPANION_NP_FILE = "C:/Program Files (x86)/StreamCompanion/Files/np.txt"
"""Path to osu!StreamCompanion NP info file, for use in `methods/np.py`."""


class Module(BaseModule):
    helpmsg = 'Prints "Now Playing" information from a configured file. Usage: np'

    def main(self):
        try:
            with open(PATH_TO_STREAMCOMPANION_NP_FILE, 'r') as file:
                return f'{file.readlines()[0]}'
        except (FileNotFoundError, IndexError):
            return 'No NP data found.'
