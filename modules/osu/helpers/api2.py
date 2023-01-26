from src.config import BASE_CONFIG_PATH, read, write

DEFAULT_CONFIG = {
    "client_id": "",
    "client_secret": "",
}

CALLBACK = ('localhost', 27274)
"""Callback URL set in the application MUST be `http://localhost:27274`."""


class Singleton:
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Singleton, cls).__new__(cls)
        return cls.instance


class OsuAPIv2Helper(Singleton):
    def __init__(self, id: int):
        """Create a new `OsuAPIv2Helper`.

        :param id: The UID of the Twitch Channel to save/load APIv2 Config for.
        """
        self._cfgpath = f"{BASE_CONFIG_PATH}/{id}/modules/osu/helpers/api2.txt"
        read(self._cfgpath, DEFAULT_CONFIG)
