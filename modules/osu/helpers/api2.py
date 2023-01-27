import webbrowser
import socket
import logging

from requests import get, post

from src.definitions import Singleton
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

        link = "https://osu.ppy.sh/oauth/authorize?client_id=%client_id%&redirect_uri=http://localhost:%callback_port%&response_type=code&scope=chat.write+public"
        link = link.replace("%client_id%", self.cfg['client_id'])\
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
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        token = post("https://osu.ppy.sh/oauth/token",
                     headers=headers, json=data)

        if not token.status_code == 200:
            logger.error(f"OAuth token grab failed! ({token.json()})")
            return

        self.cfg['token'] = token.json()
        write(self.cfgpath, self.cfg)

    def __request(self, method, endpoint: str, data: dict = None):
        if not self.cfg['token']:
            return False

        endpoint = "https://osu.ppy.sh/api/v2/" + endpoint

        headers = {
            "Authorization": f"{self.cfg['token']['token_type']} {self.cfg['token']['access_token']}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        if data:
            response = method(endpoint, headers=headers, json=data)
        else:
            response = method(endpoint, headers=headers)
        logger.debug(response.json())
        if response.status_code == 200:
            return response.json()

        # refresh token and retry once?
        self.__refresh_token()
        headers["Authorization"] = f"{self.cfg['token']['token_type']} {self.cfg['token']['access_token']}"
        if data:
            response = method(endpoint, headers=headers, json=data)
        else:
            response = method(endpoint, headers=headers)
        logger.debug(response.json())
        if response.status_code == 200:
            return response.json()

        # give up
        logger.error(
            "could not successfully perform request after a token refresh")
        return False

    def get(self, endpoint: str):
        return self.__request(get, endpoint)

    def post(self, endpoint: str, data: dict):
        return self.__request(post, endpoint, data)

    def get_beatmap(self, beatmap_id: int):
        """Get information for the beatmap with ID `beatmap_id`.
        """
        return self.get(f"beatmaps/{beatmap_id}")

    def get_beatmapset(self, beatmapset_id: int):
        """Get maps and information for the beatmap set with ID `beatmapset_id`.
        """
        return self.get(f"beatmapsets/{beatmapset_id}")

    def get_user_top_plays(self, user_id: int):
        """Get top plays for user with ID `user_id`.
        """
        return self.get(f"users/{user_id}/scores/best")

    def get_user_recent_plays(self, user_id: int):
        """Get recent plays (including fails) for user with ID `user_id`.
        """
        return self.get(f"users/{user_id}/scores/recent?include_fails=1")

    def send_message(self, message: str, target_id: int):
        """Send `message` to osu! User ID `target`.
        """
        data = {
            "target_id": target_id,
            "message": message,
            "is_action": False
        }
        self.post("chat/new", data)
