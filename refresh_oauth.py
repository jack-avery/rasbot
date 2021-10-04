import click
from authentication import Authentication
from definitions import DEFAULT_AUTHFILE, AuthenticationDeniedError

@click.command()
@click.option(
    "--auth",
    help="The auth file to modify."
)
def refresh_oauth(auth):
    a = Authentication(auth)

    try:
        a.auth['oauth'] = a.request_oauth()
    except AuthenticationDeniedError as err:
        print(f"Authentication Denied: {err}")
        input("Please ensure that your credentials are valid.")
        exit()

    if auth is None:
        auth = DEFAULT_AUTHFILE

    a.write_authfile()
    input(f"Your new OAuth token has been written to {auth}. You may close this window.")

if __name__ == "__main__":
    refresh_oauth()
