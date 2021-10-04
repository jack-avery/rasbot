###
#   rasbot authentication module
#   raspy#0292 - raspy_on_osu
###

import requests
from definitions import DEFAULT_AUTHFILE

class Authentication:
    def __init__(self,store:str=DEFAULT_AUTHFILE):
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
        self.store = store
        self.read_authfile()

    def read_authfile(self):
        # Reading the auth file
        with open(self.store,'r') as authfile:
            authlines = authfile.readlines()

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
        # Parsing the auth dict into lines for writing
        authlines = list()
        for key,value in self.auth.items():
            authlines.append(f"{key}:{value}\n")

        # Writing the auth file
        with open(self.store,'w') as authfile:
            authfile.writelines(authlines)

    def get_auth(self):
        """Returns the auth dict.
        """
        return self.auth

    def get_headers(self):
        """Returns the headers. For use in some queries.
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

        # Return the new oauth key
        return r['access_token']

if __name__ == "__main__":
    auth = Authentication()
    if input("Type 'refresh' to refresh your Twitch OAuth key, anything else will exit: ").lower() == "refresh":
        auth.auth['oauth'] = auth.request_oauth()
        auth.write_authfile()
        input("Your new OAuth token has been written to the file.")
