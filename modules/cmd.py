# This is a built-in function.
# Please do not modify this unless you really know what you're doing.

import re

from src.plugins import BaseModule
from src.definitions import (
    Author,
    Message,
    user_privilege_from_status,
    status_from_user_privilege,
)

VALID_COMMAND_RE = re.compile(r"[a-z0-9_]+")
"""Regex to compare given command names to for validation."""


class Module(BaseModule):
    helpmsg = "Add, modify, or delete a command. Usage: cmd <add/del> <name> <args?>"

    default_config = {
        # The parameters to be given, after cooldown, before response
        # to indicate this command should be mod-only or hidden from !help
        "subonly_arg": "-subonly",
        "viponly_arg": "-viponly",
        "modonly_arg": "-modonly",
        "hostonly_arg": "-hostonly",
        "hidden_arg": "-hidden",
        # The default cooldown to apply to a command if none is specified
        "default_cooldown": 5,
    }

    consumes = -1

    def __init__(self, bot, name):
        BaseModule.__init__(self, bot, name)

        self.SUBONLY_ARG = self.cfg_get("subonly_arg")
        self.VIPONLY_ARG = self.cfg_get("viponly_arg")
        self.MODONLY_ARG = self.cfg_get("modonly_arg")
        self.HOSTONLY_ARG = self.cfg_get("hostonly_arg")
        self.HIDDEN_ARG = self.cfg_get("hidden_arg")
        self.DEFAULT_COOLDOWN = self.cfg_get("default_cooldown")

    def main(self, message: Message):
        cmd = self.get_args(message)

        if not cmd:
            return self.helpmsg

        if len(cmd) < 2:
            return "Not enough parameters given."

        # use lower of next item as action
        action = cmd.pop(0).lower()

        # use lower of next item as acting command name
        cmd_name = cmd.pop(0).lower()

        if action in ["+", "a", "add", "create", "new", "make", "mk"]:
            if not cmd:
                return "Not enough parameters given."

            # try to use next item as cooldown in seconds
            # if it can't convert to int, use default
            try:
                cmd_cooldown = int(cmd[0])
                cmd.pop(0)
            except ValueError:
                cmd_cooldown = self.DEFAULT_COOLDOWN

            # check for parameters and consume if found
            params = {
                self.SUBONLY_ARG: False,
                self.VIPONLY_ARG: False,
                self.MODONLY_ARG: False,
                self.HOSTONLY_ARG: False,
                self.HIDDEN_ARG: False,
            }
            for _ in params:
                for param in params:
                    if cmd[0].lower() == param:
                        params[param] = True
                        cmd.pop(0)

            if params[self.HOSTONLY_ARG]:
                cmd_priv = Author.Privilege.HOST
            elif params[self.MODONLY_ARG]:
                cmd_priv = Author.Privilege.MOD
            elif params[self.VIPONLY_ARG]:
                cmd_priv = Author.Privilege.VIP
            elif params[self.SUBONLY_ARG]:
                cmd_priv = Author.Privilege.SUB
            else:
                cmd_priv = Author.Privilege.USER

            # verify all parameters are valid
            if not VALID_COMMAND_RE.match(cmd_name):
                return "Command name can only use alphanumeric characters and underscores (_)."

            if cmd_cooldown < 0:
                return "Command cooldown must be a positive integer."

            command = {
                "name": cmd_name,
                "cooldown": cmd_cooldown,
                "response": " ".join(cmd),
                "hidden": params[self.HIDDEN_ARG],
                "privilege": cmd_priv,
            }

            # add command and write config
            try:
                self._bot.commands_handler.add(cmd_name, command)
                self._bot.save()

                return f"Command {cmd_name} added successfully."

            except ModuleNotFoundError as mod:
                return f"Module {mod} does not exist in the modules folder."

            except AttributeError as mod:
                return f'Module {mod} does not have a "Module" class to import.'

        if action in ["-", "d", "delete", "del", "remove", "rem", "rm"]:
            if cmd_name not in self._bot.commands_handler.commands:
                return f"Command {cmd_name} does not exist!"

            self._bot.commands_handler.delete(cmd_name)
            self._bot.save()

            return f"Command {cmd_name} removed successfully."

        if action in ["e", "modify", "mod", "edit"]:
            if cmd_name not in self._bot.commands_handler.commands:
                return f"Command {cmd_name} does not exist!"

            if not cmd:
                return f"Not enough parameters."

            key = cmd.pop(0)

            if key in ["cd", "cooldown"]:
                try:
                    value = int(cmd[0])
                    if value < 0:
                        raise ValueError
                except ValueError | IndexError:
                    return "Cooldown must be a positive integer."

                self._bot.commands_handler.modify(cmd_name, "cooldown", value)
                self._bot.save()

                return f"Cooldown for {cmd_name} set to {value}."

            if key in ["name", "rename"]:
                new_name = cmd[0].lower()

                if not VALID_COMMAND_RE.match(new_name):
                    return "Command name can only use alphanumeric characters and underscores (_)."

                self._bot.commands_handler.add(
                    new_name, self._bot.commands_handler.commands[cmd_name]
                )
                self._bot.commands_handler.delete(cmd_name)
                self._bot.save()

                return f"Command {cmd_name} renamed to {new_name}."

            if key in ["res", "response"]:
                if not cmd:
                    return "Response cannot be empty."

                value = " ".join(cmd)

                self._bot.commands_handler.modify(cmd_name, "response", value)
                self._bot.save()

                return f"Response for {cmd_name} set to {value}."

            if key in ["mod", "requires_mod"]:
                priv = self._bot.commands_handler.commands[cmd_name].privilege
                if priv not in [Author.Privilege.USER, Author.Privilege.MOD]:
                    return "Command uses a new privilege setting. requires_mod will not work. Aborting"

                value = (
                    Author.Privilege.USER
                    if priv == Author.Privilege.MOD
                    else Author.Privilege.MOD
                )

                self._bot.commands_handler.modify(cmd_name, "privilege", value)
                self._bot.save()

                return f"Mod requirement for {cmd_name} toggled to {value == Author.Privilege.MOD}."

            if key in ["privs", "priv", "privilege"]:
                if not cmd:
                    return "Please provide a privilege value. 0=User, 1=Sub, 2=VIP, 3=Mod, 4=Host."

                try:
                    value = int(cmd[0])
                except ValueError:
                    value = user_privilege_from_status(cmd[0])

                if value == -1 or status_from_user_privilege(value) == -1:
                    return "Please provide a privilege value. 0=User, 1=Sub, 2=VIP, 3=Mod, 4=Host."

                self._bot.commands_handler.modify(cmd_name, "privilege", value)
                self._bot.save()

                return f"Privilege requirement for '{cmd_name}' set to '{status_from_user_privilege(value)}' and above only."

            if key in ["hide", "hidden"]:
                value = not self._bot.commands_handler.commands[cmd_name].hidden

                self._bot.commands_handler.modify(cmd_name, "hidden", value)
                self._bot.save()

                return f"Hiding from help for {cmd_name} toggled to {value}."

            return (
                "Valid fields to modify are: cooldown, response, requires_mod, hidden"
            )

        return "Valid actions are: add, remove, edit."
