import requests
import click
from bot import TwitchBot
from authentication import Authentication

@click.command()
@click.option(
    "--channel",
    help="The twitch channel to target."
)
@click.option(
    "--auth",
    help="The path to the auth file to parse."
)
@click.option(
    "--cfg",
    help="The channel ID to pull config information from."
)
def run(channel=None,auth=None,cfg=None):
    auth = Authentication(auth)
    
    if channel is None:
        channel = auth.get_auth()['user_id']

    # Resolve ID from channel name
    url = f"https://api.twitch.tv/helix/users?login={channel}"
    r = requests.get(url, headers=auth.get_headers()).json()
    channel_id=int(f"{r['data'][0]['id']}")

    # Start the bot
    tb = TwitchBot(auth,channel_id,channel,cfg)
    tb.start()

if __name__ == "__main__":
    run()
