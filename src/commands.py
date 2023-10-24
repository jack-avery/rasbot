import logging
import re
import time

from src.definitions import Author, Message, NO_MESSAGE_SIGNAL

MODULE_MENTION_RE = re.compile(r"(%([\/a-z0-9_]+)%)")
"""Regex to search command responses with to apply modules."""


class Command:
    name: str
    cooldown: int
    response: str
    privilege: int
    hidden: bool
    """Whether this command is hidden from the `help` module."""

    def __init__(
        self,
        name: str,
        command: dict = None,
    ):
        """Create a new `Command`.

        :param name: The name of the command.
        :param command: The full dict representing the command.
        """
        self.name = name.lower()

        self.cooldown = command["cooldown"]
        self.response = command["response"]
        self.hidden = command["hidden"]

        # convert legacy requires_mod into new privilege system
        if "requires_mod" in command:
            self.privilege = Author.Privilege.USER
            if command["requires_mod"]:
                self.privilege = Author.Privilege.MOD
            del command["requires_mod"]

        else:
            self.privilege = command["privilege"]

        self._last_used = 0

    def get_used_modules(self) -> list:
        """Get the list of modules that are mentioned in `self.response`.

        :return: The list of modules used.
        """
        return [m[1] for m in MODULE_MENTION_RE.findall(self.response)]

    def jsonify(self) -> dict:
        return {
            "cooldown": self.cooldown,
            "privilege": self.privilege,
            "hidden": self.hidden,
            "response": self.response,
        }


class CommandsHandler:
    commands: dict[str, Command]
    """List of available commands."""

    def __init__(self, bot):
        self.bot = bot
        self.commands = {}

    def get(self, name: str) -> Command | None:
        return self.commands.get(name, None)

    def add(
        self,
        name: str,
        command: dict = None,
    ) -> None:
        """Create a new command (or modifies an existing one).
        Automatically attempts to import any unimported modules.

        :param name: The name of the command.
        :param command: dict representing the command.
        """
        logging.debug(f"adding {name} ({command})")

        # Resolve any modules the command mentions and import new ones
        for _, module in MODULE_MENTION_RE.findall(command["response"]):
            if module not in self.bot.modules_handler.modules:
                try:
                    self.bot.modules_handler.add(module)
                except ModuleNotFoundError as err:
                    raise err

        self.commands[name] = Command(name, command)

    def modify(self, name: str, key: str, value) -> None:
        """Modify `key` for `name`.

        :param name: The name of the command.
        :param key: The field of the command to modify.
        :param value: The value to set the field to.
        """
        logging.debug(f"modifying {key} of {name} to {value}")
        if key == "cooldown":
            self.commands[name].cooldown = value

        elif key == "response":
            self.commands[name].response = value

        elif key == "privilege":
            self.commands[name].privilege = value

        elif key == "hidden":
            self.commands[name].hidden = value

        else:
            raise ValueError(f"{key} is not a valid field to modify")

    def delete(self, name: str) -> None:
        """Delete a command if it exists.

        :param name: The name of the command.
        """
        logging.debug(f"removing {name}")
        del self.commands[name]

    def run(self, command: str, message: Message) -> str | None:
        """Code to be run when this command is called from chat.

        Runs all %% codes found in the command and returns the result.
        """
        command: Command = self.commands.get(command, None)
        if not command:
            return None

        # check cooldown
        if time.time() - command._last_used < command.cooldown:
            return None

        # check privilege
        if message.author.priv < command.privilege:
            return None

        # Apply the main function for any modules found
        returned_response = command.response
        for mention, module in MODULE_MENTION_RE.findall(returned_response):
            returned_response = returned_response.replace(
                mention, str(self.bot.modules_handler.run(module, message))
            )

        if NO_MESSAGE_SIGNAL in returned_response:
            return None

        command._last_used = time.time()
        return returned_response

    def find_first_command_using_module(self, module: str) -> Command:
        for command in self.commands.values():
            if module in command.get_used_modules():
                return command
        return None
