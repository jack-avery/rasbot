###
#   rasbot definitions module
#   raspy#0292 - raspy_on_osu
###

##
# Definitions
##

BUILTIN_COMMANDS = ['help','uptime','cmdadd','cmddel','prefix']
"""Built-in commands."""

DEFAULT_PREFIX = "r!"
"""Default prefix for a new channel config."""

DEFAULT_AUTHFILE = "_AUTH"
"""Default authfile to use if none is provided as a commandline arg."""

MODONLY_ARG = "-modonly"
"""Mod-only option for command creation"""

PATH_TO_STREAMCOMPANION_NP_FILE = "C:/Program Files (x86)/StreamCompanion/Files/np.txt"
"""Path to osu!StreamCompanion NP info file, for use in `methods/np.py`."""

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
