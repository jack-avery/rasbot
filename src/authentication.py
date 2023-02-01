import requests

from src.config import read, write

AUTH_SKELETON = {
    "user_id": None,
    "client_id": None,
    "client_secret": None,
    "irc_oauth": None,
    "oauth": None,
}


class Authentication:
    file: str
    """The path to the file containing the given Twitch authentication"""
    user_id: str
    """The Twitch username of the application owner."""
    client_id: str
    """The application client ID."""
    client_secret: str
    """The application client secret."""
    irc_oauth: str
    """Twitch OAuth token for IRC connections."""
    oauth: str
    """Twitch OAuth token for API requests."""

    def __init__(self, file: str):
        """Create a new authentication identity.

        :param file: The file to pull auth from
        """
        self.file = file

        auth = read(self.file, AUTH_SKELETON)

        try:
            self.user_id = auth['user_id']
            self.client_id = auth['client_id']
            self.client_secret = auth['client_secret']
            self.irc_oauth = auth['irc_oauth']
            self.oauth = auth['oauth']

        except KeyError as key:
            raise KeyError(key)

    def get_headers(self) -> dict:
        """Returns headers for Twitch API calls.
        For use in some queries, e.g. the `uptime` module.

        :return: A dictionary for use with the `headers` param of `requests.get()`
        """
        return {'Client-ID': self.client_id,
                'Authorization': f'Bearer {self.oauth}',
                'Accept': 'application/vnd.twitchtv.v5+json'}

    def refresh_oauth(self):
        """Attempts to automatically refresh the OAuth for the given user, then save to file.
        """
        # Request new oauth token from Twitch
        r = requests.post(f"https://id.twitch.tv/oauth2/token"
                          + f'?client_id={self.client_id}'
                          + f'&client_secret={self.client_secret}'
                          + '&grant_type=client_credentials').json()

        # Set oauth and write the file
        try:
            self.oauth = r['access_token']

            data = {
                "user_id": self.user_id,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "irc_oauth": self.irc_oauth,
                "oauth": self.oauth,
            }

            write(self.file, data)

        # If it can't find the key...
        except KeyError:
            raise AuthenticationDeniedError("got error response status"
                                            + f"{r['status']}, message '{r['message']}'")


class AuthenticationDeniedError(Exception):
    pass
