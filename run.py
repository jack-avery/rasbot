import requests
import click
from bot import TwitchBot
from authorization import Authorization

@click.command()
@click.option(
    "--login",
    help="The Twitch login to use."
)
@click.option(
    "--auth",
    default="_AUTH",
    help="The path to the auth file to parse. _AUTH by default."
)
def run(login=None,auth=None):
    if login is None:
        # Prompt user for Twitch login
        login = input("Twitch.tv username > ")

    auth = Authorization(auth)

    # Resolve ID from channel name
    url = f"https://api.twitch.tv/helix/users?login={login}"
    r = requests.get(url, headers=auth.get_headers()).json()
    channel_id=f"{r['data'][0]['id']}"

    # Start the bot
    tb = TwitchBot(auth,channel_id)
    tb.start()

if __name__ == "__main__":
    run()