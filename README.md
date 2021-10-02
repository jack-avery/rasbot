# rasbot
Modular Python-based Twitch bot optimized for customizability.

Contact me at `raspy#0292` on Discord about bugs and glitches.

Installing:
1. Download [Python version 3.6.5+](https://www.python.org/downloads/)
2. Download the Source Code (using [git](https://git-scm.com/downloads) or otherwise)
3. Run this command in a console in the installation folder to install requirements:
```
pip install -r requirements.txt
```

# Usage
1. Set up your authorization in a file called \_AUTH (configurable through clargs).
      > see "Setting up your Authorization".
2. Launch run.py. That's it.

- To create commands, type `r!cmdadd <command_name> <cooldown_in_seconds> <response>`.
- To delete commands, type `r!cmddel <command_name>`.
You can make a command mod-only by adding `-modonly` to the `cmdadd` message.

To use a method, encase the method name in `&` symbols:
- For example, to use the provided `np` method: `r!cmdadd np 5 &np&`

Happy chatbotting!

# Setting up your Authorization
**Ensure you have Twitch.tv two-factor authentication enabled on your account:**

Go to your Twitch account settings, Security and Privacy.
Scroll to Security and click "Set Up Two-Factor Authentication" and follow the steps.

**To get the Client ID and Client Secret:**
1. Log in to https://dev.twitch.tv/.
2. Go to "Your Console" in the top right.
3. On the right side pane, click Register Your Application.
4. Name it rasbot, set the OAuth redirect to http://localhost, set the Category to Chat Bot
5. Click on Manage. This will show you your Client ID.
6. On the same page is the "New Secret" button to create the Client Secret.

**To get the IRC OAuth:**
1. Go to https://twitchapps.com/tmi/ and log in.
2. Add the key given to irc_oauth, exclude "oauth:".

**To get your Twitch OAuth:**
If you've configured your \_AUTH file correctly, you should be able to run authorization.py and it will print your oauth key out to you.
Note that this oauth key needs to be refreshed once every two months.

# Here's a sample of how your \_AUTH file should look:
```
user_id:taeyang_square_jumps
client_id:agd9fga84tijaer
client_secret:4gijoa48u9adfg
irc_oauth:gafd89ugi34j5aer
oauth:gfa8u9gihjon48ui
(make sure that there is an empty line at the bottom of the file.)
```


