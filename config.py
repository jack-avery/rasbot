###
#   rasbot config management module
#   raspy#0292 - raspy_on_osu
###

def read(id:int) -> dict:
    """Reads the config file for a given channel ID.

    :param id: The channel to read the config for.
    """
    # Attempt to read config
    try:
        with open("_"+str(id),'r') as cfg:
            lines = cfg.readlines()
    
    # If no config file is found, write the default,
    # and return a basic config dict.
    except FileNotFoundError:
        create_default(id)
        config = {
            "prefix": "r!",
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
        if name not in bot.commands.builtins:
            lines.append(f"{name} {command.cooldown} {command.requires_mod} {command.response}")

    # Adding newlines
    for i,line in enumerate(lines):
        lines[i] = line+"\n"

    # Writing config
    with open("_"+str(bot.channel_id),'w') as cfg:
        cfg.writelines(lines)

def create_default(id:int):
    """Creates the default config for a new user.

    :param id: The channel to write the config for.
    """
    with open("_"+str(id),'w') as cfg:
        cfg.writelines(['r!\n'])