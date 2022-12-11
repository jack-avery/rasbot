# 'request' code for osu! requests. To get this to work:
# Fill out the fields in the config file with the strings found at the websites
# Create a command using cmdadd with &request& as the response.

# TODO refactor this to use new osu! API v2 once it drops with Lazer

import socket
import requests
import re
from commands import BaseModule
from definitions import MODULE_MENTION_REGEX

OSU_BEATMAPSETID_RE = r'^https:\/\/osu.ppy.sh\/beatmapsets\/[\w#]+\/(\d+)$'
OSU_B_RE = r'^https:\/\/osu.ppy.sh\/b(?:eatmaps)?\/(\d+)$'

OSU_BEATMAPSET_RE = r'^https:\/\/osu.ppy.sh\/beatmapsets\/(\d+)$'

# See https://github.com/ppy/osu-api/wiki#response for more info
OSU_STATUSES = ["Pending", "Ranked", "Approved",
                "Qualified", "Loved", "Graveyard", "WIP"]

OSU_MODES = ["Standard", "Taiko", "CTB", "Mania"]

# TODO update this with lazer mods when the time comes
OSU_MODS = ["EZ", "NF", "HT", "HR", "SD", "PF",
            "DT", "NC", "HD", "FL", "RX", "AP", "SO", "V2"]

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

    default_config = {
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

    def __init__(self, bot, name):
        BaseModule.__init__(self, bot, name)

        # compile mapID regex
        beatmapsetid_re = re.compile(OSU_BEATMAPSETID_RE)
        b_re = re.compile(OSU_B_RE)

        # compile mapsetID regex
        beatmapset_re = re.compile(OSU_BEATMAPSET_RE)

        # create regex lists for easy iterating
        self.beatmap_res = [beatmapsetid_re, b_re]
        self.beatmapset_res = [beatmapset_re]

        # resolve usernames
        self.username = self.resolve_username(self.cfg_get('osu_user_id'))

        # if the target is the same as the user, just copy it over instead of a second call
        if self.cfg_get('osu_user_id') == self.cfg_get('osu_trgt_id'):
            self.log_d("username same as target, skipping extra api call")
            self.target = self.username
        else:
            self.target = self.resolve_username(self.cfg_get('osu_trgt_id'))

    def resolve_username(self, id):
        """Resolves a users' osu! username from their ID.
        """
        self.log_d(f"resolving osu! username for ID {id}")
        req = None
        try:
            req = requests.get(
                f"https://osu.ppy.sh/api/get_user?u={id}&k={self.cfg_get('osu_api_key')}")

            # replace ' ' with '_'
            name = req.json()[0]['username'].replace(" ", "_")
            self.log_d(f"resolved to {name}")

            return name

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

    def generate_mods_string(self, mods: str):
        """Convert `mods` into a more conventional format, and verify that they are real osu! mods."""
        self.log_d(f"resolving mods from string {mods}")
        # strip + for logic
        if mods.startswith('+'):
            mods = mods[1:]

        # remove any possible ,
        mods = mods.replace(',', '')

        # split into separate mods
        mods = [mods[i:i+2] for i in range(0, len(mods), 2)]

        # add mods to modstring; prevent duplicates and invalid mods
        modstring = '+'
        for mod in mods:
            if mod in OSU_MODS and mod not in modstring:
                modstring += mod + ','

        self.log_d(modstring)
        return modstring

    def format_message(self, map):
        """Format map information for `map` using `message_format` from the config.

        :param map: The map object as returned from the osu! API"""
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
        # do not continue if either username or target failed to resolve
        if not self.username or not self.target:
            return "A username (either self or target) could not be resolved. Please check/fix configuration."

        # do not continue if no args are provided
        if not self.bot.cmdargs:
            return "Provide a map to request."

        # use first arg as request
        req = self.bot.cmdargs[0].lower()

        # use second arg as mods
        mods = ''
        if len(self.bot.cmdargs) > 1:
            mods = self.generate_mods_string(self.bot.cmdargs[1].upper())

        # resolve mapID
        is_id = False
        id = False
        for beatmap_re in self.beatmap_res:
            if beatmap_re.match(req):
                id = beatmap_re.findall(req)[0]
                is_id = True
                break

        # if couldn't get mapid from mapID res, use mapsetID
        if not id:
            for beatmapset_re in self.beatmapset_res:
                if beatmapset_re.match(req):
                    id = beatmapset_re.findall(req)[0]
                    break

        # if couldn't get mapid from either mapID or mapsetID res, give up
        if not id:
            return "Could not resolve beatmap link format."

        # retrieve beatmap information
        if is_id:
            # beatmap
            self.log_d(f"retrieving osu map info for beatmap id {id}")
            req = requests.get(
                f"https://osu.ppy.sh/api/get_beatmaps?b={id}&k={self.cfg_get('osu_api_key')}").json()
        else:
            # beatmapset
            self.log_d(f"retrieving top diff info for beatmapset id {id}")
            req = requests.get(
                f"https://osu.ppy.sh/api/get_beatmaps?s={id}&k={self.cfg_get('osu_api_key')}").json()
            # sort mapset descending by difficulty so req[0] gives top diff
            req.sort(key=lambda r: r['difficultyrating'], reversed=True)

        try:
            map = req[0]
        except IndexError:
            self.log_d(f"failed!")
            return "Could not retrieve beatmap information."

        # add request mods to map dict and format the message
        map['mods'] = mods
        message = self.format_message(map)

        # send message and inform requester
        self.send_osu_message(
            f"{self.bot.author_name} requested: {message}")

        return "Request sent!"

    def send_osu_message(self, msg):
        self.log_d(
            f"sending osu! message to {self.target} as {self.username}: '{msg}'")

        # create IRC socket and connect to irc.ppy.sh
        irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        irc.connect(('irc.ppy.sh', 6667))

        # send message headers and message
        irc.send(bytes(f"USER {self.username}\n", "UTF-8"))
        irc.send(bytes(f"PASS {self.cfg_get('osu_irc_pwd')}\n", "UTF-8"))
        irc.send(bytes(f"NICK {self.username}\n", "UTF-8"))
        irc.send(bytes(f"PRIVMSG {self.target} {msg}\n", "UTF-8"))

        # close socket so we don't leak anything
        irc.close()
