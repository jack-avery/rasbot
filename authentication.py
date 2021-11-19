###
#   rasbot authentication module
#   raspy#0292 - raspy_on_osu
###

import requests
from definitions import DEFAULT_AUTHFILE,\
    AuthenticationDeniedError

class Authentication:
    def __init__(self,file:str=None):
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
        if file is None:
            self.file = DEFAULT_AUTHFILE
        else:
            self.file = file

        self.read_authfile()

    def read_authfile(self):
        """Reads from the authfile set by self.file.

        Assigns the read values to this `Authentication` objects' `auth` field.
        """
        # Attempting to read the auth file
        try:
            with open(self.file,'r') as authfile:
                authlines = authfile.readlines()
        
        # If not found, write the default and return
        except FileNotFoundError:
            self.create_default()
            return

        # Parsing the auth file into the auth dict
        self.auth = dict()
        for line in authlines:
            # Remove newline...
            line = line[:-1]
            # Split by delim : (see format)...
            line = line.split(':')
            # Append to dict
            self.auth[line[0]] = line[1]

    def write_authfile(self):
        """Writes to the authfile set by self.file.
        """
        # Parsing the auth dict into lines for writing
        authlines = list()
        for key,value in self.auth.items():
            authlines.append(f"{key}:{value}\n")

        # Writing the auth file
        with open(self.file,'w') as authfile:
            authfile.writelines(authlines)
    
    def create_default(self):
        """Writes the default authfile.
        """
        self.auth = dict()
        self.auth['user_id'] = "twitch username"
        self.auth['client_id'] = "client id"
        self.auth['client_secret'] = "client secret"
        self.auth['irc_oauth'] = "irc oauth"

        self.write_authfile()

    def get_auth(self):
        """Returns this `Authentication` objects' `auth` dict.
        """
        return self.auth

    def get_headers(self):
        """Returns headers.
        For use in some queries, e.g. the `uptime` method.
        """
        return {'Client-ID': self.auth["client_id"],
                'Authorization': f'Bearer {self.auth["oauth"]}',
                'Accept': 'application/vnd.twitchtv.v5+json'}
    
    def request_oauth(self):
        """Returns a new OAuth key requested from twitch.
        """
        # Request new oauth token from Twitch
        r=requests.post(f"https://id.twitch.tv/oauth2/token"
                    +f'?client_id={self.auth["client_id"]}'
                    +f'&client_secret={self.auth["client_secret"]}'
                     +'&grant_type=client_credentials').json()

        # Return the new OAuth key
        try:
            return r['access_token']
        
        # If it can't find the key...
        except KeyError:
            raise AuthenticationDeniedError("got error response status"
                    +f"{r['status']}, message '{r['message']}'")
