###
#   rasbot errors module
#   raspy#0292 - raspy_on_osu
###

# Command-related errors
class CommandStillOnCooldownError(Exception):pass
class CommandIsBuiltInError(Exception):pass
class CommandDoesNotExistError(Exception):pass
class CommandIsModOnlyError(Exception):pass
class CommandMustHavePositiveCooldownError(Exception):pass

# Method-related errors
class MethodDoesNotExistError(Exception):pass
