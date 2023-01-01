import requests

from src.definitions import AuthenticationDeniedError
from src.config import read, write


class Authentication:
    auth: dict
    """The JSON object representing the given Twitch authentication"""

    file: str
    """The path to the file containing the given Twitch authentication"""

    def __init__(self, file: str):
        """Create a new authentication identity.

        :param file: The file to pull auth from
        """
        self.file = file
        self.read_authfile()

    def read_authfile(self):
        """Reads from the authfile set by self.file.

        Assigns the read values to this `Authentication` objects' `auth` field.
        """
        self.auth = read(self.file)

    def write_authfile(self):
        """Writes `self.auth` to `self.file`.
        """
        write(self.file, self.auth)

    def get(self, key: str) -> str:
        """Return the item with the given `key`.

        :param key: The key to get the value of
        :return: The value of `self.auth[key]`
        """
        return self.auth[key]

    def get_headers(self) -> dict:
        """Returns headers for Twitch API calls.
        For use in some queries, e.g. the `uptime` module.

        :return: A dictionary for use with the `headers` param of `requests.get()`
        """
        return {'Client-ID': self.auth["client_id"],
                'Authorization': f'Bearer {self.auth["oauth"]}',
                'Accept': 'application/vnd.twitchtv.v5+json'}

    def refresh_oauth(self):
        """Refreshes this authfiles' OAuth key.
        """
        # Request new oauth token from Twitch
        r = requests.post(f"https://id.twitch.tv/oauth2/token"
                          + f'?client_id={self.auth["client_id"]}'
                          + f'&client_secret={self.auth["client_secret"]}'
                          + '&grant_type=client_credentials').json()

        # Set oauth and write the file
        try:
            self.auth['oauth'] = r['access_token']
            self.write_authfile()

        # If it can't find the key...
        except KeyError:
            raise AuthenticationDeniedError("got error response status"
                                            + f"{r['status']}, message '{r['message']}'")
