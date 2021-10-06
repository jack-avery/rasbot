###
#   rasbot config management module
#   raspy#0292 - raspy_on_osu
###

from definitions import BUILTIN_COMMANDS, DEFAULT_PREFIX

def read(cfgid) -> dict:
    """Reads the config file for a given channel ID.

    :param cfgid: The path to the channels' config.
    """
    # Attempt to read config
    try:
        with open(cfgid,'r') as cfg:
            lines = cfg.readlines()
    
    # If no config file is found, write the default,
    # and return a basic config dict.
    except FileNotFoundError:
        create_default(cfgid)
        config = {
            "prefix": DEFAULT_PREFIX,
            "commands": []
        }
        return config

    # Removing newlines
    for i,line in enumerate(lines):
        lines[i] = line[:-1]

    # Append prefix to dict
    config = dict()
    config["prefix"] = lines.pop(0)

    # Create list of commands and append to dict
    commands = list()
    for line in lines:
        commands.append(line.split(" "))
    config["commands"] = commands

    return config

def write(bot):
    """Writes the config file for the given TwitchBot.

    :param bot: The TwitchBot to write the config for.
    """
    # Append prefix to lines
    lines = list()
    lines.append(bot.prefix)

    # Adding commands
    for name,command in bot.commands.commands.items():
        # The builtins are already added each init, don't add them to the config.
        if name not in BUILTIN_COMMANDS:
            lines.append(f"{name} {command.cooldown} {command.requires_mod} {command.response}")

    # Adding newlines
    for i,line in enumerate(lines):
        lines[i] = line+"\n"

    # Writing config
    with open(bot.cfgid,'w') as cfg:
        cfg.writelines(lines)

def create_default(cfgid):
    """Creates the default config for a new user.

    :param cfgid: The path to the channel's config.
    """
    with open(cfgid,'w') as cfg:
        cfg.writelines([f'{DEFAULT_PREFIX}\n'])
