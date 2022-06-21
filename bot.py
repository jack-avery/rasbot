###
#   rasbot main twitch bot module
#   raspy#0292 - raspy_on_osu
###

import logging
import os
import sys
import traceback
import irc.bot
import commands
import config
import update
from definitions import CommandIsModOnlyError,\
    CommandStillOnCooldownError

class TwitchBot(irc.bot.SingleServerIRCBot):
    def __init__(self, auth, channel_id:int, channel:str=None, cfgid:int=None, debug:bool=False):
        """Create a new instance of a Twitch bot.

        :param auth: The Authentication object to use.

        :param channel_id: The channel ID.

        :param channel: The channel name.

        :param cfginfo: The bot config file to read configuration from.

        :param debug: Whether the bot should be verbose about actions.
        """
        # Check for updates first!
        update.check(True)

        # Set up logging
        if debug:
            logmode = logging.DEBUG
        else:
            logmode = logging.INFO
        
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logmode)
        
        stdout_formatter = logging.Formatter("%(asctime)s %(levelname)s | %(message)s")
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(logmode)
        stdout_handler.setFormatter(stdout_formatter)
        self.logger.addHandler(stdout_handler)

        self.auth = auth
        self.authkeys = self.auth.get_auth()
        self.channel_id = channel_id

        self.logger.info(f"Starting as {self.authkeys['user_id']}...")

        # Import channel info
        if cfgid is None:
            self.cfgid = f"_{self.channel_id}.txt"
        else:
            self.cfgid = cfgid
        
        self.logger.info(f"Reading config from {self.cfgid}...")

        cfg = config.read(self.cfgid)
        self.prefix = cfg["prefix"]

        self.logger.info(f"Prefix set as '{self.prefix}'")

        # Instantiate commands module
        self.commands = commands

        # Import commands
        for command in cfg["commands"]:
            self.logger.debug(f'Importing command {" ".join(command)}')
        
            # For some reason "False" doesn't eval to False.
            if command[2] == "False":
                command[2] = False

            if command[3] == "False":
                command[3] = False

            self.commands.command_modify(command[0],command[1]," ".join(command[4:]),command[2],command[3])

        self.logger.info(f"Imported {len(cfg['commands'])} custom command(s)")

        # Import methods
        methods = os.listdir('methods')
        for method in methods:
            if method.endswith('.py'):
                self.logger.debug(f"Importing method {method}")
                
                self.commands.method_add(method[:-3])

        self.logger.info(f"Imported {len(self.commands.methods)} method(s)")

        # Resolve channel name
        if channel is None:
            self.channel = "#"+self.authkeys['user_id']
        else:
            self.channel = "#"+channel

        # Create IRC bot connection
        server = 'irc.twitch.tv'
        port = 80
        self.logger.info('Connecting to ' + server + ' on port ' + str(port) + '...')
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port, f"oauth:{self.authkeys['irc_oauth']}")], self.authkeys['user_id'], self.authkeys['user_id'])

    def on_welcome(self, c, e):
        # You must request specific capabilities before you can use them
        c.cap('REQ', ':twitch.tv/membership')
        c.cap('REQ', ':twitch.tv/tags')
        c.cap('REQ', ':twitch.tv/commands')
        c.join(self.channel)

        self.logger.info(f'Joined {self.channel}! ({self.channel_id})\n')

    def on_pubmsg(self, c, e):
        """Code to be run when a message is sent.
        """
        # Resolving username and mod status
        for i in e.tags:
            if i['key']=="display-name":
                name=str.lower(i['value'])

            if i['key']=="mod":
                ismod=i['value']
        
        # Setting mod status to a bool and giving broadcaster moderator priveleges
        if ismod=='1' or name.lower()==self.channel.lower()[1:]:
            ismod=True
        else:
            ismod=False
        
        self.caller_name = name
        self.caller_ismod = ismod

        # Reading the message
        self.msg = str(e.arguments)
        self.msg_split = self.msg[2:-2].split(' ')

        try:
            # Do per-message methods
            self.commands.do_per_message_methods(self)

            # If the message starts with the command prefix...
            if self.msg_split[0][:len(self.prefix)].lower()==self.prefix:
                # Isolating command and command arguments
                # Verify that it's actually a command before continuing.
                cmd = self.msg_split[0][len(self.prefix):].lower()
                if cmd not in self.commands.commands:
                    self.logger.debug(f"Ignoring invalid command call '{cmd}' from {self.caller_name} (mod:{self.caller_ismod})")
                    return

                # Isolate command arguments from command
                self.cmdargs = self.msg_split[1:]

                try:
                    # Run the command and string result message
                    self.logger.info(f"Running command call '{cmd}' from {self.caller_name} (mod:{self.caller_ismod}) (args:{self.cmdargs})")
                    cmdresult = self.commands.commands[cmd].run(self)

                    # If there is a string result message, print it to chat
                    if cmdresult:
                        self.send_message(f"{name} > {cmdresult}")
                
                # If the command is still on cooldown, do nothing.
                # If the command is mod-only and a non-mod calls it, do nothing.
                except (CommandStillOnCooldownError,CommandIsModOnlyError) as err:
                    self.logger.info(f"{err}")

        except Exception as err:
            self.send_message(f'An error occurred in the processing of your request: {str(err)}. '
                              +'A full stack trace has been output to the command window.')
            traceback.print_exc()

    def send_message(self, message:str):
        """Sends a message. For easy use within methods.

        :param message: The message to send.
        """
        self.connection.privmsg(self.channel, message)