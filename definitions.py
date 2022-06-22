###
#   rasbot definitions module
#   raspy#0292 - raspy_on_osu
###

##
# Definitions
##

BUILTIN_COMMANDS = ['help','uptime','cmdadd','cmddel','prefix','debugechofull','debugmsgcount']
"""Built-in commands."""

BUILTIN_MODULES = ['authentication','bot','commands','config','definitions','refresh_oauth','run','update','setup']
"""Built-in modules. Used for the autoupdate function."""

VALID_COMMAND_REGEX = r'[\w+]+'
"""Regex to compare given command names to for validation."""

MODULE_MENTION_REGEX = r'&(\w+)&'
"""Regex to compare command responses to for finding any mentioned modules."""

DEFAULT_PREFIX = "r!"
"""Default prefix for a new channel config."""

DEFAULT_AUTHFILE = "_AUTH.txt"
"""Default authfile to use if none is provided as a commandline arg."""

MODONLY_ARG = "-modonly"
"""Mod-only option for command creation"""

HIDDEN_ARG = "-hidden"
"""Hidden option for command creation"""

PATH_TO_STREAMCOMPANION_NP_FILE = "C:/Program Files (x86)/StreamCompanion/Files/np.txt"
"""Path to osu!StreamCompanion NP info file, for use in `methods/np.py`."""

##
# Errors
##

# Authentication-related errors
class AuthenticationDeniedError(Exception):pass

# Command-related errors
class CommandStillOnCooldownError(Exception):pass
class CommandIsBuiltInError(Exception):pass
class CommandDoesNotExistError(Exception):pass
class CommandIsModOnlyError(Exception):pass
class CommandMustHavePositiveCooldownError(Exception):pass
class CommandGivenInvalidNameError(Exception):pass

# Module-related errors
class ModuleImportError(Exception):pass
