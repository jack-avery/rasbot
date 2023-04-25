import click
import logging
import os
import re
import sys
import time
from update import check

from src.config import read_global, BASE_CONFIG_PATH
from src.authentication import TwitchOAuth2Helper
from src.bot import TwitchBot

log = logging.getLogger("rasbot")
formatter = logging.Formatter("%(asctime)s %(levelname)s %(module)s | %(message)s")


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

    # find all local instances
    instances = dict()
    for file in os.listdir(BASE_CONFIG_PATH):
        if re.match(r"\d+", file):
            if "config.txt" in os.listdir(f"{BASE_CONFIG_PATH}/{file}"):
                instances[file] = False

    log.info(
        f"Found these configured instances: {', '.join([i for i in instances.keys()])}"
    )

    try:
        while True:
            log.info("Checking for live streams...")
            streams = auth.get_live_streams(instances)

            # kick up new instances for ids without an instance
            for id, login in streams:
                if not instances[id]:
                    instance = TwitchBot(auth, login, id)
                    instance.start()

                    instances[id] = instance

            # kill instances for missing ids (offline streams)
            live_ids = [stream[0] for stream in streams]
            for instance, bot in instances.items():
                if isinstance(bot, TwitchBot) and instance not in live_ids:
                    bot.unimport_all_modules()
                    bot.__del__()

                    instances[instance] = False

            # check once a minute
            time.sleep(60)

    except KeyboardInterrupt:
        for bot in instances.values():
            if isinstance(bot, TwitchBot):
                bot.unimport_all_modules()
                bot.__del__()

            sys.exit(0)


if __name__ == "__main__":
    main()
