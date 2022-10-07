# Chatter watchtime XP module.
# You can tweak the frequency of granting XP and the ranges to grant below.
# "Levels" may be implemented eventually, but assume it will be left as-is.

from commands import BaseModule
import os
import random
import requests
import sqlite3
import threading

DEFAULT_CONFIG = {
    # Amount of seconds between each grant. Default is 60 (1 minute).
    "xp_grant_frequency": 60,
    # Amount (min, max) to grant to inactive users. Default is (1, 1).
    "xp_inactive_range": [1, 1],
    # Amount (min, max) to grant to active users. Default is (2, 3).
    "xp_active_range": [2, 3],
    "omit_users": []
}


class RepeatTimer(threading.Timer):
    # See https://stackoverflow.com/a/48741004
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)


class Module(BaseModule):
    helpmsg = f"Get how much XP a user has or see the top 3. Usage: xp <username/top>"

    def __init__(self, bot, name):
        BaseModule.__init__(self, bot, name, DEFAULT_CONFIG)

        # resolve path
        self.db_path = f"modules/xp_store/{self.bot.channel_id}.db"

        # init the sqlite3 connection
        try:
            self.db = sqlite3.connect(self.db_path)

        except sqlite3.OperationalError:
            # Make folder and reattempt init
            os.mkdir("modules/xp_store")
            self.db = sqlite3.connect(self.db_path)

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
        timer = RepeatTimer(self.cfg["xp_grant_frequency"], self.tick)
        timer.start()

    # Get viewerlist and do XP gain logic
    def tick(self):
        # Create a new connection for this thread
        thread_db = sqlite3.connect(self.db_path)

        # TODO replace this if the API ever becomes outdated
        users = requests.get(
            f"https://tmi.twitch.tv/group/user/{self.bot.channel_name}/chatters", headers=self.bot.auth.get_headers()).json()

        # Prevent streamer from earning watchtime XP on their own stream
        users['chatters'].pop('broadcaster')

        # Give XP to each user
        for utype in users['chatters']:
            for user in users['chatters'][utype]:
                if user.lower() in self.cfg["omit_users"]:
                    continue

                # Resolve how much XP to grant to this user
                if (user in self.active_users):
                    amt = random.randint(
                        self.cfg['xp_active_range'][0], self.cfg['xp_active_range'][1])
                else:
                    amt = random.randint(
                        self.cfg['xp_inactive_range'][0], self.cfg['xp_inactive_range'][1])

                # Grant it to the user
                thread_db.execute(
                    "INSERT OR IGNORE INTO xp VALUES(?,?)", (user, 0))
                thread_db.execute(
                    f"UPDATE xp SET amt = amt + {amt} WHERE user = \"{user}\"")

        # Commit XP modifications and clear active users for the next window.
        thread_db.commit()

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

    def mod_user(self, action, user, arg):
        """Perform an action on a user.
        """
        with self.db as db:
            if action == "purge":
                db.execute(f"UPDATE xp SET amt = 0 WHERE user = \"{user}\"")
                msg = f"Reset {user}'s to 0."

            elif action == "set":
                try:
                    arg = int(arg)
                except ValueError:
                    return f"Please provide an amount to set the user's XP to."

                db.execute(
                    f"UPDATE xp SET amt = {arg} WHERE user = \"{user}\"")
                msg = f"Set {user}'s XP to {arg}."

            elif action == "ban":
                if user in self.cfg["omit_users"]:
                    return f"User {user} is already banned from XP."

                db.execute(f"UPDATE xp SET amt = 0 WHERE user = \"{user}\"")
                self.cfg["omit_users"].append(user.lower())
                self.save_config()
                msg = f"Set {user}'s XP to 0 and banished from earning."

            elif action == "unban":
                if user not in self.cfg["omit_users"]:
                    return f"User {user} is not banned from XP."

                self.cfg["omit_users"].remove(user.lower())
                self.save_config()
                msg = f"Removed {user} from XP banished users."

            db.commit()
        return msg

    def main(self):
        if not self.bot.cmdargs:
            arg = self.bot.author_name
        else:
            arg = self.bot.cmdargs[0]

        # Show top 3
        if arg == "top":
            return self.get_top()

        # XP moderation tools
        if arg == "mod":
            if not self.bot.author_ismod:
                return "You must be a moderator to do that."

            try:
                args = self.bot.cmdargs[1:]

                action = args[0]
                user = args[1]

                try:
                    arg = args[2]
                except IndexError:
                    arg = None

                # Resolve user
                if user.startswith('@'):
                    user = user[1:]

                return self.mod_user(action, user, arg)

            except IndexError:
                return "Please provide an action and a user. Valid actions are: purge, set <amount>, ban, unban."

        # Resolve user and show stats
        if arg.startswith('@'):
            arg = arg[1:]

        return self.get_user(arg)

    def on_pubmsg(self):
        # Add this user to the active users list.
        if not self.bot.author_name in self.active_users:
            self.active_users.append(self.bot.author_name)
