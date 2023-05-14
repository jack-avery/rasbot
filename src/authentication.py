import logging
from requests import get, post
import socket
import time
import webbrowser

from src.config import ConfigHandler, BASE_CONFIG_PATH
from src.definitions import Singleton

log = logging.getLogger("rasbot")


class OAuth2Handler(Singleton):
    name = ""
    """Discriminator for this OAuth2Handler."""
    default_config = {
        "client_id": None,
        "client_secret": None,
    }
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
        self.cfg_handler = ConfigHandler(
            f"{BASE_CONFIG_PATH}/{cfgpath}", self.default_config
        )
        self.cfg = self.cfg_handler.read()

        self.set_fields()

        if "token" not in self.cfg:
            self.__get_auth()
        else:
            # refresh token automatically if expired
            if self.token["expiry"] < time.time():
                self.__refresh_token()

    def set_fields(self):
        """Set the fields obtained from reading `self.cfgpath` to fields of this `OAuth2Handler`."""
        self.client_id = dict.get(self.cfg, "client_id", None)
        self.client_secret = dict.get(self.cfg, "client_secret", None)
        self.token = dict.get(self.cfg, "token", None)

    def jsonify(self) -> dict:
        """Returns a `dict` ("json-ified") with the fields of this `OAuth2Handler`."""
        return {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "token": self.token,
        }

    def __save(self):
        """Write the result of `self.jsonify()` to `self.cfgpath`."""
        self.cfg_handler.write(self.jsonify())

    def setup(self) -> None:
        """Perform a guided setup for this OAuth2. By default just logs an error and does nothing."""
        log.error(
            f"{self.name} - Config missing client_id and client_secret, cannot setup OAuth2."
        )
        return False

    def __get_auth(self):
        """Opens the Application Authorization page to get the auth code, and gets the initial token."""
        if not self.client_id or not self.client_secret:
            setup_complete = self.setup()

            if not setup_complete:
                return

        link = f"{self.oauth_grant_uri}?client_id={self.client_id}&redirect_uri=http://localhost{f':{self.callback_port}' if self.callback_port else ''}&response_type=code&scope={' '.join(self.scopes)}"
        webbrowser.open(link, new=2)

        auth_code = self.__oauth_grant_listen()
        log.info("Got the temporary code! Getting your initial OAuth token...")

        self.__get_initial_token(auth_code)
        log.info(f"Success! OAuth2 session '{self.name}' set up.")

    def __oauth_grant_listen(self) -> str:
        """Create a local HTTP server on `self.callback_port` (80 if None),
        listen for exactly one request, and return the obtained authorization code.

        :return: The OAuth grant code for use in `self.__get_initial_token()`.
        """
        port = 80
        if self.callback_port:
            port = self.callback_port

        with socket.create_server(("localhost", port)) as listener:
            conn, addr = listener.accept()
            auth_code = conn.recv(4096)

            # Strip request bytes to strictly the code
            auth_code = auth_code[auth_code.find(b"code=") + 5 :]

            # TODO: handle this better...
            andex = auth_code.find(b"&")
            if andex == -1:
                auth_code = auth_code[: auth_code.find(b" ")]
            else:
                auth_code = auth_code[:andex]

            auth_code = auth_code.decode("ASCII")

            # Inform the user in-browser
            conn.send(b"Got the temporary code! You can now close this window.")
            return auth_code

    def __get_initial_token(self, auth_code: str):
        """Get the initial token for this OAuth2 session.

        :param auth_code: The auth code as obtained from `__oauth_grant_listen()`.
        """
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": auth_code,
            "grant_type": "authorization_code",
            "redirect_uri": f"http://localhost{f':{self.callback_port}' if self.callback_port else ''}",
        }
        self.__get_token(data)

    def __refresh_token(self):
        """Refresh `self.token` using its' refresh code."""
        if not self.token:
            return

        log.debug(f"refreshing '{self.name}' OAuth token")

        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": self.token["refresh_token"],
        }
        if not self.__get_token(data):
            self.__get_auth()

    def __get_token(self, data):
        """Get a new token or refresh an existing one using `data`.

        :param data: The json data to send in the POST.
        """
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        token = post(self.oauth_token_uri, headers=headers, json=data)

        if not token.status_code == 200:
            log.error(f"'{self.name}' OAuth token grab failed! ({token.json()})")
            return False

        self.token = token.json()
        self.token["expiry"] = self.token["expires_in"] + time.time()
        self.__save()
        return True

    def __request(self, method, endpoint: str, data: dict = None):
        """Send a request to an endpoint of `self.api`.

        Returns `False` if the request was unsuccessful (e.g. 401, 404).

        :param method: `requests` method to use.
        :param endpoint: Endpoint relative to `self.api` to call.
        :param data: The json data to send in the request, frequently used in POST requests.

        :return: The json data of the response, or `False` if unsuccessful.
        """
        if not self.token:
            return False

        if time.time() >= dict.get(self.token, "expiry", 0):
            self.__refresh_token()

        url = self.api + endpoint

        headers = {
            "Authorization": f"{str.capitalize(self.token['token_type'])} {self.token['access_token']}",
            "Client-Id": self.client_id,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        log.debug(f"{method.__name__} {url}")

        if data:
            response = method(url, headers=headers, json=data)
        else:
            response = method(url, headers=headers)

        log.debug(response.status_code, response.json())

        if str(response.status_code).startswith("2"):
            return response.json()

        log.debug(response.json())
        return False

    def _get(self, endpoint: str = None, data: dict = None) -> bool | dict:
        """Send a GET request to `endpoint` of `self.api`.

        :param endpoint: Endpoint relative to `self.api` to call.
        :param data: The json data to send in the GET.

        :return: The json data of the response, or `False` if unsuccessful.
        """
        if data:
            return self.__request(get, endpoint, data)
        return self.__request(get, endpoint)

    def _post(self, endpoint: str = None, data: dict = None) -> bool | dict:
        """Send a POST request to `endpoint` of `self.api`.

        Returns `False` if unsuccessful.

        :param endpoint: Endpoint relative to `self.api` to call.
        :param data: The json data to send in the POST.

        :return: The json data of the response, or `False` if unsuccessful.
        """
        return self.__request(post, endpoint, data)


class TwitchOAuth2Helper(OAuth2Handler):
    name = "twitch"
    default_config = {
        "user_id": None,
        "client_id": None,
        "client_secret": None,
        "irc_oauth": None,
    }
    callback_port = None
    scopes = ["moderator:read:chatters"]
    oauth_grant_uri = "https://id.twitch.tv/oauth2/authorize"
    oauth_token_uri = "https://id.twitch.tv/oauth2/token"
    api = "https://api.twitch.tv/helix"

    def set_fields(self):
        super().set_fields()

        self.user_id = dict.get(self.cfg, "user_id", None)
        self.irc_oauth = dict.get(self.cfg, "irc_oauth", None)

    def jsonify(self):
        return {
            "user_id": self.user_id,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "irc_oauth": self.irc_oauth,
            "token": self.token,
        }

    def setup(self):
        # Getting Twitch username
        self.user_id = input("Your Twitch username: ").lower()

        # Asking to set up Twitch 2FA
        print(f"\nHello, {self.user_id}!")
        print(
            "You'll need to make sure you have Twitch.tv mobile two-factor authentication enabled:"
        )
        print("1. Go to your Twitch account settings, Security and Privacy.")
        print(
            "2. Scroll to Security and click 'Set Up Two-Factor Authentication' and follow the steps."
        )
        input("Press [Enter] once you've set that up.")

        # Getting Client ID and Secret
        print("\nNow, go to dev.twitch.tv and log in:")
        print("1. Click on 'Your Console' in the top right.")
        print("2. On the right side pane, click Register Your Application.")
        print("3. Give it a name. Doesn't matter what.")
        print("4. Create an OAuth redirect for http://localhost and click 'Add'.")
        print("5. Set the Category to Chat Bot.")
        print("6. Click 'Create', and then click 'Manage'.")
        self.client_id = input("Enter the Client ID: ")

        print("\nNow, click on 'New Secret'.")
        self.client_secret = input("Enter the Client Secret: ")

        # Getting IRC OAuth
        print("\nAlmost done! Now, go to twitchapps.com/tmi/ and log in.")

        # Making sure the key is stripped
        self.irc_oauth = input("Enter the text it gives you: ")
        if self.irc_oauth.startswith("oauth:"):
            self.irc_oauth = self.irc_oauth[6:]

        return True

    def get_stream(self, user_id: int = None, user_login: str = None) -> bool | dict:
        """Return the stream information for `user_id` or `user_login`.

        Prioritizes `user_id` first.

        :param user_id: The User ID of the user to get stream information for.
        :param user_login: The User Login of the user to get stream information for.

        :return: Stream information, or `False` if no result/query failed.
        """
        if user_id:
            query = self._get(f"/streams?user_id={user_id}")

            if len(query["data"]) == 0:
                return False

            return query["data"][0]

        if user_login:
            query = self._get(f"/streams?user_login={user_login}")

            if len(query["data"]) == 0:
                return False

            return query["data"][0]

        raise ValueError("get_stream requires either user_id or user_login")

    def get_user_id(self, user_login: str) -> bool | int:
        """Return the user ID for `user_login`.

        :param user_login: The User Login of the user to get the User ID for.

        :return: The User ID of the user, or `False` if no result/query failed.
        """
        query = self._get(f"/users?login={user_login}")

        if len(query["data"]) == 0:
            return False

        return int(query["data"][0]["id"])

    def get_all_chatters(self, channel_id: int, user_id: int) -> bool | list:
        """Return a list of `user_login` for all users in the current channel.

        Automatically paginates and returns all users.

        :param channel_id: The channel ID to get chatters for.
        :param user_id: The User ID of the current OAuth2 session user.

        :return: A `list` of all `user_login` connected to the chat for `channel_id`.
        """
        results = []
        query = self._get(
            f"/chat/chatters?broadcaster_id={channel_id}&moderator_id={user_id}&first=1000"
        )

        # nothing there. return empty list here to prevent errors
        if len(query["data"]) == 0:
            return results

        results += [user["user_login"] for user in query["data"]]

        # paginate, if applicable
        # query["pagination"] should be empty (== False) if no more than 1000
        while query["pagination"]:
            query = self._get(
                f"/chat/chatters?broadcaster_id={channel_id}&moderator_id={user_id}&first=1000&after={query['pagination']['cursor']}"
            )
            results += [user["user_login"] for user in query["data"]]

        return results

    def get_live_streams(self, channels: list) -> list:
        """Return a list of live streams from a list of `user_id`.

        Automatically paginates and returns all live streams in `channels`.

        :param channels: The list of `user_id` to get live channels for.

        :return: A `list` of all `[user_id, user_login]` in `channels` currently live on Twitch.
        """
        # TODO: support more than 100 streams, but really, that should never happen for a single installation?
        # in meantime cull to 100
        channels = channels[:100]

        results = []
        query = self._get(
            f"/streams?{'&'.join([f'user_id={id}' for id in channels])}&type=live&first=100"
        )

        # nothing there. return empty list here to prevent errors
        if len(query["data"]) == 0:
            return results

        results += [[user["user_id"], user["user_login"]] for user in query["data"]]

        return results
