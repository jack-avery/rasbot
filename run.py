import requests
import click
from bot import TwitchBot
from authentication import Authentication
from definitions import AuthenticationDeniedError


@click.command()
@click.option(
    "--channel",
    help="The twitch channel to target."
)
@click.option(
    "--auth",
    help="The path to the auth file."
)
@click.option(
    "--cfg",
    help="The path to the channel config file."
)
@click.option(
    "--debug/--normal",
    help="Have this instance be verbose about actions.",
    default=False
)
def run(channel=None, auth=None, cfg=None, debug=False):
    auth = Authentication(auth)

    if channel is None:
        channel = auth.get_auth()['user_id']

    # Resolve ID from channel name
    channel_id = False
    while not channel_id:
        url = f"https://api.twitch.tv/helix/users?login={channel}"
        r = requests.get(url, headers=auth.get_headers()).json()
        try:
            channel_id = int(f"{r['data'][0]['id']}")
        except KeyError:
            if r['status'] == 401:
                print("OAuth key is invalid or expired. Attempting a refresh...")
                try:
                    auth.auth['oauth'] = auth.request_oauth()
                    auth.write_authfile()
                except AuthenticationDeniedError as err:
                    print(f"Authentication Denied: {err}")
                    print("Please ensure that your credentials are valid.")
                    print("You may need to re-run setup.py.\n")
                    input("This error is unrecoverable. rasbot will now exit.")
                    exit(1)

    # Start the bot
    tb = TwitchBot(auth, channel_id, channel, cfg, debug)
    tb.start()


if __name__ == "__main__":
    run()
