# 'request' code for osu! requests. To get this to work:
# Fill out the fields in the config file with the strings found at the websites
# Create a command using cmdadd with &request& as the response.

# TODO refactor this to use new osu! API v2 once it drops with Lazer

import socket
import requests
import re
from commands import BaseModule
from definitions import MODULE_MENTION_REGEX

DEFAULT_CONFIG = {
    # Your osu! ID. Go to your profile on the website and this should be in the URL.
    "osu_user_id": "",
    # Your osu! API key. Get this from https://osu.ppy.sh/p/api.
    "osu_api_key": "",
    # Your osu! IRC password. Get this from https://old.ppy.sh/p/irc.
    "osu_irc_pwd": "",
    # ID of the user that the request should go to.
    "osu_trgt_id": "",
    # The format of the message to send alongside. See MESSAGE_OPTIONS for keys.
    # Enclose keys in & as you would a module in a command.
    "message_format": "&map& &mods& (&length& @ &bpm&BPM, &stars&*, mapped by &creator&)"
}

OSU_BEATMAPSETID_RE = r'^https:\/\/osu.ppy.sh\/beatmapsets\/[\w#]+\/(\d+)$'
OSU_B_RE = r'^https:\/\/osu.ppy.sh\/b(?:eatmaps)?\/(\d+)$'

OSU_BEATMAPSET_RE = r'^https:\/\/osu.ppy.sh\/beatmapsets\/(\d+)$'

# See https://github.com/ppy/osu-api/wiki#response for more info
OSU_STATUSES = ["Pending", "Ranked", "Approved",
                "Qualified", "Loved", "Graveyard", "WIP"]

OSU_MODES = ["Standard", "Taiko", "CTB", "Mania"]

MESSAGE_OPT_RE = re.compile(MODULE_MENTION_REGEX)

MESSAGE_OPTIONS = {
    # web
    "map": lambda m: f"[https://osu.ppy.sh/b/{m['beatmap_id']} {m['artist']} - {m['title']} [{m['version']}]]",
    "mapid": lambda m: m['beatmap_id'],
    "mapsetid": lambda m: m['beatmapset_id'],
    "mapstatus": lambda m: f"{OSU_STATUSES[int(m['approved'])]}",

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
    "gamemode": lambda m: f"{OSU_MODES[int(m['mode'])]}",

    # song info
    "song": lambda m: f"{m['artist']} - {m['title']}",
    "songartist": lambda m: m['artist'],
    "songartistunicode": lambda m: m['artist_unicode'],
    "songtitle": lambda m: m['title'],
    "songtitleunicode": lambda m: m['title_unicode'],
    "songsource": lambda m: m['source'],

    # requests specific additions
    "mods": lambda m: m['mods']
}


class Module(BaseModule):
    helpmsg = 'Request an osu! beatmap to be played. Usage: request <beatmap link> <+mods?>'

    def __init__(self, bot, name):
        BaseModule.__init__(self, bot, name, DEFAULT_CONFIG)

        beatmapsetid_re = re.compile(OSU_BEATMAPSETID_RE)
        b_re = re.compile(OSU_B_RE)

        beatmapset_re = re.compile(OSU_BEATMAPSET_RE)

        self.beatmap_res = [beatmapsetid_re, b_re]
        self.beatmapset_res = [beatmapset_re]

        # Resolve usernames
        self.username = self.resolve_username(self.cfg_get('osu_user_id'))
        self.target = self.resolve_username(self.cfg_get('osu_trgt_id'))

    def resolve_username(self, id):
        """Resolves a users' osu! username from their ID.
        """
        self.log_d(f"resolving osu! username for ID {id}")
        req = None
        try:
            req = requests.get(
                f"https://osu.ppy.sh/api/get_user?u={id}&k={self.cfg_get('osu_api_key')}")
            return req.json()[0]['username'].replace(" ", "_")
        except:
            if isinstance(req, requests.Response):
                self.log_e(
                    f"could not resolve osu! username for id:{id}. API key may be invalid. (response code {req.status_code})"
                )
            else:
                self.log_e(
                    f"something has gone horribly wrong! 'req' is of type {type(req)} - expected requests.Response"
                )
            return None

    def format_message(self, map):
        message = self.cfg_get('message_format')

        for m in MESSAGE_OPT_RE.findall(message):
            try:
                message = message.replace(
                    f'&{m}&',
                    str(MESSAGE_OPTIONS[m](map))
                )
            except KeyError:
                self.log_e(
                    f"config error: message_format uses invalid key '{m}'")

        return message

    def main(self):
        if not self.username or not self.target:
            return "A username (either self or target) could not be resolved. Please check/fix configuration."

        if not self.bot.cmdargs:
            return "Provide a map to request."

        req = self.bot.cmdargs[0].lower()

        mods = ''
        if len(self.bot.cmdargs) > 1:
            if self.bot.cmdargs[1].startswith("+"):
                mods = self.bot.cmdargs[1].upper()

        # Resolve ID
        is_id = False
        id = False
        for beatmap_re in self.beatmap_res:
            if beatmap_re.match(req):
                id = beatmap_re.findall(req)[0]
                is_id = True
                break

        if not id:
            for beatmapset_re in self.beatmapset_res:
                if beatmapset_re.match(req):
                    id = beatmapset_re.findall(req)[0]
                    break

        if not id:
            return "Could not resolve beatmap link format."

        # Retrieve beatmap information
        if is_id:
            req = requests.get(
                f"https://osu.ppy.sh/api/get_beatmaps?b={id}&k={self.cfg_get('osu_api_key')}").json()
        else:
            req = requests.get(
                f"https://osu.ppy.sh/api/get_beatmaps?s={id}&k={self.cfg_get('osu_api_key')}").json()
            req.sort(key=lambda r: r['difficultyrating'], reversed=True)

        try:
            map = req[0]
        except IndexError:
            return "Could not retrieve beatmap information."

        map['mods'] = mods
        message = self.format_message(map)

        self.send_osu_message(
            f"{self.bot.author_name} requested: {message}")

        return "Request sent!"
            

    def send_osu_message(self, msg):
        self.log_d(f"sending osu! message '{msg}' as {self.username} to {self.target}")
        # Create IRC socket and connect to irc.ppy.sh
        irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        irc.connect(('irc.ppy.sh', 6667))

        irc.send(bytes(
            f"USER {self.username} {self.username} {self.username} {self.username}\n", "UTF-8"))
        irc.send(bytes(f"PASS {self.cfg_get('osu_irc_pwd')}\n", "UTF-8"))
        irc.send(bytes(f"NICK {self.username}\n", "UTF-8"))
        irc.send(bytes(f"PRIVMSG {self.target} {msg}\n", "UTF-8"))

        irc.close()
