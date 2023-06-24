import json
import logging
import os
import subprocess
import sys
import threading
import time

log_handlers = []
formatter = logging.Formatter(
    "%(asctime)s | %(module)s [%(levelname)s] %(message)s",
)
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.INFO)
stdout_handler.setFormatter(formatter)
log_handlers.append(stdout_handler)
if not os.path.exists("logs"):
    os.mkdir("logs")
file_handler = logging.FileHandler(
    f"logs/{time.asctime().replace(':','-').replace(' ','_')}.log"
)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
log_handlers.append(file_handler)
logging.basicConfig(handlers=log_handlers, level=logging.DEBUG)


def check_dependencies():
    logging.info("Checking Python dependencies...")
    manifests = [
        manifest
        for manifest in os.listdir("src/manifests")
        if manifest.endswith(".manifest")
    ]
    for manifest in manifests:
        with open(f"src/manifests/{manifest}", "r") as manifestfile:
            manifest = json.loads(manifestfile.read())
        if "requirements" in manifest:
            if not manifest["requirements"]:
                continue
            subprocess.call(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "--disable-pip-version-check",
                    "-q",
                    *manifest["requirements"].split(" "),
                ]
            )


##
# Helper classes.
##


class Author:
    name: str
    uid: str
    is_mod: bool
    is_sub: bool
    is_vip: bool
    is_host: bool
    priv: int

    class Privilege:
        USER = 0
        SUB = 1
        VIP = 2
        MOD = 3
        HOST = 4

    def __init__(
        self,
        name: str,
        uid: str,
        is_mod: bool = False,
        is_sub: bool = False,
        is_vip: bool = False,
        is_host: bool = False,
    ):
        """Create a new `Author`.

        :param name: The name of the user.
        :param uid: The ID of the user.
        :param is_mod: Whether the user is a Moderator of the Twitch chat.
        :param is_sub: Whether the user is subscribed to the Twitch channel.
        :param is_vip: Whether the user is a VIP of the Twitch channel.
        :param is_host: Whether the user is the owner of the Twitch channel.
        """
        self.name = name
        self.uid = uid
        self.is_mod = is_mod
        self.is_sub = is_sub
        self.is_vip = is_vip
        self.is_host = is_host

        if is_host:
            self.priv = self.Privilege.HOST
        elif is_mod:
            self.priv = self.Privilege.MOD
        elif is_vip:
            self.priv = self.Privilege.VIP
        elif is_sub:
            self.priv = self.Privilege.SUB
        else:
            self.priv = self.Privilege.USER


def user_privilege_from_status(status: str) -> int:
    """Returns the integer representing `status` privilege.
    `host (4) > mod (3) > vip (2) > sub (1) > user (0)`

    :return: An integer representing the status' privilege. -1 if not found.
    """
    status = status.lower()
    if status in ["host", "broadcaster"]:
        return Author.Privilege.HOST
    if status in ["mod", "moderator", "janitor"]:
        return Author.Privilege.MOD
    if status in ["vip"]:
        return Author.Privilege.VIP
    if status in ["sub", "subscriber"]:
        return Author.Privilege.SUB
    if status in ["user", "pleb"]:
        return Author.Privilege.USER
    return -1


def status_from_user_privilege(priv: int) -> int:
    """Returns the integer representing `priv` status.
    `host (4) > mod (3) > vip (2) > sub (1) > user (0)`

    :return: An integer representing the privileges' status. -1 if not found.
    """
    if priv == Author.Privilege.HOST:
        return "Host"
    if priv == Author.Privilege.MOD:
        return "Mod"
    if priv == Author.Privilege.VIP:
        return "VIP"
    if priv == Author.Privilege.SUB:
        return "Sub"
    if priv == Author.Privilege.USER:
        return "User"
    return -1


class Message:
    author: Author
    text_raw: str
    cmd: str
    """The command used, if applicable, in this message."""
    args: list
    """The list of arguments in the message.\n
    ### Do not modify this directly!! Use `Module.get_args(message)` to get arguments in modules.
    """

    def __init__(self, author: Author, text_raw: str = ""):
        """Create a new `Message`.

        :param author: The `Author` of this message.
        :param text_raw: The raw text of the message.
        """
        self.author = author
        self.text_raw = text_raw
        self.cmd = None
        self.args = None

    def attach_command(self, cmd: str = "", args: list = []):
        """Attach command information to this `Message`.

        :param cmd: The command the `Author` called.
        :param args: The list of args the `Author` provided.
        """
        self.cmd = cmd
        self.args = args

    def consume(self, amount: int = 0):
        """Consume `amount` arguments, removing them from `self.args` and returning them.

        :param amount: The amount of arguments to consume from `self.args`.
        :return: The args consumed for use.
        """
        ret = []
        remaining = len(self.args)

        # return false if no arguments remain or not consuming anything
        if not remaining or amount == 0:
            return None

        # consume all if negative
        if amount < 0:
            amount = remaining

        # don't consume more than in the list
        elif amount > remaining:
            amount = remaining

        # consume and return consumed args
        ret = self.args[:amount]
        self.args = self.args[amount:]
        return ret


class Singleton:
    spaces = {}

    def __new__(cls, *args, **kwargs):
        name = args[0]
        if not hasattr(cls.spaces, name):
            cls.spaces[name] = super(Singleton, cls).__new__(cls)
        return cls.spaces[name]


class RepeatTimer(threading.Timer):
    # See https://stackoverflow.com/a/48741004
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)
