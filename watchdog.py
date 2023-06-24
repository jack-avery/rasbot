import click
import logging
import os
import re
import sys
import threading

import time
from update import check

from src.config import read_global, BASE_CONFIG_PATH
from src.authentication import TwitchOAuth2Helper
from src.bot import TwitchBot


class InstanceHandler(threading.Thread):
    def __init__(self, *args, **kwargs):
        self.bot = kwargs["bot"]
        kwargs.pop("bot")
        super(InstanceHandler, self).__init__(*args, **kwargs)

    def stop(self):
        self.bot.__del__()


@click.command()
@click.option(
    "--authfile",
    help="The path to the auth file. This is relative to the 'userdata' folder.",
)
@click.option(
    "--debug/--normal",
    help="Have instances be verbose about actions.",
    default=False,
)
def main(authfile=None, debug=False):
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
        logging.addHandler(file_handler)

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(loglevel)
    stdout_handler.setFormatter(formatter)
    logging.addHandler(stdout_handler)

    logging.setLevel(loglevel)

    # read auth
    if not authfile:
        authfile = cfg_global["default_authfile"]

    auth = TwitchOAuth2Helper(authfile)

    # find all local instances
    instances = dict()
    for file in os.listdir(BASE_CONFIG_PATH):
        if re.match(r"\d+", file):
            if "config.txt" in os.listdir(f"{BASE_CONFIG_PATH}/{file}"):
                instances[file] = False

    logging.info(
        f"Found these configured instances: {', '.join([i for i in instances.keys()])}"
    )

    while True:
        # check for new instances
        logging.info("Checking for live streams...")
        streams = auth.get_live_streams(list(instances.keys()))

        # kick up new instances for ids without an instance
        for id, login in streams:
            if not instances[id]:
                logging.info(f"Kicking up instance for {login} ({id})")
                instance = TwitchBot(auth, login, id)
                instances[id] = InstanceHandler(
                    target=lambda: instance.start(), bot=instance
                )
                instances[id].start()

        # kill instances for missing ids (offline streams)
        live_ids = [stream[0] for stream in streams]
        for id, bot in instances.items():
            if isinstance(bot, InstanceHandler) and id not in live_ids:
                logging.info(f"Killing instance for {login} ({id})")
                bot.stop()

                instances[id] = False

        # inform of which streams are running
        logging.info(
            f"Running instances: {', '.join([i for i, b in instances.items() if isinstance(b, InstanceHandler)])}"
        )

        # check once a minute
        time.sleep(60)


if __name__ == "__main__":
    main()
