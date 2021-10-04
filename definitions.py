###
#   rasbot definitions module
#   raspy#0292 - raspy_on_osu
###

##
# Definitions
##

# Default prefix for a new channel config
DEFAULT_PREFIX = "r!"

# Default authfile to use if none is provided as a clarg
DEFAULT_AUTHFILE = "_AUTH"

# Mod-only option for command creation
MODONLY_ARG = "-modonly"

# Path to osu!StreamCompanion NP info file, for use in methods/np.py
PATH_TO_STREAMCOMPANION_NP_FILE = "C:/Program Files (x86)/StreamCompanion/Files/np.txt"

##
# Errors
##

# Command-related errors
class CommandStillOnCooldownError(Exception):pass
class CommandIsBuiltInError(Exception):pass
class CommandDoesNotExistError(Exception):pass
class CommandIsModOnlyError(Exception):pass
class CommandMustHavePositiveCooldownError(Exception):pass

# Method-related errors
class MethodDoesNotExistError(Exception):pass
