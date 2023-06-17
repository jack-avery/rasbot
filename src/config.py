import logging
import os
import yaml

log = logging.getLogger("rasbot")

BASE_CONFIG_PATH = "userdata"
GLOBAL_CONFIG_FILE = "rasbot.txt"

DEFAULT_CHANNEL = {
    "commands": {
        "help": {
            "cooldown": 10,
            "privilege": 0,
            "hidden": False,
            "response": "@%caller% > %help%",
        },
        "uptime": {
            "cooldown": 10,
            "privilege": 0,
            "hidden": False,
            "response": "@%caller% > %uptime%",
        },
        "cmd": {
            "cooldown": 0,
            "privilege": 0,
            "hidden": False,
            "response": "@%caller% > %cmd%",
        },
        "prefix": {
            "cooldown": 0,
            "privilege": 3,
            "hidden": False,
            "response": "@%caller% > %prefix%",
        },
        "admin": {
            "cooldown": 0,
            "privilege": 3,
            "hidden": True,
            "response": "@%caller% > %admin%",
        },
    },
    "meta": {"prefix": "r!"},
    "modules": [],
}
"""Default channel config."""

DEFAULT_GLOBAL = {
    "always_debug": False,
    "default_authfile": "auth.txt",
    "release_branch": "main",
    "telemetry": -1,
}

read_global = lambda: ConfigHandler(GLOBAL_CONFIG_FILE, DEFAULT_GLOBAL).read()


class ConfigHandler:
    def __init__(self, path: str, default: dict):
        self._default_config = default

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
        try:
            with open(self._path, "r") as cfgfile:
                file_data = yaml.safe_load(cfgfile.read())

                if not file_data:
                    raise FileNotFoundError

                if self._default_config:
                    for key in self._default_config:
                        if key in file_data:
                            continue
                        log.warn(
                            f"{self._path} - missing default key '{key}', saving default '{self._default_config[key]}'"
                        )
                        file_data[key] = self._default_config[key]

                return self.write(file_data)

        except yaml.MarkedYAMLError as err:
            log.error(f"Failed to read config file at path {self._path}:")
            if hasattr(err, "problem_mark"):
                if err.context:
                    log.error(f"\n{err.problem_mark}\n{err.problem} {err.context}")
                else:
                    log.error(f"\n{err.problem_mark}\n{err.problem}")
                log.error(
                    "the error may be at or near this mark depending on the issue\n"
                )
            else:
                log.error("Unknown error?? Contact raspy..\n")

            log.critical("rasbot will refuse to start when trying to load this!!")

            if self._default_config:
                print(
                    "\nThe config does have a default, but anything saved will be deleted.\n"
                    + "You can also optionally attempt to fix the formatting given the error above, then restart rasbot."
                )
                overwrite_with_default = (
                    input(
                        "Would you like to overwrite the existing file with the default? (y/n) > "
                    ).lower()
                    == "y"
                )
                if overwrite_with_default:
                    self.write(self._default_config)
                    return self._default_config

        except FileNotFoundError:
            if not self._default_config:
                return dict()

            log.debug(f"{self._path} not found, writing default;")
            return self.write(self._default_config)

    def write(self, cfg: dict):
        """Write `cfg` to `self._path` and return `cfg`.

        :param cfg: The `dict` object to convert to json and write
        """
        with open(self._path, "w") as cfgfile:
            log.debug(f"writing {self._path}")
            cfgfile.write(yaml.safe_dump(cfg, indent=4))

        return cfg
