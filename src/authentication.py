import json
import requests

from src.definitions import AuthenticationDeniedError


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
        # Attempting to read the auth file
        auth = False
        try:
            with open(self.file, 'r') as authfile:
                auth = json.loads(authfile.read())

        # If not found, do nothing. Assume set-up
        except FileNotFoundError:
            self.auth = {}
            return

            # Verify the auth has everything it needs...
        if [k for k in auth.keys()] != ['user_id', 'client_id', 'client_secret', 'irc_oauth', 'oauth']:
            print("Your authfile is missing crucial elements.")
            print("You may need to re-run setup.py.")
            input("rasbot cannot continue, exiting.")
            exit()

        self.auth = auth

    def write_authfile(self):
        """Writes `self.auth` to `self.file`.
        """
        # Writing the auth file
        with open(self.file, 'w') as authfile:
            authfile.write(json.dumps(self.auth, indent=4))

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
