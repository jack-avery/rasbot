###
#   rasbot errors module
#   raspy#0292 - raspy_on_osu
###

class CommandStillOnCooldownError(Exception):
    pass

class CommandIsBuiltInError(Exception):
    pass

class CommandIsModOnlyError(Exception):
    pass