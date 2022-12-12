##
# Definitions used in multiple files go here.
##

VALID_COMMAND_REGEX = r'[a-z0-9_]+'
"""Regex to compare given command names to for validation."""

MODULE_MENTION_REGEX = r'&([\/a-z0-9_]+)&'
"""Regex to compare command responses to for finding any mentioned modules."""

NO_MESSAGE_SIGNAL = "&NOMSG&"
"""Signal for a module to return for there to be no message sent no matter what."""

##
# Errors
##

# Authentication-related errors


class AuthenticationDeniedError(Exception):
    pass

# Command-related errors


class CommandStillOnCooldownError(Exception):
    pass


class CommandDoesNotExistError(Exception):
    pass


class CommandIsModOnlyError(Exception):
    pass


class CommandMustHavePositiveCooldownError(Exception):
    pass


class CommandGivenInvalidNameError(Exception):
    pass
