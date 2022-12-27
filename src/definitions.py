##
# Helper classes.
##

class Author:
    name = str
    """The display name of the author."""

    uid = str
    """The ID of the author."""

    mod = bool
    """Whether the author is a moderator."""

    sub = bool
    """Whether the author is a subscriber."""

    vip = bool
    """Whether the author is a VIP."""

    host = bool
    """Whether the author is the channel owner."""

    def __init__(self, name: str, uid: str, mod: bool = False, sub: bool = False, vip: bool = False, host: bool = False):
        """Create a new `Author`.

        :param name: The name of the user.
        :param uid: The ID of the user.
        :param mod: Whether the user is a Moderator of the Twitch chat.
        :param sub: Whether the user is subscribed to the Twitch channel.
        :param vip: Whether the user is a VIP of the Twitch channel.
        :param host: Whether the user is the owner of the Twitch channel.
        """
        self.name = name
        self.uid = uid
        self.mod = mod
        self.sub = sub
        self.vip = vip
        self.host = host

    def user_status(self) -> str:
        """Returns the highest privilege this user has.
        `host > mod > vip > sub > none`

        :return: A string representing this users' highest privilege level.
        """
        if self.host:
            return "Host"

        if self.mod:
            return "Mod"

        if self.vip:
            return "VIP"

        if self.sub:
            return "Sub"

        return "User"


class Message:
    author: Author
    """The `Author` object of the message."""

    text_raw: str
    """The raw text of the message."""

    cmd: str
    """The command used, if applicable, in this message."""

    args: list
    """The list of arguments in the message.
    Do not modify this directly!! Use `Message.consume()` to get arguments in modules.
    """

    def __init__(self, author: Author, text_raw: str = ''):
        """Create a new `Message`.

        :param author: The `Author` of this message.
        :param text_raw: The raw text of the message.
        """
        self.author = author
        self.text_raw = text_raw

    def attach_command(self, cmd: str = '', args: list = []):
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
            return False

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

##
# Definitions used in multiple files go here.
##


VALID_COMMAND_REGEX = r'[a-z0-9_]+'
"""Regex to compare given command names to for validation."""

MODULE_MENTION_REGEX = r'&([\/a-z0-9_]+)&'
"""Regex to compare command responses to for finding any mentioned modules."""

NO_MESSAGE_SIGNAL = "&NOMSG&"
"""Signal for a module to return for there to be no message sent no matter what."""

##
# Errors
##

# Authentication-related errors


class AuthenticationDeniedError(Exception):
    pass

# Command-related errors


class CommandStillOnCooldownError(Exception):
    pass


class CommandDoesNotExistError(Exception):
    pass


class CommandIsModOnlyError(Exception):
    pass


class CommandMustHavePositiveCooldownError(Exception):
    pass


class CommandGivenInvalidNameError(Exception):
    pass
