# Chatter watchtime XP module.
# You can tweak the frequency of granting XP and the ranges to grant in the config file.
# "Levels" may be implemented eventually, but assume it will be left as-is.

from src.commands import BaseModule
from src.config import BASE_CONFIG_PATH
from src.definitions import Message

import os
import random
import requests
import sqlite3
import threading


class RepeatTimer(threading.Timer):
    # See https://stackoverflow.com/a/48741004
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)


class Module(BaseModule):
    helpmsg = f"Get how much XP a user has or see the top 3. Usage: xp <username/top>"

    default_config = {
        # Amount of seconds between each grant. Default is 60 (1 minute).
        "xp_grant_frequency": 60,
        # Amount (min, max) to grant to inactive users. Default is (1, 1).
        "xp_inactive_range": [1, 1],
        # Amount (min, max) to grant to active users. Default is (2, 3).
        "xp_active_range": [2, 3],
        "omit_users": []
    }

    consumes = 5

    def __init__(self, bot, name):
        BaseModule.__init__(self, bot, name)

        # resolve path
        self.db_path = f"{BASE_CONFIG_PATH}/{self._bot.channel_id}/modules/xp.db"

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
        self.timer = RepeatTimer(self.cfg_get("xp_grant_frequency"), self.tick)
        self.timer.start()

    def __del__(self):
        self.timer.cancel()

    # Get viewerlist and do XP gain logic
    def tick(self):
        self.log_d(f"running XP grant logic")
        # Create a new connection for this thread
        thread_db = sqlite3.connect(self.db_path)

        # TODO replace this if the API ever becomes outdated
        users = requests.get(
            f"https://tmi.twitch.tv/group/user/{self._bot.channel_name}/chatters", headers=self._bot.auth.get_headers()).json()

        # Prevent streamer from earning watchtime XP on their own stream
        users['chatters'].pop('broadcaster')

        # Give XP to each user
        for utype in users['chatters']:
            for user in users['chatters'][utype]:
                user = user.lower()
                if user in self.cfg_get("omit_users"):
                    continue

                # Resolve how much XP to grant to this user
                active_range = self.cfg_get('xp_active_range')
                inactive_range = self.cfg_get('xp_inactive_range')
                if (user in self.active_users):
                    amt = random.randint(
                        active_range[0], active_range[1])
                else:
                    amt = random.randint(
                        inactive_range[0], inactive_range[1])

                # Grant it to the user
                thread_db.execute(
                    "INSERT OR IGNORE INTO xp VALUES(?,?)", (user, 0))
                thread_db.execute(
                    f"UPDATE xp SET amt = amt + {amt} WHERE user = \"{user}\"")

        # Commit XP modifications and clear active users for the next window.
        thread_db.commit()

        self.active_users.clear()

    def get_top(self, rank: int):
        """Return the top 3 XP holders.
        """
        with self.db as db:
            if rank:
                user = self.get_user(rank=rank)
                if user:
                    return f"{user[0]} is #{user[1]} with {user[2]} XP."
                else:
                    return f"There is no rank #{rank} user."

            self.log_d(f"Retrieving top 3 XP holders")
            cs = db.cursor()
            cs.execute(f"SELECT user,amt FROM xp ORDER BY amt DESC")
            res = cs.fetchmany(3)

            return " | ".join([f"{r[0]}: {r[1]}" for r in res])

    def get_user(self, user: str = None, rank: int = None):
        """Return the user, position, and XP.

        :param user: The name of the user
        :param rank: The rank of the user
        :return: A list containing [`name`, `rank`, `xp`]
        """
        self.log_d(f"retrieving user:{user} or rank:{rank}")

        with self.db as db:
            cs = db.cursor()

            # Getting their position
            all = tuple(map(lambda x: x, cs.execute(
                'SELECT user, amt FROM xp ORDER BY amt DESC').fetchall()))
            try:
                if user:
                    if user.startswith("@"):
                        user = user[1:]

                    all_names = [i[0] for i in all]
                    rank = all_names.index(user)

                else:
                    if rank > len(all):
                        raise ValueError

                    # to allow negative indices, show last place, etc.
                    if rank > 0:
                        rank -= 1

                user = all[rank]
                return (user[0], rank + 1, user[1])

            except ValueError:
                # If finding their index in the sorted list fails assume they don't exist.
                return False

    def mod_user(self, args):
        """Perform an action on a user.
        """
        actions = ['set', 'transfer', 'ban', 'unban']
        msg = f"Please provide a valid action and a user. Valid actions include: {', '.join(actions)}."

        try:
            action = args[0]
            user = args[1]

            if action not in actions:
                raise IndexError
        except IndexError:
            return msg

        if user.startswith("@"):
            user = user[1:]

        self.log_d(f"running XPMod action {action} {args} on {user}")
        with self.db as db:
            if action == "set":
                # verify needed args exist
                try:
                    amt = int(args[2])
                except (ValueError, IndexError):
                    return "Please provide a number to set the user's XP to."

                # perform update
                db.execute(
                    f"UPDATE xp SET amt = {amt} WHERE user = \"{user}\"")
                msg = f"Set {user}'s XP to {amt}."

            elif action == "transfer":
                # verify needed args exist
                try:
                    target = args[2]
                    amount = int(args[3])
                except (ValueError, IndexError):
                    return "Please provide a user to transfer the first user's points to, and how many."

                # resolve users and amounts
                src = self.get_user(user=user)
                if not src:
                    return f"User {user} has no tracked XP."
                tar = self.get_user(user=target)
                if not tar:
                    if target.startswith("@"):
                        target = target[1:]

                    tar = (target, 0, 0)

                    db.execute(
                        "INSERT OR IGNORE INTO xp VALUES(?,?)", (target, 0))

                # ensure we don't grant more than the user can afford
                d = src[2] - amount
                if d < 0:
                    s_amt = 0
                    t_amt = tar[2] + src[2]
                    amount = src[2]
                else:
                    s_amt = d
                    t_amt = tar[2] + amount

                # perform updates
                db.execute(
                    f"UPDATE xp SET amt = {s_amt} WHERE user = \"{src[0]}\"")
                db.execute(
                    f"UPDATE xp SET amt = {t_amt} WHERE user = \"{tar[0]}\"")
                msg = f"Transferred {amount} points from {user} to {tar[0]}."

            elif action == "ban":
                omit_users = self.cfg_get("omit_users")
                if user in omit_users:
                    return f"User {user} is already banned from XP."

                # create the user if they don't already exist
                db.execute(
                    "INSERT OR IGNORE INTO xp VALUES(?,?)", (user, 0))
                db.execute(f"UPDATE xp SET amt = 0 WHERE user = \"{user}\"")

                omit_users.append(user)
                self.cfg_set("omit_users", omit_users)

                msg = f"Set {user}'s XP to 0 and banished from earning."

            elif action == "unban":
                omit_users = self.cfg_get("omit_users")
                if user not in omit_users:
                    return f"User {user} is not banned from XP."

                omit_users.remove(user)
                self.cfg_set("omit_users", omit_users)

                msg = f"Removed {user} from XP banished users."

            db.commit()
        return msg

    def main(self, message: Message):
        args = self.get_args_lower(message)

        if not args:
            arg = message.author.name.lower()
        else:
            arg = args.pop(0)

        # Show top 3 or user at rank given
        if arg == "top":

            rank = None
            if args:
                try:
                    rank = int(args.pop(0))
                except ValueError:
                    return "Give a valid integer for rank."

            return self.get_top(rank)

        # XP moderation tools
        if arg == "mod":
            if not message.author.mod:
                return "You must be a moderator to do that."

            return self.mod_user(args)

        user = self.get_user(user=arg)
        if user:
            return f"{user[0]} is #{user[1]} with {user[2]} XP."
        else:
            return f"{arg} has no tracked XP."

    def on_pubmsg(self, message: Message):
        # Add this user to the active users list.
        if not message.author.name in self.active_users:
            self.active_users.append(message.author.name.lower())
