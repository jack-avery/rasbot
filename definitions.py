##
# Definitions used in multiple files go here.
##

VALID_COMMAND_REGEX = r'[a-z0-9_]+'
"""Regex to compare given command names to for validation."""

MODULE_MENTION_REGEX = r'&([\/a-z0-9_]+)&'
"""Regex to compare command responses to for finding any mentioned modules."""

DEFAULT_CONFIG = {
    "meta": {
        "prefix": "r!"
    },
    "commands": {
        "help": {
            "cooldown": 10,
            "requires_mod": False,
            "hidden": False,
            "response": "@&caller& > &help&"
        },
        "uptime": {
            "cooldown": 10,
            "requires_mod": False,
            "hidden": False,
            "response": "@&caller& > &uptime&"
        },
        "cmdadd": {
            "cooldown": 0,
            "requires_mod": True,
            "hidden": False,
            "response": "@&caller& > &cmdadd&"
        },
        "cmddel": {
            "cooldown": 0,
            "requires_mod": True,
            "hidden": False,
            "response": "@&caller& > &cmddel&"
        },
        "prefix": {
            "cooldown": 0,
            "requires_mod": True,
            "hidden": False,
            "response": "@&caller& > &prefix&"
        },
    },
    "modules": []
}
"""Default channel config."""

DEFAULT_AUTHFILE = "_AUTH.txt"
"""Default authfile to use if none is provided as a commandline arg."""

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
