import os
import sys
import subprocess

import src.config as config
from src.definitions import AuthenticationDeniedError


def main(file: str):
    # Check for new requirements
    print("Running local requirements.txt...")
    subprocess.check_call([sys.executable, "-m", "pip",
                           "install", "-r", "requirements.txt"])
    print("All requirements installed.\n")

    # We don't want people to accidentally overwrite their current auth
    if os.path.isfile(file):
        print(f"You already have an authfile at {file}!")
        print(f"Running this tool will overwrite {file}.")
        print("If you want to save it, please rename it to something else, then restart this tool.\n")
        if input("Are you sure you want to continue? (y/Y for yes): ").lower() != 'y':
            sys.exit(0)

    # Set up
    # Import auth here as it uses requests and will error out otherwise
    from src.authentication import Authentication

    # Getting Twitch username
    user_id = input("Your Twitch username: ").lower()

    # Asking to set up Twitch 2FA
    print(f"\nHello, {user_id}!")
    print("You'll need to make sure you have Twitch.tv mobile two-factor authentication enabled:")
    print("1. Go to your Twitch account settings, Security and Privacy.")
    print("2. Scroll to Security and click 'Set Up Two-Factor Authentication' and follow the steps.")
    input("Press [Enter] once you've set that up.")

    # Getting Client ID and Secret
    print("\nNow, go to dev.twitch.tv and log in:")
    print("1. Click on 'Your Console' in the top right.")
    print("2. On the right side pane, click Register Your Application.")
    print("3. Give it a name. Doesn't matter what.")
    print("4. Create an OAuth redirect for http://localhost and click 'Add'.")
    print("5. Set the Category to Chat Bot.")
    print("6. Click 'Create', and then click 'Manage'.")
    client_id = input("Enter the Client ID: ")

    print("\nNow, click on 'New Secret'.")
    client_secret = input("Enter the Client Secret: ")

    # Getting IRC OAuth
    print("\nAlmost done! Now, go to twitchapps.com/tmi/ and log in.")

    # Making sure the key is stripped
    irc_oauth = input("Enter the text it gives you: ")
    if irc_oauth.startswith("oauth:"):
        irc_oauth = irc_oauth[6:]

    # Adding all the info to the auth
    auth = Authentication(file)
    auth.auth['user_id'] = user_id
    auth.auth['client_id'] = client_id
    auth.auth['client_secret'] = client_secret
    auth.auth['irc_oauth'] = irc_oauth

    # Automatically getting OAuth
    print("\nTrying to automatically set up your OAuth...")
    try:
        auth.refresh_oauth()
        print("Got it!")
    except AuthenticationDeniedError as err:
        print(f"Failed to set up: {err}")
        input("Re-run the program, and make sure you enter things correctly!")
        sys.exit(1)

    # Inform the user
    input("\nSetup done! You can close this window.")


if __name__ == "__main__":
    cfg_global = config.read_global()

    file = cfg_global['default_authfile']

    main(file)
