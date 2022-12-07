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
    # ID of the user that the request should go to.
    "osu_trgt_id": "",
    # The format of the message to send alongside. See format_message() for keys.
}

OSU_BEATMAPSET_RE = r'^https:\/\/osu.ppy.sh\/beatmapsets\/[\w#]+\/(\d+)$'

OSU_B_RE = r'^https:\/\/osu.ppy.sh\/b(?:eatmaps)?\/(\d+)$'


class Module(BaseModule):
    helpmsg = 'Request an osu! beatmap to be played. Usage: request <beatmap link>'

    def __init__(self, bot, name):
        BaseModule.__init__(self, bot, name, DEFAULT_CONFIG)

        self.beatmapset_re = re.compile(OSU_BEATMAPSET_RE)
        self.b_re = re.compile(OSU_B_RE)

        # Resolve usernames
        self.username = self.resolve_username(self.cfg['osu_user_id'])
        self.target = self.resolve_username(self.cfg['osu_trgt_id'])

    def resolve_username(self, id):
        """Resolves a users' osu! username from their ID.
        """
        self.bot.log_debug(f"Resolving osu! username for ID {id}")
        try:
            req = requests.get(
                f"https://osu.ppy.sh/api/get_user?u={id}&k={self.cfg['osu_api_key']}")
            return req.json()[0]['username'].replace(" ", "_")
        except:
            print(
                f"An error occurred trying to resolve osu! username for ID {id}. Your API key may be invalid.")
            return None

    def format_message(self, map):
        # See https://github.com/ppy/osu-api/wiki#response for more info

        STATUSES = ["Pending", "Ranked", "Approved",
                    "Qualified", "Loved", "Graveyard", "WIP"]

        MODES = ["Standard", "Taiko", "CTB", "Mania"]

        OPTIONS = {
            # web
            "map": lambda m: f"[https://osu.ppy.sh/b/{m['beatmap_id']} {m['artist']} - {m['title']} [{m['version']}]]",
            "mapid": lambda m: m['beatmap_id'],
            "mapsetid": lambda m: m['beatmapset_id'],
            "mapstatus": lambda m: f"{STATUSES[int(m['approved'])]}",

            # creator
            "creator": lambda m: f"[https://osu.ppy.sh/users/{m['creator_id']} {m['creator']}]",
            "creatorid": lambda m: m['creator_id'],
            "creatorname": lambda m: m['creator'],

            # beatmap metadata
            "length": lambda m: f"{int(int(m['total_length']) / 60)}:{int(m['total_length']) % 60}",
            "bpm": lambda m: round(float(m['bpm']), 2),
            "stars": lambda m: round(float(m['difficultyrating']), 2),
            "cs": lambda m: m['diff_size'],
            "od": lambda m: m['diff_overall'],
            "ar": lambda m: m['diff_approach'],
            "hp": lambda m: m['diff_drain'],
            "gamemode": lambda m: f"{MODES[int(m['mode'])]}",

            # song info
            "song": lambda m: f"{m['artist']} - {m['title']}",
            "songartist": lambda m: m['artist'],
            "songartistunicode": lambda m: m['artist_unicode'],
            "songname": lambda m: m['title'],
            "songtitleunicode": lambda m: m['title_unicode'],
            "songsource": lambda m: m['source'],
        }

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

            # Customization for this is TODO. Until then this should do just fine.
            time = f"{int(int(map['total_length']) / 60)}:{int(map['total_length']) % 60}"
            bpm = round(float(map['bpm']), 2)
            stars = round(float(map['difficultyrating']), 2)
            message = f"({time} @ {bpm}BPM, {stars}*, mapset by [https://osu.ppy.sh/users/{map['creator_id']} {map['creator']}])"

            self.send_osu_message(
                f"{self.bot.author_name} requested: [https://osu.ppy.sh/b/{id} {map['artist']} - {map['title']} [{map['version']}]] {message}")

            return "Request sent!"

        else:
            return "Username could not be resolved. Please check/fix configuration."

    def send_osu_message(self, msg):
        self.bot.log_debug(f"Sending osu! message '{msg}' to {self.target}")
        # Create IRC socket and connect to irc.ppy.sh
        irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        irc.connect(('irc.ppy.sh', 6667))

        irc.send(bytes(
            f"USER {self.username} {self.username} {self.username} {self.username}\n", "UTF-8"))
        irc.send(bytes(f"PASS {self.cfg['osu_irc_pwd']}\n", "UTF-8"))
        irc.send(bytes(f"NICK {self.username}\n", "UTF-8"))
        irc.send(bytes(f"PRIVMSG {self.target} {msg}\n", "UTF-8"))

        irc.close()
