import logging
import sys
import traceback

from src.definitions import check_dependencies

# Automatically install dependencies listed in manifests
check_dependencies()

import click

from update import check_manifests
from src.config import ConfigHandler, GLOBAL_CONFIG_FILE, DEFAULT_GLOBAL
from src.authentication import TwitchOAuth2Helper
from src.bot import TwitchBot

@click.command()
@click.option("--channel", help="The Twitch channel to target.")
@click.option(
    "--authfile",
    help="The path to the auth file. This is relative to the 'userdata' folder.",
)
def main(channel=None, authfile=None):
    tb = None
    try:
        # Check for updates/missing files first!
        check_manifests()

        # read global config
        gcfg_handler = ConfigHandler(GLOBAL_CONFIG_FILE, DEFAULT_GLOBAL)
        cfg_global = gcfg_handler.read()

        if not authfile:
            authfile = cfg_global["default_authfile"]
        auth = TwitchOAuth2Helper(authfile)

        if not channel:
            channel = auth.user_id

        tb = TwitchBot(auth, channel)
        tb.start()

    except KeyboardInterrupt:
        if isinstance(tb, TwitchBot):
            tb.__del__()
        sys.exit(0)

    except:
        err_str = traceback.format_exc()
        logging.error(err_str)


if __name__ == "__main__":
    main()
