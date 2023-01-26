import webbrowser
import socket
import requests
import logging

from src.config import BASE_CONFIG_PATH, read, write

logger = logging.getLogger("rasbot")

DEFAULT_CONFIG = {
    # Your osu! user ID. Owner of the application.
    "osu_user_id": "",
    # The Client ID you got when you registered.
    "client_id": "",
    # The Client Secret you got when you registered.
    "client_secret": "",

    # The remainder of the info is obtained automatically by the OsuAPIv2Helper.
}

CALLBACK_PORT = 27274
"""Callback URL set in the application MUST be `http://localhost:27274`."""

OAUTH_APP_AUTH_LINK = "https://osu.ppy.sh/oauth/authorize?client_id=%client_id%&redirect_uri=http://localhost:%callback_port%&response_type=code&scope=chat.write+public"
OAUTH_TOKEN_REFRESH_EP = "https://osu.ppy.sh/oauth/token"
OAUTH_TOKEN_REFRESH_HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
}

OSU_API_BASE = "https://osu.ppy.sh/api/v2/"


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
        self.cfgpath = f"{BASE_CONFIG_PATH}/{id}/modules/osu/helpers/api2.txt"
        self.cfg = read(self.cfgpath, DEFAULT_CONFIG)

        if "token" not in self.cfg:
            self.__get_auth()

    def __get_auth(self):
        """Opens the Application Authorization page to get the auth code.
        """
        if not self.cfg['client_id'] or not self.cfg['client_secret']:
            return

        link = OAUTH_APP_AUTH_LINK.replace("%client_id%", self.cfg['client_id'])\
                                  .replace("%callback_port%", str(CALLBACK_PORT))
        webbrowser.open(link, new=2)
        logger.info(
            "See your web browser to continue setting up your osu! API v2 Authentication.")

        # Listen once for the callback containing the code
        with socket.create_server(('localhost', CALLBACK_PORT)) as listener:
            conn, addr = listener.accept()
            auth_code = conn.recv(4096)

            # Strip request bytes to strictly the code
            auth_code = auth_code[auth_code.find(b'=')+1:]
            auth_code = auth_code[:auth_code.find(b' ')]
            auth_code = auth_code.decode("ASCII")

            # Inform the user in-browser
            conn.send(b'Got the temporary code! You can now close this window.')

        logger.info(
            "Got the temporary code! Getting your initial OAuth token...")
        data = {
            "client_id": self.cfg['client_id'],
            "client_secret": self.cfg['client_secret'],
            "code": auth_code,
            "grant_type": "authorization_code",
            "redirect_uri": f"http://localhost:{CALLBACK_PORT}"
        }
        self.__get_token(data)

    def __refresh_token(self):
        """Refresh the token using the existing OAuth tokens' refresh code.
        """
        if not self.cfg['token']:
            return

        logger.debug("refreshing OAuth token")

        data = {
            "client_id": self.cfg['client_id'],
            "client_secret": self.cfg['client_secret'],
            "grant_type": "refresh_token",
            "refresh_token": self.cfg['token']['refresh_token']
        }
        self.__get_token(data)

    def __get_token(self, data):
        """Get a new token or refresh an existing one using `data`.
        """
        token = requests.post(OAUTH_TOKEN_REFRESH_EP,
                              headers=OAUTH_TOKEN_REFRESH_HEADERS, json=data)
        if not token.status_code == 200:
            logger.error(f"OAuth token grab failed! ({token.json()})")

        self.cfg['token'] = token.json()
        write(self.cfgpath, self.cfg)

    def get(self, endpoint: str):
        if not self.cfg['token']:
            return False

        endpoint = OSU_API_BASE + endpoint
        headers = {
            "Authorization": f"{self.cfg['token']['token_type']} {self.cfg['token']['access_token']}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        response = requests.get(endpoint, headers=headers)
        if response.status_code == 200:
            return response.json()

        # If not successful, refresh token and try again?
        self.__refresh_token()
        response = requests.get(endpoint, headers=headers)
        return response.json()

    def send_message(self, message: str, target_id: int):
        """Send `message` to osu! User ID `target`.
        """
        if not self.cfg['token']:
            return False

        endpoint = OSU_API_BASE + "chat/new"
        headers = {
            "Authorization": f"{self.cfg['token']['token_type']} {self.cfg['token']['access_token']}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        data = {
            "target_id": target_id,
            "message": message,
            "is_action": False
        }
        res = requests.post(endpoint,
                            headers=headers, json=data)
