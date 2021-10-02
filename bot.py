###
#   rasbot main twitch bot module
#   raspy#0292 - raspy_on_osu
###

import os
import traceback
import requests
import irc.bot
import commands
import config
from errors import CommandIsModOnlyError, CommandStillOnCooldownError

class TwitchBot(irc.bot.SingleServerIRCBot):
    def __init__(self, auth, channel_id:int, cfgfile:str=None):
        """Create a new instance of a Twitch bot.

        :param auth: The Authorization object to use.

        :param channel_id: The channel ID.

        :param dbfile: The dbfile to read information from.
        """
        self.auth = auth
        self.authkeys = self.auth.get_auth()
        self.channel_id = channel_id

        # Create DB handler
        #self.db = DBHandler(dbfile)

        # Import channel info
        #info = self.db.get_channel_info_for_id(channel_id)

        if cfgfile:
            cfg = config.read(cfgfile)
        else:
            cfg = config.read(self.channel_id)
        
        self.prefix = cfg["prefix"]

        # Instantiate commands module
        self.commands = commands

        # Import commands
        #db_commands = self.db.get_commands_for_id(channel_id)
        for command in cfg["commands"]:
            self.commands.command_modify(command[0],command[1],command[3],command[2])

        # Import custommethods
        custommethods = os.listdir('custommethods')
        custommethods.remove('__pycache__')
        for custommethod in custommethods:
            if custommethod[-3:] == '.py':
                self.commands.custommethod_add(custommethod[:-3])

        # Resolve channel name
        url = f"https://api.twitch.tv/helix/users?id={self.channel_id}"
        r = requests.get(url, headers=self.auth.get_headers()).json()
        self.channel=f"#{r['data'][0]['login']}"

        # Create IRC bot connection
        server = 'irc.twitch.tv'
        port = 80
        print('Connecting to ' + server + ' on port ' + str(port) + '...')
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port, f"oauth:{self.authkeys['irc_oauth']}")], self.authkeys["user_id"], self.authkeys["user_id"])

    def on_welcome(self, c, e):
        print(f'Joined {self.channel}! ({self.channel_id})')
        
        # You must request specific capabilities before you can use them
        c.cap('REQ', ':twitch.tv/membership')
        c.cap('REQ', ':twitch.tv/tags')
        c.cap('REQ', ':twitch.tv/commands')
        c.join(self.channel)

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
        msg = str(e.arguments)
        msg = msg[2:-2].lower().split(' ')

        # If you want anything to be run per-message,
        # Right here is probably where you want to put it.

        try:
            # If the message starts with the command prefix...
            if msg[0][:len(self.prefix)]==self.prefix:
                # Isolating command and command arguments
                # Verify that it's actually a command before continuing.
                cmd = msg[0][len(self.prefix):]
                if cmd not in self.commands.commands:
                    return

                # Isolate command arguments from command
                self.cmdargs = msg[1:]

                try:
                    # Run the command and string result message
                    cmdresult = self.commands.commands[cmd].run(self)

                    # If there is a string result message, print it to chat
                    if cmdresult:
                        self.connection.privmsg(self.channel, f"{name} > {cmdresult}")
                
                # If the command is still on cooldown, do nothing.
                # If the command is mod-only and a non-mod calls it, do nothing.
                except (CommandStillOnCooldownError,CommandIsModOnlyError):
                    return

        except Exception as err:
            self.connection.privmsg(self.channel, f'An error occurred in the processing of your request: {str(err)}'
                                                +'. A full stack trace has been output to the command window.')
            traceback.print_exc()
