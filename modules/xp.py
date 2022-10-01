from commands import BaseModule
import random
import requests
import sqlite3
import threading

XP_GRANT_FREQUENCY = 180.0
"""Amount of seconds between each grant. Default is 180 (3 minutes)."""

XP_GRANT_BASE = 2
"""Base amount of XP to grant per grant. Default is 2."""

XP_GRANT_REWARD_ACTIVITY = True
"""Whether the XP granted should be increased for active chatters. Default is True."""

XP_GRANT_REWARD_AMOUNT = 3
"""Maximum amount of extra XP to give to active users. Default is 3."""


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
            user,
            amt,
            UNIQUE(user)
        )
        """)

        # Create active users array for activity bonus
        self.active_users = []

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
            for user in users['chatters'][utype]:
                # Resolve how much XP to grant to this user
                amt = XP_GRANT_BASE
                if (user in self.active_users) and XP_GRANT_REWARD_ACTIVITY:
                    amt += random.randint(1, XP_GRANT_REWARD_AMOUNT)

                # Grant it to the user
                self.grant_xp(tdb, user, amt)

        # Clear active users for this window.
        self.active_users.clear()

    def grant_xp(self, tdb, user, amt):
        """Grant `amt` xp to `user`, creating their entry if it doesn't exist.
        """
        with tdb as db:
            db.execute("INSERT OR IGNORE INTO xp VALUES(?,?)", (user, 0))
            db.execute(
                f"UPDATE xp SET amt = amt + {amt} WHERE user = \"{user}\"")

    def get_xp(self, user) -> int:
        """Return the amount of xp `user` has, or `0` if the user doesn't exist.
        """
        with self.db as db:
            cs = db.cursor()
            cs.execute(f"SELECT amt FROM xp WHERE user = \"{user}\"")
            res = cs.fetchone()
            return res[0] if res else 0

    def main(self):
        if not self.bot.cmdargs:
            return

        user = self.bot.cmdargs[0]
        if user.startswith('@'):
            user = user[1:]

        return f"{user} has {self.get_xp(user)} XP."

    def on_pubmsg(self):
        # Add this user to the active users list.
        if not self.bot.author_name in self.active_users:
            self.active_users.append(self.bot.author_name)
