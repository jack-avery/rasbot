import src.authentication
import webbrowser


class OsuAPIv2Helper(src.authentication.OAuth2Handler):
    name = "osu2"
    default_config = {
        # Your osu! user ID. Owner of the application.
        "osu_user_id": "",
        # The Client ID you got when you registered.
        "client_id": "",
        # The Client Secret you got when you registered.
        "client_secret": "",
        # The remainder of the info is obtained automatically by the OsuAPIv2Helper.
    }
    callback_port = 27274
    scopes = ["chat.write", "public"]
    oauth_grant_uri = "https://osu.ppy.sh/oauth/authorize"
    oauth_token_uri = "https://osu.ppy.sh/oauth/token"
    api = "https://osu.ppy.sh/api/v2"

    def set_fields(self):
        super().set_fields()

        self.osu_user_id = self.cfg.get("osu_user_id", None)

    def setup(self):
        print("osu! API v2 setup")

        print("Go to your osu! profile on the website.")
        self.osu_user_id = input(
            "Your osu! User ID (https://osu.ppy.sh/users/[this number]): "
        )

        webbrowser.open(
            "https://osu.ppy.sh/home/account/edit#new-oauth-application", new=2
        )
        print(
            "\nA new browser page to your osu! profile has opened. Click on 'New OAuth Application' at the bottom."
        )
        print(
            "Enter a name and set the Application Callback URL to http://localhost:27274."
        )

        self.client_id = input("Client ID: ")
        self.client_secret = input("Client Secret: ")

        return True

    def get_username(self, user_id: int) -> str:
        """
        https://osu.ppy.sh/docs/index.html#get-user

        Get the username for user with ID `user_id`.
        """
        return self._get(f"/users/{user_id}")

    def get_beatmap(self, beatmap_id: int) -> dict:
        """
        https://osu.ppy.sh/docs/index.html#get-beatmap

        Get information for the beatmap with ID `beatmap_id`.
        """
        return self._get(f"/beatmaps/{beatmap_id}")

    def get_beatmapset(self, beatmapset_id: int) -> dict:
        """
        https://osu.ppy.sh/docs/index.html#get-apiv2beatmapsetsbeatmapset

        Get maps and information for the beatmap set with ID `beatmapset_id`.
        """
        return self._get(f"/beatmapsets/{beatmapset_id}")

    def get_user_top_plays(self, user_id: int) -> list:
        """
        https://osu.ppy.sh/docs/index.html#get-user-scores

        Get top plays for user with ID `user_id`.
        """
        return self._get(f"/users/{user_id}/scores/best")

    def get_user_recent_plays(self, user_id: int, include_fails: bool = True) -> list:
        """
        https://osu.ppy.sh/docs/index.html#get-user-scores

        Get recent plays for user with ID `user_id`. Includes fails by default.
        """
        return self._get(
            f"/users/{user_id}/scores/recent?include_fails={'1' if include_fails else '0'}"
        )

    def send_message(self, target_id: int, message: str) -> dict:
        """Send `message` to osu! User ID `target`."""
        data = {"target_id": target_id, "message": message, "is_action": False}
        return self._post("/chat/new", data)

    def message_self(self, message: str) -> dict:
        """
        Send `message` to yourself.

        This will eventually replace using IRC in `modules/osu/request.py`,
        this does not currently work: https://github.com/ppy/osu/discussions/21598
        """
        data = {"target_id": self.osu_user_id, "message": message, "is_action": False}
        return self._post("/chat/new", data)

    def jsonify(self):
        return {
            "osu_user_id": self.osu_user_id,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "token": self.token,
        }
