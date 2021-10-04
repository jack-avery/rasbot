# 'np' code for a Now Playing function. To get this to work:
# Install osu!StreamCompanion in the default directory (or modify the directory below to fit your NP file).
# Create a command using cmdadd with &np& as the response.

from definitions import PATH_TO_STREAMCOMPANION_NP_FILE

def main(bot):
    try:
        with open(PATH_TO_STREAMCOMPANION_NP_FILE,'r') as file:
            return f'{file.readlines()[0]}'
    except FileNotFoundError:
        return 'No NP data found.'
