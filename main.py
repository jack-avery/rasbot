import subprocess
import sys

subprocess.call(
    [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--disable-pip-version-check",
        "-qqq",
        "-r",
        "requirements.txt",
    ]
)

import click
import logging
import os
import time
from update import check

from src.config import read_global
from src.authentication import TwitchOAuth2Helper
from src.bot import TwitchBot

log = logging.getLogger("rasbot")
formatter = logging.Formatter("%(asctime)s %(levelname)s %(module)s | %(message)s")


@click.command()
@click.option("--channel", help="The Twitch channel to target.")
@click.option(
    "--authfile",
    help="The path to the auth file. This is relative to the 'userdata' folder.",
)
@click.option(
    "--debug/--normal",
    help="Have this instance be verbose about actions.",
    default=False,
)
def main(channel=None, authfile=None, debug=False):
    # Check for updates first!
    check(silent=True)

    # read global config
    cfg_global = read_global()

    # Set up logging
    if cfg_global["always_debug"]:
        debug = True

    loglevel = logging.INFO
    if debug:
        loglevel = logging.DEBUG

        if not os.path.exists("logs"):
            os.mkdir("logs")
        file_handler = logging.FileHandler(
            f"logs/{time.asctime().replace(':','-').replace(' ','_')}.log"
        )
        file_handler.setLevel(loglevel)
        file_handler.setFormatter(formatter)
        log.addHandler(file_handler)

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(loglevel)
    stdout_handler.setFormatter(formatter)
    log.addHandler(stdout_handler)

    log.setLevel(loglevel)

    # read auth
    if not authfile:
        authfile = cfg_global["default_authfile"]

    auth = TwitchOAuth2Helper(authfile)

    # use self as channel if no channel given
    if not channel:
        channel = auth.user_id

    # start the bot
    try:
        tb = TwitchBot(auth, channel)
        tb.start()

    # catch ctrl+C and force unimport modules;
    # speeds up ctrl+C exiting with timed modules
    except KeyboardInterrupt:
        tb.unimport_all_modules()
        sys.exit(0)


if __name__ == "__main__":
    main()
