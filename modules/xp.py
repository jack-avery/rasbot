# Chatter watchtime XP module.
# You can tweak the frequency of granting XP and the ranges to grant below.
# "Levels" may be implemented eventually, but assume it will be left as-is.

from commands import BaseModule
import random
import requests
import sqlite3
import threading

XP_GRANT_FREQUENCY = 180.0
"""Amount of seconds between each grant. Default is 180 (3 minutes)."""

XP_INACTIVE_RANGE = (2, 2)
"""Amount (min, max) to grant to inactive users. Default is (2, 2)."""

XP_ACTIVE_RANGE = (2, 5)
"""Amount (min, max) to grant to active users. Default is (2, 5)."""


class RepeatTimer(threading.Timer):
    # See https://stackoverflow.com/a/48741004
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)


class Module(BaseModule):
    helpmsg = "Get how much XP a user has or see the top 3. Usage: xp <username/top>"

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

    # Get viewerlist and do XP gain logic
    def tick(self):
        # Create a new connection for this thread
        thread_db = sqlite3.connect(f"modules/_xp/{self.bot.channel_id}.db")

        users = requests.get(
            f"https://tmi.twitch.tv/group/user/{self.bot.channel[1:]}/chatters", headers=self.bot.auth.get_headers()).json()

        for utype in users['chatters']:
            for user in users['chatters'][utype]:
                # Resolve how much XP to grant to this user
                if (user in self.active_users):
                    amt = random.randint(
                        XP_ACTIVE_RANGE[0], XP_ACTIVE_RANGE[1])
                else:
                    amt = random.randint(
                        XP_INACTIVE_RANGE[0], XP_INACTIVE_RANGE[1])

                # Grant it to the user
                thread_db.execute(
                    "INSERT OR IGNORE INTO xp VALUES(?,?)", (user, 0))
                thread_db.execute(
                    f"UPDATE xp SET amt = amt + {amt} WHERE user = \"{user}\"")

        # Clear active users for this window.
        self.active_users.clear()

    def get_top(self):
        """Return the top 3 XP holders.
        """
        with self.db as db:
            cs = db.cursor()
            cs.execute(f"SELECT user,amt FROM xp ORDER BY amt DESC")
            res = cs.fetchmany(3)

            return " | ".join([f"{r[0]}: {r[1]}" for r in res])

    def get_user(self, user):
        """Return the user, their XP, and position.
        """
        with self.db as db:
            cs = db.cursor()

            # Getting their position
            all = tuple(map(lambda x: x[0], cs.execute(
                'SELECT user FROM xp ORDER BY amt DESC').fetchall()))
            try:
                pos = all.index(user) + 1
            except ValueError:
                # If finding their index in the sorted list fails assume they don't exist.
                return f"User {user} has no tracked XP."

            cs.execute(f"SELECT amt FROM xp WHERE user = \"{user}\"")
            xp = cs.fetchone()[0]

        return f"{user} is #{pos} with {xp} XP."

    def main(self):
        if not self.bot.cmdargs:
            return "Please provide a user, or 'top' to see the top 3."

        arg = self.bot.cmdargs[0]

        # Show top 3
        if arg == "top":
            return self.get_top()

        # Resolve user and show stats
        if arg.startswith('@'):
            arg = arg[1:]

        return self.get_user(arg)

    def on_pubmsg(self):
        # Add this user to the active users list.
        if not self.bot.author_name in self.active_users:
            self.active_users.append(self.bot.author_name)
