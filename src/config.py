import json
import os

BASE_CONFIG_PATH = "userdata"
GLOBAL_CONFIG_FILE = "rasbot.txt"

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
        "admin": {
            "cooldown": 0,
            "requires_mod": True,
            "hidden": True,
            "response": "&admin&"
        },
    },
    "modules": []
}
"""Default channel config."""

DEFAULT_GLOBAL = {
    "always_debug": False,
    "default_authfile": "auth.txt",
    "release_branch": "main",
}


def verify_folder_exists(path: str):
    """Create `path` if it does not exist."""
    folder_list = path.split("/")
    folders = []
    for i, name in enumerate(folder_list):
        # assume file and end of path reached, break
        if '.' in name:
            break

        folder = f"{'/'.join(folder_list[:i+1])}"
        folders.append(folder)

    # Verify config folder exists
    for folder in folders:
        if not os.path.exists(folder):
            os.mkdir(folder)


def read_global() -> dict:
    """Reads the global config file.
    """
    return read(GLOBAL_CONFIG_FILE, DEFAULT_GLOBAL)


def read_channel(path: str) -> dict:
    """Reads the channel config file from `path`.

    :param path: The path to the config.
    """
    return read(path, DEFAULT_CHANNEL)


def read(path: str, default: dict) -> dict:
    """Read a file and return the contained json.
    Creates containing folders if they don't exist.

    :param cfg: The path to the file.
    :param default: Default to write to file if the path does not exist.
    :return: The resulting config
    """
    if not path.startswith(BASE_CONFIG_PATH):
        path = f"{BASE_CONFIG_PATH}/{path}"
    verify_folder_exists(path)

    # Attempt to read config
    try:
        with open(path, 'r') as cfgfile:
            return json.loads(cfgfile.read())

    # If the json fails to load...
    except json.decoder.JSONDecodeError as err:
        print(f"\nFailed to read config file at path {path}:")
        print(f"{err.msg} (line {err.lineno}, column {err.colno})\n")
        print("The file likely has a formatting error somewhere.")
        input("Find and fix the error, then re-launch rasbot.")

    # If no config file is found, write the default,
    # and return a basic config dict.
    except FileNotFoundError:
        if default:
            return write(path, default)


def write(path: str, cfg: dict):
    """Write `cfg` to `path` and return `cfg`.

    :param path: The path to write to
    :param cfg: The `dict` object to convert to json and write
    """
    if not path.startswith(BASE_CONFIG_PATH):
        path = f"{BASE_CONFIG_PATH}/{path}"
    verify_folder_exists(path)

    with open(path, 'w') as cfgfile:
        cfgfile.write(json.dumps(cfg, indent=4, skipkeys=True))

    return cfg
