import os
from authentication import Authentication
from definitions import DEFAULT_AUTHFILE,\
    AuthenticationDeniedError

# We don't want people to accidentally overwrite their current auth
if os.path.isfile(DEFAULT_AUTHFILE):
    print(f"You already have an authfile at {DEFAULT_AUTHFILE}!")
    print(f"Running this tool will overwrite {DEFAULT_AUTHFILE}.")
    print("If you want to save it, please rename it to something else, then restart this tool.\n")
    if input("Are you sure you want to continue? (y/Y for yes): ").lower() != 'y':
        exit()

# Set up
auth = Authentication()

# Getting Twitch username
user_id = input("Your Twitch username: ")

# Asking to set up Twitch 2FA
print(f"\nHello, {user_id}!")
print("You'll need to make sure you have Twitch.tv two-factor authentication enabled:")
print("1. Go to your Twitch account settings, Security and Privacy.")
print("2. Scroll to Security and click 'Set Up Two-Factor Authentication' and follow the steps.")
input("Press [Enter] once you've set that up.")

# Getting Client ID and Secret
print("\nNow, go to dev.twitch.tv and log in:")
print("1. Click on 'Your Console' in the top right.")
print("2. On the right sidepane, click Register Your Application.")
print("3. Give it a name. Doesn't matter what.")
print("4. Add an OAuth redirect for http://localhost.")
print("5. Set the Category to Chat Bot.")
print("6. Click 'Create', and then click 'Manage'.")
client_id = input("Enter the Client ID: ")

print("\nNow, click on 'New Secret'.")
client_secret = input("Enter the Client Secret: ")

# Getting IRC OAuth
print("Almost done! Now, go to twitchapps.com/tmi/ and log in.")

# Making sure the key is stripped
irc_oauth = input("Enter the text it gives you: ")
if "oauth:" in irc_oauth: 
    irc_oauth = irc_oauth[irc_oauth.find(":")+1:]

auth.auth['user_id'] = user_id
auth.auth['client_id'] = client_id
auth.auth['client_secret'] = client_secret
auth.auth['irc_oauth'] = irc_oauth

# Automatically getting OAuth
print("\nTrying to automatically set up your OAuth...")

try:
    auth.auth['oauth'] = auth.request_oauth()
    print("Got it!")
except AuthenticationDeniedError as err:
    print(f"Failed to set up: {err}")
    input("Re-run the program, and make sure you enter things correctly!")
    exit()

# Write the authfile and finish
auth.write_authfile()
input("\nSetup done! You can close this window.")