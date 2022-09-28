from definitions import DEFAULT_CONFIG
import json


def read(cfgid) -> dict:
    """Reads the config file for a given channel ID.

    :param cfgid: The path to the channels' config.
    """
    # Attempt to read config
    try:
        with open(cfgid, 'r') as cfg:
            config = json.loads(cfg.read())

    # If no config file is found, write the default,
    # and return a basic config dict.
    except FileNotFoundError:
        create_default(cfgid)
        config = DEFAULT_CONFIG

    return config


def write(bot):
    """Writes the config file for the given TwitchBot.

    :param bot: The TwitchBot to write the config for.
    """
    bot.log_debug(f"Writing configuration to {bot.cfgid}")

    # Append prefix to lines
    data = {
        'meta': {
            'prefix': bot.prefix
        },
        'commands': {},
        'modules': [],
    }

    # Adding commands
    for name, command in bot.commands.commands.items():
        data['commands'][name] = {
            'cooldown': command.cooldown,
            'requires_mod': command.requires_mod,
            'hidden': command.hidden,
            'response': command.response,
        }

    # Writing config
    with open(bot.cfgid, 'w') as cfg:
        cfg.write(json.dumps(data, indent=4))


def create_default(cfgid):
    """Creates the default config for a new user.

    :param cfgid: The path to the channel's config.
    """
    with open(cfgid, 'w') as cfg:
        cfg.write(json.dumps(DEFAULT_CONFIG, indent=4))
