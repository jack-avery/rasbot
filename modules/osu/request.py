# 'request' code for osu! requests. To get this to work:
# Fill out the fields in the config file in `userdata/[id]/modules/osu` with the strings found at the websites
#   ^ Ctrl+F 'default_config' to find the fields
# Create a command using cmd with %osu/request% in the response.

import irc
import re
from threading import Thread
import time

from src.commands import BaseModule, NO_MESSAGE_SIGNAL
from src.definitions import Author, Message, status_from_user_privilege

from modules.osu.helpers.api2 import OsuAPIv2Helper

OSU_LONG_RE = r"^https:\/\/osu.ppy.sh\/beatmapsets\/(\d+)\/?(?:#[a-z]+\/(\d+))?$"
OSU_SHORT_RE = r"^https:\/\/osu.ppy.sh\/b(?:eatmaps)?\/(\d+)$"

# See https://github.com/ppy/osu-api/wiki#response for more info
OSU_STATUSES = [
    "Pending",
    "Ranked",
    "Approved",
    "Qualified",
    "Loved",
    "Graveyard",
    "WIP",
]

OSU_MODES = ["Standard", "Taiko", "CTB", "Mania"]

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
    "map": lambda m: f"[https://osu.ppy.sh/b/{m['id']} {m['beatmapset']['artist']} - {m['beatmapset']['title']} [{m['version']}]]",
    "mapid": lambda m: m["id"],
    "mapsetid": lambda m: m["beatmapset_id"],
    "mapstatus": lambda m: str(m["status"]).capitalize(),
    # creator
    "creator": lambda m: f"[https://osu.ppy.sh/users/{m['user_id']} {m['beatmapset']['creator']}]",
    "creatorid": lambda m: m["user_id"],
    "creatorname": lambda m: m["creator"],
    # beatmap metadata
    "length": lambda m: f"{int(int(m['total_length']) / 60)}:{0 if int(m['total_length']) % 60 < 10 else ''}{int(m['total_length']) % 60}",
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
    "requesterstatus": lambda m: status_from_user_privilege(m["sender"].priv),
    "mods": lambda m: m["mods"],
}


class OsuRequestsIRCBot(irc.bot.SingleServerIRCBot):
    def __init__(self, user, server, port=6667, password=None, log_i=None):
        irc.bot.SingleServerIRCBot.__init__(
            self, [(server, port, password)], user, user
        )
        self.user = user
        self.log_i = log_i

    def on_welcome(self, c, e):
        self.log_i(f"osu! IRC Connected as {self.user}")

    def send_message(self, msg: str):
        self.connection.privmsg(self.user, msg)


class Module(BaseModule):
    helpmsg = 'Request an osu! beatmap to be played. Usage: request <beatmap link> <+mods?> (mods: "request submode" to toggle submode)'

    default_config = {
        # Your osu! ID. Go to your profile on the website and this should be in the URL.
        "osu_trgt_id": "",
        # Your osu! IRC password. Get this from https://old.ppy.sh/p/irc.
        "osu_irc_pwd": "",
        # The format of the message to send alongside. See MESSAGE_OPTIONS for keys.
        # Enclose keys in % as you would a module in a command.
        "message_format": "%requester% (%requesterstatus%) requested: %map% %mods% (%length% @ %bpm%BPM, %stars%*, by %creator%)",
        # Per-user cooldown for requests (in seconds)
        "cd_per_user": 0,
        # Whether or not ALL messages posted in chat should be parsed for beatmap links.
        "parse_all_messages": True,
        # Whether or not to inform user of requests handled using parse_all_messages.
        "respond_all_messages": True,
    }

    consumes = 2

    def __init__(self, bot, name):
        BaseModule.__init__(self, bot, name)

        # set up
        self.cooldown = self.cfg_get("cd_per_user")
        self.author_cds = dict()

        # get api v2 helper
        self.api_helper = OsuAPIv2Helper(
            f"{self._bot.channel_id}/modules/osu/helpers/api2.txt"
        )

        # compile mapID regex
        self.beatmap_re = re.compile(OSU_LONG_RE)
        self.b_re = re.compile(OSU_SHORT_RE)

        # resolve username
        self.username = self.resolve_username(self.cfg_get("osu_trgt_id"))

        # create IRC bot
        if self.username:
            self.osu_irc_bot = OsuRequestsIRCBot(
                self.username,
                "irc.ppy.sh",
                password=self.cfg_get("osu_irc_pwd"),
                log_i=self.log_i,
            )

            self.osu_irc_bot_thread = Thread(target=self.osu_irc_bot.start)
            self.osu_irc_bot_thread.daemon = True
            self.osu_irc_bot_thread.start()

    def resolve_username(self, id: (str | int)) -> str | None:
        """Resolves a users' osu! username from their ID.
        :param id: The ID of the osu! user to resolve the name for.
        :return: The name of the user, or `None` if the resolution failed.
        """
        self.log_d(f"resolving osu! username for ID {id}")

        name = self.api_helper.get_username(id)
        if not name:
            return None

        # replace ' ' with '_'
        name = name["username"].replace(" ", "_")
        self.log_d(f"resolved to {name}")
        return name

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

        return self.process_request(message.author, args)

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
                response = self.process_request(message.author, args)
                if self.cfg_get("respond_all_messages"):
                    # TODO: make this use command response format from a request command?
                    self._bot.send_message(f"@{message.author.name} > {response}")

                # only process first map
                return

    def process_request(self, author: Author, args):
        # do not continue if either username or target failed to resolve
        if not self.username:
            return (
                "Your username could not be resolved. Please check/fix configuration."
            )

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

        # use second arg as mods
        mods = ""
        if len(args) > 1:
            mods = self.generate_mods_string(args[1].upper())

        # get map info; use full re first as it's more common
        if self.beatmap_re.match(req):
            # returns [()]? oh well, grab [0] so we have ()
            ids = self.beatmap_re.findall(req)[0]

            # if mapid isn't empty use it
            if ids[1]:
                # beatmap
                id = ids[1]
                self.log_d(f"retrieving osu map info for beatmap id {id}")
                map = self.api_helper.get_beatmap(id)

            # if mapid is empty use mapsetid
            else:
                # beatmapset
                id = ids[0]
                self.log_d(f"retrieving top diff info for beatmapset id {id}")
                mapset = self.api_helper.get_beatmapset(id)
                maps = mapset["beatmaps"]
                # sort mapset descending by difficulty so req[0] gives top diff
                maps.sort(key=lambda m: m["difficulty_rating"], reverse=True)
                map = maps[0]
                # set map mapset to mapset for use within formatting
                map["beatmapset"] = mapset

        # use short re? (osu.ppy.sh/b/id)
        elif self.b_re.match(req):
            id = self.b_re.findall(req)[0]
            self.log_d(f"retrieving osu map info for beatmap id {id}")
            map = self.api_helper.get_beatmap(id)

        # give up
        else:
            return "Could not resolve beatmap link format."

        if not map:
            return "Could not retrieve beatmap information."

        # add request mods to map dict and format the message
        map["mods"] = mods
        map["sender"] = author
        message = self.format_message(map)

        # send message, set cooldown and inform requester
        self.send_osu_message(message)
        self.author_cds[author.uid] = time.time()

        return f"{map['beatmapset']['artist']} - {map['beatmapset']['title']} | Request sent!"

    def send_osu_message(self, msg: str):
        """Send `msg` as an osu! message to `target` as `username`
        :param msg: The message to send
        """
        self.log_d(f"sending osu! message to {self.username}: '{msg}'")

        self.osu_irc_bot.send_message(msg)
