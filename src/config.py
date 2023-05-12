import json
import logging
import os

log = logging.getLogger("rasbot")

BASE_CONFIG_PATH = "userdata"
GLOBAL_CONFIG_FILE = "rasbot.txt"

DEFAULT_CHANNEL = {
    "meta": {"prefix": "r!"},
    "commands": {
        "help": {
            "cooldown": 10,
            "requires_mod": False,
            "hidden": False,
            "response": "@%caller% > %help%",
        },
        "uptime": {
            "cooldown": 10,
            "requires_mod": False,
            "hidden": False,
            "response": "@%caller% > %uptime%",
        },
        "cmd": {
            "cooldown": 0,
            "requires_mod": True,
            "hidden": False,
            "response": "@%caller% > %cmd%",
        },
        "prefix": {
            "cooldown": 0,
            "requires_mod": True,
            "hidden": False,
            "response": "@%caller% > %prefix%",
        },
        "admin": {
            "cooldown": 0,
            "requires_mod": True,
            "hidden": True,
            "response": "@%caller% > %admin%",
        },
    },
    "modules": [],
}
"""Default channel config."""

DEFAULT_GLOBAL = {
    "always_debug": False,
    "default_authfile": "auth.txt",
    "release_branch": "main",
    "enable_telemetry": False,
}

read_global = lambda: ConfigHandler(GLOBAL_CONFIG_FILE, DEFAULT_GLOBAL).read()


class ConfigHandler:
    def __init__(self, path: str, default: dict):
        self._default = default

        if not path.startswith(BASE_CONFIG_PATH):
            path = f"{BASE_CONFIG_PATH}/{path}"
        self._path = path

        self.verify_folder_exists()

    def verify_folder_exists(self):
        """Create `self._path` if it does not exist."""
        folder_list = self._path.split("/")
        folders = []
        for i, name in enumerate(folder_list):
            # assume file and end of path reached, break
            if "." in name:
                break

            folder = f"{'/'.join(folder_list[:i+1])}"
            folders.append(folder)

        # Verify config folder exists
        for folder in folders:
            if not os.path.exists(folder):
                log.debug(f"creating non-existent searched folder {folder}")
                os.mkdir(folder)

    def read(self) -> dict:
        """Read a file and return the contained json.
        Creates containing folders if they don't exist.

        :return: The resulting config
        """
        # Attempt to read config
        try:
            with open(self._path, "r") as cfgfile:
                data = json.loads(cfgfile.read())

                if not data:
                    raise FileNotFoundError

                # add missing keys
                if self._default:
                    for key in self._default:
                        if key in data:
                            continue
                        log.warn(
                            f"{self._path} - missing default key '{key}', saving default '{self._default[key]}'"
                        )
                        data[key] = self._default[key]
                        self.write(data)

                return data

        # If the json fails to load...
        except json.decoder.JSONDecodeError as err:
            log.error(f"\nFailed to read config file at path {self._path}:")
            log.error(f"{err.msg} (line {err.lineno}, column {err.colno})\n")
            log.error("The file likely has a formatting error somewhere.")
            log.error("Find and fix the error, then re-launch rasbot.")

        # If no config file is found, write the default,
        # and return a basic config dict.
        except FileNotFoundError:
            if self._default:
                log.debug(f"{self._path} not found, writing default;")
                return self.write(self._default)

            # No default; return empty dict to prevent errors
            return dict()

    def write(self, cfg: dict):
        """Write `cfg` to `self._path` and return `cfg`.

        :param cfg: The `dict` object to convert to json and write
        """
        with open(self._path, "w") as cfgfile:
            log.debug(f"writing {self._path}")
            cfgfile.write(json.dumps(cfg, indent=4, skipkeys=True))

        return cfg
