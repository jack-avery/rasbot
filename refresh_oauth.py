import click
from authentication import Authentication
from definitions import AuthenticationDeniedError


@click.command()
@click.option(
    "--auth",
    help="The path to the auth file to modify."
)
def refresh_oauth(auth):
    a = Authentication(auth)

    try:
        a.auth['oauth'] = a.request_oauth()
    except AuthenticationDeniedError as err:
        print(f"Authentication Denied: {err}")
        input("Please ensure that your credentials are valid.")
        exit()

    a.write_authfile()
    input(
        f"Your new OAuth token has been written to {a.file}. You may close this window.")


if __name__ == "__main__":
    refresh_oauth()
