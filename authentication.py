import json
import requests

from definitions import DEFAULT_AUTHFILE,\
    AuthenticationDeniedError


class Authentication:
    def __init__(self, file: str = None):
        """Create a new authentication identity.
        Automatically pulls and parses from the _AUTH file.

        :param file: The file to pull auth from. See format.

        Format:

        user_id:<twitch_name>

        client_id:<client_id>

        client_secret:<client_secret>

        irc_oauth:<irc_oauth>

        oauth:<twitch_oauth>
        """
        if not file:
            self.file = DEFAULT_AUTHFILE
        else:
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
        """Writes to the authfile set by self.file.
        """
        # Writing the auth file
        with open(self.file, 'w') as authfile:
            authfile.write(json.dumps(self.auth, indent=4))

    def get(self, key):
        """Return the item with the given `key`.
        """
        return self.auth[key]

    def get_headers(self):
        """Returns headers.
        For use in some queries, e.g. the `uptime` module.
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

        # Return the new OAuth key
        try:
            self.auth['oauth'] = r['access_token']
            self.write_authfile()

        # If it can't find the key...
        except KeyError:
            raise AuthenticationDeniedError("got error response status"
                                            + f"{r['status']}, message '{r['message']}'")
