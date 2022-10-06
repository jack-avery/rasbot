# 'request' code for osu! requests. To get this to work:
# Fill out the fields in the config file with the strings found at the websites
# Create a command using cmdadd with &request& as the response.

# TODO refactor this to use new osu! API v2 once it drops with Lazer

import socket
import requests
import re
from commands import BaseModule

DEFAULT_CONFIG = {
    # Your osu! ID. Go to your profile on the website and this should be in the URL.
    "osu_user_id": "",
    # Your osu! API key. Get this from https://osu.ppy.sh/p/api.
    "osu_api_key": "",
    # Your osu! IRC password. Get this from https://old.ppy.sh/p/irc.
    "osu_irc_pwd": "",
}

OSU_BEATMAPSET_RE = r'^https:\/\/osu.ppy.sh\/beatmapsets\/[\w#]+\/(\d+)$'

OSU_B_RE = r'^https:\/\/osu.ppy.sh\/b\/(\d+)$'


class Module(BaseModule):
    helpmsg = 'Request an osu! beatmap to be played. Usage: request <beatmap link>'

    def __init__(self, bot, name):
        BaseModule.__init__(self, bot, name, DEFAULT_CONFIG)

        # Create IRC socket and connect to irc.ppy.sh
        self.irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.irc.connect(('irc.ppy.sh', 6667))

        self.beatmapset_re = re.compile(OSU_BEATMAPSET_RE)
        self.b_re = re.compile(OSU_B_RE)

        # Resolve username
        self.username = False
        try:
            req = requests.get(
                f"https://osu.ppy.sh/api/get_user?u={self.cfg['osu_user_id']}&k={self.cfg['osu_api_key']}")
            self.username = req.json()[0]['username'].replace(" ", "_")
        except:
            print(
                "An error occurred trying to resolve your osu! username. Your API key may be invalid.")

    def main(self):
        if self.username:
            if not self.bot.cmdargs:
                return "Provide a map to request."

            req = self.bot.cmdargs[0].lower()

            # Resolve ID
            if self.beatmapset_re.match(req):
                id = self.beatmapset_re.findall(req)[0]
            elif self.b_re.match(req):
                id = self.b_re.findall(req)[0]
            else:
                return "Could not resolve beatmap link format."

            # Retrieve beatmap information
            req = requests.get(
                f"https://osu.ppy.sh/api/get_beatmaps?b={id}&k={self.cfg['osu_api_key']}")

            try:
                map = req.json()[0]
            except IndexError:
                return "Could not retrieve beatmap information."

            # Anything can go in here, this is intended to be customizable.
            # See the possible information from the 'map' dict at https://github.com/ppy/osu-api/wiki#response
            message = f"({map['bpm']} BPM, {map['difficultyrating']} Stars)"

            self.send_osu_message(
                f"{self.bot.author_name} requested: [https://osu.ppy.sh/b/{id} {map['artist']} - {map['title']} [{map['version']}]] {message}")

            return "Request sent!"

        else:
            return "Username could not be resolved. Please check/fix configuration."

    def send_osu_message(self, msg):
        self.irc.send(bytes(
            f"USER {self.username} {self.username} {self.username} {self.username}\n", "UTF-8"))
        self.irc.send(bytes(f"PASS {self.cfg['osu_irc_pwd']}\n", "UTF-8"))
        self.irc.send(bytes(f"NICK {self.username}\n", "UTF-8"))
        self.irc.send(bytes(f"PRIVMSG {self.username} {msg}\n", "UTF-8"))
