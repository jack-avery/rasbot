# 'np' code for a Now Playing function. To get this to work:
# Create an output pattern in osu!StreamCompanion with the info you want
# Point the path in definitions.py to the file
# Create a command using cmdadd with &np& as the response.

from commands import BaseMethod
from definitions import PATH_TO_STREAMCOMPANION_NP_FILE

class Method(BaseMethod):
    def main(self,bot):
        try:
            with open(PATH_TO_STREAMCOMPANION_NP_FILE,'r') as file:
                return f'{file.readlines()[0]}'
        except (FileNotFoundError, IndexError):
            return 'No NP data found.'

    def help(self):
        return 'Prints "Now Playing" information from a configured file. Usage: np'
