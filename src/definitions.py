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

    def user_status(self) -> str:
        """Returns the highest privilege this user has.
        `host > mod > vip > sub > none`

        :return: A string representing this users' highest privilege level.
        """
        if self.is_host:
            return "Host"

        if self.is_mod:
            return "Mod"

        if self.is_vip:
            return "VIP"

        if self.is_sub:
            return "Sub"

        return "User"


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
