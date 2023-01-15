# 'request' code for osu! requests. To get this to work:
# Fill out the fields in the config file in `userdata/[id]/modules/osu` with the strings found at the websites
#   ^ Ctrl+F 'default_config' to find the fields
# Create a command using cmd with %request% in the response.

# TODO refactor this to use new osu! API v2 once it drops with Lazer

import irc
import requests
import re
from threading import Thread
import time

from src.commands import BaseModule, NO_MESSAGE_SIGNAL
from src.definitions import Author,\
    Message

OSU_API_CHAT_URL = "https://osu.ppy.sh/api/v2/chat/new"

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

MESSAGE_OPT_RE = re.compile(r'(%([\/a-z0-9_]+)%)')

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
    "combo": lambda m: m['max_combo'],
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
    "requester": lambda m: m['sender'].name,
    "requesterstatus": lambda m: m['sender'].user_status(),
    "mods": lambda m: m['mods']
}


class OsuRequestsIRCBot(irc.bot.SingleServerIRCBot):
    def __init__(self, user, target, server, port=6667, password=None, log_i=None):
        irc.bot.SingleServerIRCBot.__init__(
            self, [(server, port, password)], user, user)

        self.target = target
        self.user = user
        self.log_i = log_i

    def on_welcome(self, c, e):
        self.log_i(f"osu! IRC Connected as {self.user}")

    def send_message(self, msg: str):
        self.connection.privmsg(self.target, msg)


class Module(BaseModule):
    helpmsg = 'Request an osu! beatmap to be played. Usage: request <beatmap link> <+mods?> (mods: "request submode" to toggle submode)'

    default_config = {
        # Your osu! ID. Go to your profile on the website and this should be in the URL.
        "osu_user_id": "",
        # Your osu! API key. Get this from https://old.ppy.sh/p/api.
        "osu_api_key": "",
        # Your osu! IRC password. Get this from https://old.ppy.sh/p/irc.
        "osu_irc_pwd": "",
        # ID of the user that the request should go to.
        "osu_trgt_id": "",
        # The format of the message to send alongside. See MESSAGE_OPTIONS for keys.
        # Enclose keys in % as you would a module in a command.
        "message_format": "%requester% (%requesterstatus%) requested: %map% %mods% (%length% @ %bpm%BPM, %stars%*, by %creator%)",
        # Per-user cooldown for requests (in seconds)
        "cd_per_user": 0,
        # Whether or not requests should be for Subscribers, VIPs, and Mods only
        "submode": False,
        # Whether or not ALL messages posted in chat should be parsed for beatmap links.
        "parse_all_messages": True,
    }

    consumes = 2

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

        self.cooldown = self.cfg_get('cd_per_user')
        self.author_cds = dict()

        # resolve usernames
        self.username = self.resolve_username(self.cfg_get('osu_user_id'))

        # if the target is the same as the user, just copy it over instead of a second call
        if self.cfg_get('osu_user_id') == self.cfg_get('osu_trgt_id'):
            self.log_d("username same as target, skipping extra api call")
            self.target = self.username
        else:
            self.target = self.resolve_username(self.cfg_get('osu_trgt_id'))

        # create IRC bot
        if self.username and self.target:
            self.osu_irc_bot = OsuRequestsIRCBot(
                self.username, self.target, 'irc.ppy.sh', password=self.cfg_get('osu_irc_pwd'), log_i=self.log_i)

            self.osu_irc_bot_thread = Thread(target=self.osu_irc_bot.start)
            self.osu_irc_bot_thread.daemon = True
            self.osu_irc_bot_thread.start()

    def resolve_username(self, id: (str | int)) -> (str | None):
        """Resolves a users' osu! username from their ID.

        :param id: The ID of the osu! user to resolve the name for.
        :return: The name of the user, or `None` if the resolution failed.
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

        except (IndexError, KeyError):
            self.log_e(
                f"could not resolve osu! username for id:{id}. API key may be invalid. (response code {req.status_code})"
            )
            return None

    def generate_mods_string(self, mods: str) -> str:
        """Convert `mods` into a more conventional format, and verify that they are real osu! mods.

        :param mods: The string given by the user representing the mods selection.
        :return: The formatted and verified string of valid osu! mods.
        """
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

        if modstring == '+':
            return ''

        self.log_d(modstring)
        return modstring

    def format_message(self, map) -> str:
        """Format map information for `map` using `message_format` from the config.

        :param map: The map object as returned from the osu! API
        :return: The message to send as formatted using `message_format`
        """
        message = self.cfg_get('message_format')

        for flag, option in MESSAGE_OPT_RE.findall(message):
            if option not in MESSAGE_OPTIONS:
                self.log_e(
                    f"config error: message_format uses invalid key '{option}'")
                continue

            message = message.replace(
                flag,
                str(MESSAGE_OPTIONS[option](map))
            )

        return message

    def main(self, message: Message):
        args = self.get_args(message)

        fail_msg = self.process_request(message.author, args)

        if fail_msg:
            return fail_msg

        return "Request sent!"

    def on_pubmsg(self, message: Message):
        if not self.cfg_get('parse_all_messages'):
            return

        # do not parse again if using a command
        if message.cmd:
            return

        words = message.text_raw.split(' ')
        for i, word in enumerate(words):
            if "osu.ppy.sh" in word:
                args = words[i:]
                self.process_request(message.author, args)

    def process_request(self, author: Author, args):
        # do not continue if either username or target failed to resolve
        if not self.username or not self.target:
            return "A username (either self or target) could not be resolved. Please check/fix configuration."

        # prevent normal users from requesting in submode
        if self.cfg_get('submode') and not (author.is_mod or author.is_sub or author.is_vip):
            return NO_MESSAGE_SIGNAL

        # exit early if user requested within cooldown
        if author.uid in self.author_cds:
            time_passed = time.time() - self.author_cds[author.uid]
            if time_passed < self.cooldown:
                self.log_d(
                    f"user {author.name} requested while still on cd; ignoring")
                return NO_MESSAGE_SIGNAL

        # do not continue if no args are provided
        if not args:
            return "Provide a map to request."

        # use first arg as request (or submode toggle)
        req = args[0].lower()

        # allow mods to toggle submode
        if req == 'submode' and author.is_mod:
            t = not self.cfg_get('submode')
            self.cfg_set('submode', t)
            if t:
                return "Submode enabled"
            else:
                return "Submode disabled"

        # use second arg as mods
        mods = ''
        if len(args) > 1:
            mods = self.generate_mods_string(args[1].upper())

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
            req.sort(key=lambda r: r['difficultyrating'], reverse=True)

        try:
            map = req[0]
        except IndexError:
            self.log_e(f"failed to get info for id/setid {id}")
            return "Could not retrieve beatmap information."

        # add request mods to map dict and format the message
        map['mods'] = mods
        map['sender'] = author
        message = self.format_message(map)

        # send message, set cooldown and inform requester
        self.send_osu_message(message)
        self.author_cds[author.uid] = time.time()

        return False

    def send_osu_message(self, msg: str):
        """Send `msg` as an osu! message to `target` as `username`

        :param msg: The message to send
        """
        self.log_d(
            f"sending osu! message to {self.target} as {self.username}: '{msg}'")

        self.osu_irc_bot.send_message(msg)
