import socket
import requests
import re
from commands import BaseModule

OSU_USER_ID = "6578827"
"""Your osu! ID. Go to your profile on the website and this should be in the URL."""

OSU_API_KEY = ""
"""Your osu! API key. Get this from https://osu.ppy.sh/p/api."""

OSU_IRC_PASSWORD = ""
"""Your osu! IRC password. Get this from https://old.ppy.sh/p/irc."""

OSU_BEATMAPSET_RE = r'^https:\/\/osu.ppy.sh\/beatmapsets\/[\w#]+\/(\d+)$'

OSU_B_RE = r'^https:\/\/osu.ppy.sh\/b\/(\d+)$'


class Module(BaseModule):
    def __init__(self):
        BaseModule.__init__(self)

        # Create IRC socket and connect to irc.ppy.sh
        self.irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.irc.connect(('irc.ppy.sh', 6667))

        self.beatmapset_re = re.compile(OSU_BEATMAPSET_RE)
        self.b_re = re.compile(OSU_B_RE)

        # Resolve username
        self.username = False
        try:
            req = requests.get(
                f"https://osu.ppy.sh/api/get_user?u={OSU_USER_ID}&k={OSU_API_KEY}")
            self.username = req.json()[0]['username'].replace(" ", "_")
        except:
            print(
                "An error occurred trying to resolve your osu! username. Your API key may be invalid.")

    def main(self, bot):
        if self.username:
            try:
                req = bot.cmdargs[0].lower()
            except:
                return

            # Resolve ID
            if self.beatmapset_re.match(req):
                id = self.beatmapset_re.findall(req)[0]
            elif self.b_re.match(req):
                id = self.b_re.findall(req)[0]
            else:
                return

            # Retrieve beatmap information
            req = requests.get(
                f"https://osu.ppy.sh/api/get_beatmaps?b={id}&k={OSU_API_KEY}")
            map = req.json()[0]

            # Anything can go in here, this is intended to be customizable.
            # See the possible information from the 'map' dict at https://github.com/ppy/osu-api/wiki#response
            message = f"({map['bpm']} BPM, {map['difficultyrating']} Stars)"

            self.send_message(
                f"{bot.author_name} requested: [https://osu.ppy.sh/b/{id} {map['artist']} - {map['title']} [{map['version']}]] {message}")

    def send_message(self, msg):
        self.irc.send(bytes("USER " + self.username + " " + self.username +
                      " " + self.username + " " + self.username + "\n", "UTF-8"))
        self.irc.send(bytes("PASS " + OSU_IRC_PASSWORD + "\n", "UTF-8"))
        self.irc.send(bytes("NICK " + self.username + "\n", "UTF-8"))
        self.irc.send(bytes("PRIVMSG " + self.username +
                      " " + msg + "\n", "UTF-8"))
