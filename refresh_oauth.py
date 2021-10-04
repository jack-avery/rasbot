import click
from authentication import Authentication

@click.command()
@click.option(
    "--auth",
    help="The auth file to modify."
)
def refresh_oauth(auth):
    a = Authentication(auth)
    a.auth['oauth'] = a.request_oauth()
    a.write_authfile()
    input(f"Your new OAuth token has been written to {auth}. You may close this window.")

if __name__ == "__main__":
    refresh_oauth()
