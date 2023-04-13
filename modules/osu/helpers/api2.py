import src.authentication


class OsuAPIv2Helper(src.authentication.OAuth2Handler):
    name = "osu2"
    """Discriminator for this OAuth2Handler."""

    default_config = {
        # Your osu! user ID. Owner of the application.
        "osu_user_id": "",
        # The Client ID you got when you registered.
        "client_id": "",
        # The Client Secret you got when you registered.
        "client_secret": "",
        # The remainder of the info is obtained automatically by the OsuAPIv2Helper.
    }
    """Default configuration for this OAuth2Handler."""

    callback_port = 27274
    """Callback port to http://localhost for auth code grabbing."""

    scopes = ["chat.write", "public"]
    """A list of scopes that are used by the handler. Default is for Twitch."""

    oauth_grant_uri = "https://osu.ppy.sh/oauth/authorize"
    """Base URL of the website to get the user authorization grant from."""

    oauth_token_uri = "https://osu.ppy.sh/oauth/token"
    """API endpoint to get/refresh the OAuth token at."""

    api = "https://osu.ppy.sh/api/v2"
    """Base URL of the API."""

    def get_username(self, user_id: int):
        """Get the username for user with ID `user_id`."""
        return self._get(f"/users/{user_id}")

    def get_beatmap(self, beatmap_id: int):
        """Get information for the beatmap with ID `beatmap_id`."""
        return self._get(f"/beatmaps/{beatmap_id}")

    def get_beatmapset(self, beatmapset_id: int):
        """Get maps and information for the beatmap set with ID `beatmapset_id`."""
        return self._get(f"/beatmapsets/{beatmapset_id}")

    def get_user_top_plays(self, user_id: int):
        """Get top plays for user with ID `user_id`."""
        return self._get(f"/users/{user_id}/scores/best")

    def get_user_recent_plays(self, user_id: int, include_fails: bool = True):
        """Get recent plays for user with ID `user_id`. Includes fails by default."""
        return self._get(
            f"/users/{user_id}/scores/recent?include_fails={'1' if include_fails else '0'}"
        )

    def send_message(self, target_id: int, message: str):
        """Send `message` to osu! User ID `target`."""
        data = {"target_id": target_id, "message": message, "is_action": False}
        self._post("/chat/new", data)
