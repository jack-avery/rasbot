# 'np' code for a Now Playing function. To get this to work:
# Install osu!StreamCompanion in the default directory (or modify the directory below to fit your NP file).
# Create a command using cmdadd with &np& as the response.

def main(bot):
    PATH_TO_STREAMCOMPANION_NP_FILE = "C:/Program Files (x86)/StreamCompanion/Files/np.txt"

    try:
        with open(PATH_TO_STREAMCOMPANION_NP_FILE,'r') as file:
            return f'{file.readlines()[0]}'
    except:
        return f'No NP data found.'