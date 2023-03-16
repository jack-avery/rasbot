# 'request_v2' code for osu! requests using the v2 API instead of IRC.

from src.commands import BaseModule, NO_MESSAGE_SIGNAL
from src.definitions import Author, Message

import re
import time

from helpers.api2 import OsuAPIv2Helper

OSU_BEATMAPSETID_RE = r"^https:\/\/osu.ppy.sh\/beatmapsets\/[\w#]+\/(\d+)$"
OSU_B_RE = r"^https:\/\/osu.ppy.sh\/b(?:eatmaps)?\/(\d+)$"

OSU_BEATMAPSET_RE = r"^https:\/\/osu.ppy.sh\/beatmapsets\/(\d+)$"

# TODO update this with lazer mods when the time comes
OSU_MODS = [
    "EZ",
    "NF",
    "HT",
    "HR",
    "SD",
    "PF",
    "DT",
    "NC",
    "HD",
    "FL",
    "RX",
    "AP",
    "SO",
    "V2",
]

MESSAGE_OPT_RE = re.compile(r"(%([\/a-z0-9_]+)%)")

MESSAGE_OPTIONS = {
    # web
    "map": lambda m: f"[{m['url']} {m['beatmapset']['artist']} - {m['beatmapset']['title']} [{m['version']}]]",
    "mapid": lambda m: m["id"],
    "mapsetid": lambda m: m["beatmapset_id"],
    "mapstatus": lambda m: str(m["status"]).capitalize(),
    # creator
    "creator": lambda m: f"[https://osu.ppy.sh/users/{m['user_id']} {m['beatmapset']['creator']}]",
    "creatorid": lambda m: m["user_id"],
    "creatorname": lambda m: m["creator"],
    # beatmap metadata
    "length": lambda m: f"{int(int(m['total_length']) / 60)}:{int(m['total_length']) % 60}",
    "bpm": lambda m: m["bpm"],
    "combo": lambda m: m["max_combo"],
    "stars": lambda m: m["difficulty_rating"],
    "cs": lambda m: m["cs"],
    "od": lambda m: m["accuracy"],
    "ar": lambda m: m["ar"],
    "hp": lambda m: m["drain"],
    "gamemode": lambda m: m["mode"],
    # song info
    "song": lambda m: f"{m['beatmapset']['artist']} - {m['beatmapset']['title']}",
    "songartist": lambda m: m["beatmapset"]["artist"],
    "songartistunicode": lambda m: m["beatmapset"]["artist_unicode"],
    "songtitle": lambda m: m["beatmapset"]["title"],
    "songtitleunicode": lambda m: m["beatmapset"]["title_unicode"],
    # requests specific additions
    "requester": lambda m: m["sender"].name,
    "requesterstatus": lambda m: m["sender"].user_status(),
    "mods": lambda m: m["mods"],
}


class Module(BaseModule):
    helpmsg = 'Request an osu! beatmap to be played. Usage: request <beatmap link> <+mods?> (mods: "request submode" to toggle submode)'

    default_config = {
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

        # get api v2 helper
        self.api_helper = OsuAPIv2Helper(self._bot.channel_id)

        # compile mapID regex
        beatmapsetid_re = re.compile(OSU_BEATMAPSETID_RE)
        b_re = re.compile(OSU_B_RE)

        # compile mapsetID regex
        beatmapset_re = re.compile(OSU_BEATMAPSET_RE)

        # create regex lists for easy iterating
        self.beatmap_res = [beatmapsetid_re, b_re]
        self.beatmapset_res = [beatmapset_re]

        self.cooldown = self.cfg_get("cd_per_user")
        self.author_cds = dict()

    def generate_mods_string(self, mods: str) -> str:
        """Convert `mods` into a more conventional format, and verify that they are real osu! mods.

        :param mods: The string given by the user representing the mods selection.
        :return: The formatted and verified string of valid osu! mods.
        """
        self.log_d(f"resolving mods from string {mods}")
        # strip + for logic
        if mods.startswith("+"):
            mods = mods[1:]

        # remove any possible ,
        mods = mods.replace(",", "")

        # split into separate mods
        mods = [mods[i : i + 2] for i in range(0, len(mods), 2)]

        # add mods to modstring; prevent duplicates and invalid mods
        modstring = "+"
        for mod in mods:
            if mod in OSU_MODS and mod not in modstring:
                modstring += mod + ","

        if modstring == "+":
            return ""

        self.log_d(modstring)
        return modstring

    def format_message(self, map) -> str:
        """Format map information for `map` using `message_format` from the config.

        :param map: The map object as returned from the osu! API
        :return: The message to send as formatted using `message_format`
        """
        message = self.cfg_get("message_format")

        for flag, option in MESSAGE_OPT_RE.findall(message):
            if option not in MESSAGE_OPTIONS:
                self.log_e(f"config error: message_format uses invalid key '{option}'")
                continue

            message = message.replace(flag, str(MESSAGE_OPTIONS[option](map)))

        return message

    def main(self, message: Message):
        args = self.get_args(message)

        fail_msg = self.process_request(message.author, args)

        if fail_msg:
            return fail_msg

        return "Request sent!"

    def on_pubmsg(self, message: Message):
        if not self.cfg_get("parse_all_messages"):
            return

        # do not parse again if using a command
        if message.cmd:
            return

        words = message.text_raw.split(" ")
        for i, word in enumerate(words):
            if "osu.ppy.sh" in word:
                args = words[i:]
                self.process_request(message.author, args)

    def process_request(self, author: Author, args):
        # prevent normal users from requesting in submode
        if self.cfg_get("submode") and not (
            author.is_mod or author.is_sub or author.is_vip
        ):
            return NO_MESSAGE_SIGNAL

        # exit early if user requested within cooldown
        if author.uid in self.author_cds:
            time_passed = time.time() - self.author_cds[author.uid]
            if time_passed < self.cooldown:
                self.log_d(f"user {author.name} requested while still on cd; ignoring")
                return NO_MESSAGE_SIGNAL

        # do not continue if no args are provided
        if not args:
            return "Provide a map to request."

        # use first arg as request (or submode toggle)
        req = args[0].lower()

        # allow mods to toggle submode
        if req == "submode" and author.is_mod:
            t = not self.cfg_get("submode")
            self.cfg_set("submode", t)
            if t:
                return "Submode enabled"
            else:
                return "Submode disabled"

        # use second arg as mods
        mods = ""
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
            map = self.api_helper.get_beatmap(id)
        else:
            # beatmapset
            self.log_d(f"retrieving top diff info for beatmapset id {id}")
            maps = self.api_helper.get_beatmapset(id)
            # sort mapset descending by difficulty so req[0] gives top diff
            maps.sort(key=lambda m: m["difficultyrating"], reverse=True)
            map = req[0]

        if not map:
            return "Could not get beatmap information."

        # add request mods to map dict and format the message
        map["mods"] = mods
        map["sender"] = author
        message = self.format_message(map)

        # send message, set cooldown and inform requester
        self.send_osu_message(message)
        self.author_cds[author.uid] = time.time()

        return False

    def send_osu_message(self, msg: str):
        """Send `msg` as an osu! message to `target`

        :param msg: The message to send
        """
        uid = self.cfg_get("osu_trgt_id")
        if not uid:
            self.log_e("configure your user id first before using requests!")
            return

        self.log_d(f"sending osu! message: '{msg}'")

        self.api_helper.send_message(msg, uid)
