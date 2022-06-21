# rasbot
**Modular Python-based Twitch bot optimized for customizability and ease of use.**

rasbot is a Python-based Twitch bot that runs on *your* Twitch account,
and comes with a short list of modules to facilitate the creation of simple chat commands,
such as a simple `keyboard` command that shows your keyboard.

rasbot also comes set up to allow users to easily create their own custom modules,
where if you know how to code it in Python, it can run as a command for your Twitch bot,
for example, the provided [np](https://github.com/raspy-on-osu/rasbot/blob/master/modules/np.py)
module that reads from a file created by [osu!StreamCompanion](https://github.com/Piotrekol/StreamCompanion)
and outputs 'now playing' information into the chat.

Join our [official Discord server](https://discord.gg/qpyT4zx) to discuss rasbot development, including issues, ideas, and share modules.

# How to Use
1. Download and install [Python version 3.10.0+](https://www.python.org/downloads/)
2. Download the Source Code:
> Using [git](https://git-scm.com/downloads): `git clone https://github.com/raspy-on-osu/rasbot` <br/>
> Or, click on **Code** and **Download ZIP**.
3. Run this command in the installation folder to install requirements:
```
py -m pip install -r requirements.txt
```
4. Run `setup.py` and follow the steps to set up your authentication.
5. Run `run.py`. If you set up rasbot correctly, it will log some information and print something similar to: 
```
Joined #raspy_on_osu! (57511738)
```

> If `setup.py` fails, see "Setting up your authentication manually".

**rasbot will automatically check for updates every time you run `run.py`.**
You can check for updates manually by running update.py, and force a reinstallation of built-in modules using the command:
```
update.py --force
```

# Managing Commands
```
Create/update a command:
r!cmdadd <name> <cooldown> <parameters> <response>

Remove a command:
r!cmddel <name>
```

Valid parameters include:<br/>
`-modonly`: Set the command to be moderator/broadcaster use only.<br/>
`-hidden`: Set the command to be hidden from the `help` method.

By default, a command's name must contain only alphanumeric characters and underscores.

**Example**:
```
Creating the np command which uses modules/np.py:
r!cmdadd np 5 &np&

Making it hidden and mod-only:
r!cmdadd np 5 -hidden -modonly &np&

Removing it:
r!cmddel np
```

# Modules
Modules are subprograms that allow the user to run specific snippits of code whenever a message is sent, or a command response contains a modules' name encased in `&`.<br/>
To use a modules' method in a command, encase the module name in `&` symbols, such as in the examples above.<br/>
*For documentation on creating your own module, see [this](https://github.com/raspy-on-osu/rasbot/blob/master/modules/README.md).*

# Setting up your authentication manually

If `setup.py` doesn't work, here's how to do it manually...

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
4. Give it a name (doesn't matter), add an OAuth redirect to http://localhost, set the Category to Chat Bot
> Make sure to click "Add" to add the OAuth redirect.
5. Click on Manage. This will show you your Client ID.
6. On the same page is the "New Secret" button to create the Client Secret.

**To get the IRC OAuth:**
1. Go to https://twitchapps.com/tmi/ and log in.
2. Add the key given to irc_oauth, exclude "oauth:".

**To get your Twitch OAuth:**
If you've configured your \_AUTH file correctly, you should be able to run refresh_oauth.py and it will configure your Twitch OAuth for you.
> Note that this oauth key needs to be refreshed once every two months.

**Here's a sample of how your \_AUTH file should look BEFORE running the above:**
```
user_id:taeyang_square_jumps
client_id:agd9fga84tijaer
client_secret:4gijoa48u9adfg
irc_oauth:gafd89ugi34j5aer

```
>Make sure that there is the empty line at the bottom of the file.
