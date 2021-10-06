# rasbot
**Modular Python-based Twitch bot optimized for customizability.**

rasbot is a Python-based Twitch bot that runs on *your* Twitch account, 
and comes with a short list of methods to facilitate the creation of simple chat commands, 
such as a simple `keyboard` command that shows your keyboard.

rasbot also comes set up to allow users to easily create their own custom methods, 
where if you know how to code it in Python, it can run as a command for your Twitch bot, 
for example, the provided [np](https://github.com/raspy-on-osu/rasbot/blob/master/methods/np.py) 
method that reads from a file created by [osu!StreamCompanion](https://github.com/Piotrekol/StreamCompanion) 
and outputs 'now playing' information into the chat.

Contact me at `raspy#0292` on Discord about bugs and glitches,
or join our [official Discord server](https://discord.gg/qpyT4zx)!

# Installing
1. Download [Python version 3.6.5+](https://www.python.org/downloads/)
2. Download the Source Code (using [git](https://git-scm.com/downloads) or otherwise)
3. Run this command in a console in the installation folder to install requirements:
```
py -m pip install -r requirements.txt
```

# Usage
1. Set up your authentication in a file called \_AUTH (configurable through clargs).
> see "Setting up your Authentication".
2. Launch run.py. That's it.

Managing commands:
- To create commands, type `r!cmdadd <command_name> <cooldown_in_seconds> <response>`.
- To delete commands, type `r!cmddel <command_name>`.
- You can make a command mod-only by adding `-modonly` to the `cmdadd` message.

To use a method, encase the method name in `&` symbols:
- For example, to use the provided `np` method: `r!cmdadd np 5 &np&`

Happy chatbotting!

# Setting up your Authentication

**To have rasbot run properly, you need 5 things:**
1. `user_id:` Your Twitch username.
2. `client_id:` The Client ID for the Twitch app, set-up below.
3. `client_secret:` The Client Secret for the Twitch app, set-up below
4. `irc_oauth:` The Twitch IRC OAuth, used for connecting to Twitch chat.
5. `oauth:` The Twitch API OAuth, used for making calls to the Twitch API.

`user_id` and `oauth` are the easiest as you already know your `user_id`, and `oauth` is configured automatically by the `refresh_oauth.py` program.

**Ensure you have Twitch.tv two-factor authentication enabled on your account:**

Go to your Twitch account settings, Security and Privacy.
Scroll to Security and click "Set Up Two-Factor Authentication" and follow the steps.
> This is required to register an application to get your Client ID and Secret.

**To get the Client ID and Client Secret:**
1. Log in to https://dev.twitch.tv/.
2. Go to "Your Console" in the top right.
3. On the right side pane, click Register Your Application.
4. Give it a name (doesn't matter), set the OAuth redirect to http://localhost, set the Category to Chat Bot
5. Click on Manage. This will show you your Client ID.
6. On the same page is the "New Secret" button to create the Client Secret.

**To get the IRC OAuth:**
1. Go to https://twitchapps.com/tmi/ and log in.
2. Add the key given to irc_oauth, exclude "oauth:".

**To get your Twitch OAuth:**
If you've configured your \_AUTH file correctly, you should be able to run refresh_oauth.py and it will configure your OAuth for you.
Note that this oauth key needs to be refreshed once every two months.

**Here's a sample of how your \_AUTH file should look BEFORE running the above:**
```
user_id:taeyang_square_jumps
client_id:agd9fga84tijaer
client_secret:4gijoa48u9adfg
irc_oauth:gafd89ugi34j5aer

```
Make sure that there is an empty line at the bottom of the file.

