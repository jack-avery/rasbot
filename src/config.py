import json
import os

DEFAULT_CHANNEL = {
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

DEFAULT_GLOBAL = {
    "always_debug": False,
    "default_authfile": "config/auth.txt",
    "release_branch": "main",
    "channels": [],
}


def read_global() -> dict:
    """Reads the global config file.
    """
    # verify config folder exists
    if not os.path.exists("config"):
        os.mkdir("config")

    return read("config/rasbot.txt", DEFAULT_GLOBAL)


def read_channel(path: str) -> dict:
    """Reads the channel config file from `path`.

    :param path: The path to the config.
    """
    return read(path, DEFAULT_CHANNEL)


def read(path: str, default: dict) -> dict:
    """Read a file and return the contained json.

    :param cfg: The path to the file.

    :param default: Default to write to file if the path does not exist.
    """
    # Attempt to read config
    try:
        with open(path, 'r') as cfgfile:
            config = json.loads(cfgfile.read())
            return config

    # If the json fails to load...
    except json.decoder.JSONDecodeError as err:
        print(f"\nFailed to read config file at path {path}:")
        print(f"{err.msg} (line {err.lineno}, column {err.colno})\n")
        print("The file likely has a formatting error somewhere.")
        input("Find and fix the error, then re-launch rasbot.")

    # If no config file is found, write the default,
    # and return a basic config dict.
    except FileNotFoundError:
        with open(path, 'w') as cfgfile:
            return write(path, default)


def write_channel(bot):
    """Generates then writes the config file for the given TwitchBot.

    :param bot: The TwitchBot to write the config for.
    """
    bot.log_debug("config", f"writing {bot.cfgpath}")

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
    write(bot.cfgpath, data)


def write(path: str, cfg: dict):
    """Write `cfg` to `path` and return `cfg`.
    """
    with open(path, 'w') as file:
        file.write(json.dumps(cfg, indent=4))

    return cfg
