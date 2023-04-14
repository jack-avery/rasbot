import logging
from requests import get, post
import http.server
import time
import webbrowser

from src.config import BASE_CONFIG_PATH, read, write
from src.definitions import Singleton

logger = logging.getLogger("rasbot")

AUTH_SKELETON = {
    "user_id": None,
    "client_id": None,
    "client_secret": None,
    "irc_oauth": None,
    "oauth": None,
}


class OAuth2Handler(Singleton):
    name = ""
    """Discriminator for this OAuth2Handler."""
    default_config = None
    """Default configuration for this OAuth2Handler."""
    callback_port = None
    """Callback port to http://localhost for auth code grabbing."""
    scopes = []
    """A list of scopes that are used by the handler."""
    oauth_grant_uri = ""
    """Base URL of the website to get the user authorization grant from."""
    oauth_token_uri = ""
    """API endpoint to get/refresh the OAuth token at."""
    api = ""
    """Base URL of the API."""

    def __init__(self, cfgpath: int):
        """Create a new `OAuthV2Handler`.

        :param cfgpath: The path to save/load APIv2 Config for.
        """
        self.cfgpath = f"{BASE_CONFIG_PATH}/{cfgpath}"
        self.cfg = read(self.cfgpath, self.default_config)

        if "token" not in self.cfg:
            self.__get_auth()

    def __get_auth(self):
        """Opens the Application Authorization page to get the auth code, and gets the initial token."""
        if not self.cfg["client_id"] or not self.cfg["client_secret"]:
            setup_complete = self.setup()

            if not setup_complete:
                return

        link = f"{self.oauth_grant_uri}?client_id={self.cfg['client_id']}&redirect_uri=http://localhost{f':{self.callback_port}' if self.callback_port else ''}&response_type=code&scope={' '.join(self.scopes)}"
        webbrowser.open(link, new=2)
        logger.info(
            f"See your web browser to continue setting up your '{self.name}' OAuth2."
        )

        self.__oauth_grant_listen()
        logger.info("Got the temporary code! Getting your initial OAuth token...")

        self.__get_initial_token()
        logger.info(f"Success! OAuth2 session '{self.name}' set up.")

    def __oauth_grant_listen(self):
        """Create a local HTTP server and listen for exactly one request, and return the obtained authorization code."""
        port = 80
        if self.callback_port:
            port = self.callback_port

        with http.server.HTTPServer(("localhost", port), OAuth2ListenHandler) as server:
            server.handle_request()

    def __get_initial_token(self):
        """Get the initial token for this OAuth2 session.

        :param auth_code: The auth code as gotten from the callback.
        """
        data = {
            "client_id": self.cfg["client_id"],
            "client_secret": self.cfg["client_secret"],
            "code": oauth_code,
            "grant_type": "authorization_code",
            "redirect_uri": f"http://localhost{f':{self.callback_port}' if self.callback_port else ''}",
        }
        self.__get_token(data)

    def __refresh_token(self):
        """Refresh the token using the existing OAuth tokens' refresh code."""
        if "token" not in self.cfg:
            return

        logger.debug("refreshing OAuth token")

        data = {
            "client_id": self.cfg["client_id"],
            "client_secret": self.cfg["client_secret"],
            "grant_type": "refresh_token",
            "refresh_token": self.cfg["token"]["refresh_token"],
        }
        self.__get_token(data)

    def __get_token(self, data):
        """Get a new token or refresh an existing one using `data`."""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        token = post(self.oauth_token_uri, headers=headers, json=data)

        if not token.status_code == 200:
            logger.error(f"OAuth token grab failed! ({token.json()})")
            return

        self.cfg["token"] = token.json()
        self.cfg["token"]["expiry"] = self.cfg["token"]["expires_in"] + time.time()
        write(self.cfgpath, self.cfg)

    def __request(self, method, endpoint: str, data: dict = None):
        if "token" not in self.cfg:
            return False

        if time.time() >= dict.get(self.cfg["token"], "expiry", 0):
            self.__refresh_token()

        url = self.api + endpoint

        headers = {
            "Authorization": f"{str.capitalize(self.cfg['token']['token_type'])} {self.cfg['token']['access_token']}",
            "Client-Id": self.cfg["client_id"],
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        logger.debug(url, headers)

        if data:
            response = method(url, headers=headers, json=data)
        else:
            response = method(url, headers=headers)

        logger.debug(response.json())

        if response.status_code == 200:
            return response.json()

    def _get(self, endpoint: str = None, data: dict = None):
        if data:
            return self.__request(get, endpoint, data)
        return self.__request(get, endpoint)

    def _post(self, endpoint: str = None, data: dict = None):
        return self.__request(post, endpoint, data)

    def setup(self):
        """Perform a guided setup for this OAuth2. By default just logs an error and does nothing."""
        logger.error(
            f"{self.name} - Config missing client_id and client_secret, cannot setup OAuth2."
        )
        return False


class OAuth2ListenHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        global oauth_code
        code = self.path
        code = code[code.find("=") + 1 :]

        andex = code.find("&")
        if andex == -1:
            oauth_code = code
            return

        code = code[:andex]
        oauth_code = code


oauth_code = ""
"""Global variable so that `OAuth2ListenHandler` can communicate with `OAuth2Handler.__oauth_grant_listen`..."""


class TwitchOAuth2Helper(OAuth2Handler):
    name = "twitch"
    """Discriminator for this OAuth2Handler."""
    default_config = None
    """Default configuration for this OAuth2Handler."""
    callback_port = None
    """Callback port to http://localhost for auth code grabbing."""
    scopes = ["moderator:read:chatters"]
    """A list of scopes that are used by the handler. Default is for Twitch."""
    oauth_grant_uri = "https://id.twitch.tv/oauth2/authorize"
    """Base URL of the website to get the user authorization grant from."""
    oauth_token_uri = "https://id.twitch.tv/oauth2/token"
    """API endpoint to get/refresh the OAuth token at."""
    api = "https://api.twitch.tv/helix"
    """Base URL of the API."""

    def get_all_chatters(self, channel_id: int, user_id: int):
        """Return a list of `user_login` for all users in the current channel.

        Automatically paginates and returns all users.
        
        :param channel_id: The channel ID to get chatters for.
        :param user_id: The User ID of the current OAuth2 session user.
        """
        results = []
        query = self._get(f"/chat/chatters?broadcaster_id={channel_id}&moderator_id={user_id}&first=1000")

        # nothing there. return empty list here to prevent errors
        if len(query["data"]) == 0:
            return results

        results += [user["user_login"] for user in query["data"]]

        # paginate, if applicable
        # query["pagination"] should be empty (== False) if no more than 1000
        while query["pagination"]:
            query = self._get(f"/chat/chatters?broadcaster_id={channel_id}&moderator_id={user_id}&first=1000&after={query['pagination']['cursor']}")
            results += [user["user_login"] for user in query["data"]]
        
        return results


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
    oauth2: TwitchOAuth2Helper
    """Twitch OAuth2 helper instance."""

    def __init__(self, file: str):
        """Create a new authentication identity.

        :param file: The file to pull auth from
        """
        self.file = file

        auth = read(self.file, AUTH_SKELETON)
        self.oauth2 = TwitchOAuth2Helper(self.file)

        try:
            self.user_id = auth["user_id"]
            self.client_id = auth["client_id"]
            self.client_secret = auth["client_secret"]
            self.irc_oauth = auth["irc_oauth"]
            self.oauth = auth["oauth"]

        except KeyError as key:
            raise KeyError(key)

    def get_headers(self) -> dict:
        """Returns headers for Twitch API calls.
        For use in some queries, e.g. the `uptime` module.

        :return: A dictionary for use with the `headers` param of `requests.get()`
        """
        return {
            "Client-ID": self.client_id,
            "Authorization": f"Bearer {self.oauth}",
            "Accept": "application/vnd.twitchtv.v5+json",
        }

    def refresh_oauth(self):
        """Attempts to automatically refresh the OAuth for the given user, then save to file."""
        # Request new oauth token from Twitch
        r = post(
            f"https://id.twitch.tv/oauth2/token"
            + f"?client_id={self.client_id}"
            + f"&client_secret={self.client_secret}"
            + "&grant_type=client_credentials"
        ).json()

        # Set oauth and write the file
        try:
            self.oauth = r["access_token"]

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
            raise AuthenticationDeniedError(
                "got error response status" + f"{r['status']}, message '{r['message']}'"
            )


class AuthenticationDeniedError(Exception):
    pass
