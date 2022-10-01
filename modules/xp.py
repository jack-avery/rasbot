# Channel watcher XP code TODO

from commands import BaseModule
import random
import requests
import sqlite3
import threading

XP_GRANT_FREQUENCY = 60.0
"""Amount of seconds between each grant."""

XP_GRANT_AMOUNT = 10
"""Amount of XP to grant per grant."""

XP_GRANT_VARY = True
"""Whether the XP granted should vary."""

XP_GRANT_VARIANCE = 5
"""How much the XP granted should vary, if it does. (+-)"""


class RepeatTimer(threading.Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)


class Module(BaseModule):
    helpmsg = "Get how many points a user has. Usage: xp <username>"

    def __init__(self, bot):
        BaseModule.__init__(self, bot)

        # init the sqlite3 connection
        self.db = sqlite3.connect(f"modules/_xp/{self.bot.channel_id}.db")

        # Create the table if it doesn't exist
        self.db.execute("""
        CREATE TABLE IF NOT EXISTS xp (
            name,
            amt,
            UNIQUE(name)
        )
        """)

        # Tick XP every XP_GRANT_FREQUENCY seconds
        timer = RepeatTimer(XP_GRANT_FREQUENCY, self.tick)
        timer.start()

    # Get viewerlist and do XP gain stuff here
    def tick(self):
        # Create a new connection for this thread
        tdb = sqlite3.connect(f"modules/_xp/{self.bot.channel_id}.db")

        users = requests.get(
            f"https://tmi.twitch.tv/group/user/{self.bot.channel[1:]}/chatters", headers=self.bot.auth.get_headers()).json()

        for utype in users['chatters']:
            for name in users['chatters'][utype]:
                # Resolve how much XP to grant to this user
                if XP_GRANT_VARY:
                    amt = XP_GRANT_AMOUNT + \
                        random.randint(-XP_GRANT_VARIANCE, XP_GRANT_VARIANCE)
                else:
                    amt = XP_GRANT_AMOUNT

                # Grant it to the user
                self.grant_xp(tdb, name, amt)

    def grant_xp(self, tdb, name, amt):
        """Grant `amt` xp to `name`, creating their entry if it doesn't exist.
        """
        with tdb as db:
            db.execute("INSERT OR IGNORE INTO xp VALUES(?,?)", (name, 0))
            db.execute(
                f"UPDATE xp SET amt = amt + {amt} WHERE name = \"{name}\"")

    def get_xp(self, name) -> int:
        """Return the amount of xp `name` has, or `0` if the user doesn't exist.
        """
        with self.db as db:
            cs = db.cursor()
            cs.execute(f"SELECT amt FROM xp WHERE name = \"{name}\"")
            res = cs.fetchone()
            return res[0] if res else 0

    def main(self):
        if not self.bot.cmdargs:
            return

        user = self.bot.cmdargs[0]
        if user.startswith('@'):
            user = user[1:]

        return f"{user} has {self.get_xp(user)} XP."
