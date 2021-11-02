import importlib.util
import re
import time
from definitions import BUILTIN_COMMANDS,\
    VALID_COMMAND_REGEX,\
    CommandDoesNotExistError, CommandGivenInvalidNameError,\
    CommandIsBuiltInError,\
    CommandIsModOnlyError,\
    CommandMustHavePositiveCooldownError,\
    CommandStillOnCooldownError

###
#   rasbot commands module
#   raspy#0292 - raspy_on_osu
###

class Command:
    def __init__(self, name:str, cooldown:int = 5, response:str='', requires_mod:bool=False, hidden:bool=False):
        '''Creates a new command.

        :param name: The name of the command.

        :param cooldown: The cooldown of the command in seconds.

        :param response: The text response of the command. Encapsulate custom commands in &&.

        :param requires_mod: Whether the command requires the user to be a mod.

        :param hidden: Whether the command should be hidden from help.
        '''
        self.name = name.lower()
        self.cooldown = int(cooldown)
        self.response = response
        self.requires_mod = bool(requires_mod)
        self.hidden = bool(hidden)

        self.__last_used = 0

    def run(self, bot):
        """Code to be run when this command is called from chat.
        
        Runs all && codes found in the command and returns the result.
        """
        # Make sure the command is not on cooldown before doing anything
        if not time.time()-self.__last_used > self.cooldown:
            raise CommandStillOnCooldownError(f"command {self.name} called while still on cooldown")
        
        # Do not allow non-moderators to use mod-only commands
        if not bot.caller_ismod and self.requires_mod:
            raise CommandIsModOnlyError(f"mod-only command {self.name} called by non-mod {bot.caller_name}")

        # Apply any methods encased in &&
        returned_response = self.response
        for method_name, method in methods.items():
            if f'&{method_name}&' in returned_response:
                returned_response = returned_response.replace(
                                                              f'&{method_name}&',
                                                              str(method.main(bot))
                                                             )

        # Update the last usage time and return the response
        self.__last_used = time.time()
        
        return returned_response

def command_modify(name:str, cooldown:int = 5, response:str = '', requires_mod:bool = False, hidden:bool = False):
    '''Creates a new command (or modifies an existing one),
    and appends it to the commands dict.

    :param name: The name of the command.

    :param cooldown: The cooldown of the command in seconds.

    :param response: The text response of the command. Encapsulate custom commands in &&.
    '''
    # You cannot modify built-in commands
    if name in BUILTIN_COMMANDS:
        raise CommandIsBuiltInError(f"attempt made to modify builtin command {name}")

    # Command cannot have a negative cooldown
    if int(cooldown) < 0:
        raise CommandMustHavePositiveCooldownError(f"command {name} provided invalid cooldown length {cooldown}")

    # Command must match the regex defined by VALID_COMMAND_REGEX
    if not command_re.match(name):
        raise CommandGivenInvalidNameError(f"command provided invalid name {name}")

    commands[name] = Command(name,cooldown,response,requires_mod,hidden)

def command_del(name:str):
    '''Deletes a command and removes it from the dict.

    :param name: The name of the command.
    '''
    # You cannot modify built-ins
    if name in BUILTIN_COMMANDS:
        raise CommandIsBuiltInError(f"attempt made to modify builtin command {name}")
    
    # Command must match the regex defined by VALID_COMMAND_REGEX
    if not command_re.match(name):
        raise CommandGivenInvalidNameError(f"command provided invalid name {name}")

    try:
        del(commands[name])
    except KeyError:
        raise CommandDoesNotExistError(f'command {name} does not exist')

class BaseMethod:
    """The base class for a Method, custom or not.

    Facilitates defaults for a Method so as to prevent errors.
    """

    def main(self, bot):
        """Code to be run for the methods' && code.
        """
        pass

    def help(self):
        """The help message when used with the `help` method.
        """
        return f'No help message available for method.'

    # Default per-message function.
    def per_message(self, bot):
        """Code to be run for every message received.

        By default, does nothing.
        """
        pass

def method_add(name:str):
    '''Creates a new method and appends it to the methods dict.

    :param name: The name of the method. File must be visible in the methods folder.
    '''
    spec = importlib.util.spec_from_file_location(f"{name}",f"methods/{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    methods[name] = module.Method()

def do_per_message_methods(bot):
    """Runs the per_message() of every Method imported from `./methods`.
    """
    for module in methods.values():
        module.per_message(bot)

# Do not modify this! These are built-in commands, initialized on module import.
commands = dict()
methods = dict()
command_re = re.compile(VALID_COMMAND_REGEX)
commands["help"] = Command("help",5,"&help&")
commands["uptime"] = Command("uptime",5,"&uptime&")
commands["cmdadd"] = Command("cmdadd",0,"&cmdadd&",True)
commands["cmddel"] = Command("cmddel",0,"&cmddel&",True)
commands["prefix"] = Command("prefix",0,"&prefix&",True)
commands["debugechofull"] = Command("debugechofull",0,"&debugechofull&",True,True)
commands["debugmsgcount"] = Command("debugmsgcount",0,"&debugmsgcount&",True,True)
