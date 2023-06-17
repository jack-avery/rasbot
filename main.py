from src.definitions import check_all_dependencies

# Automatically install dependencies listed in manifests
check_all_dependencies()

import logging
import os
import sys
import time
import traceback

import click

from update import check
from src.config import ConfigHandler, GLOBAL_CONFIG_FILE, DEFAULT_GLOBAL
from src.authentication import TwitchOAuth2Helper
from src.bot import TwitchBot
from src.telemetry import report_exception, notify_instance, TelemetryLevel

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
    try:
        tb = None

        # Check for updates first!
        check(silent=True)

        # read global config
        gcfg_handler = ConfigHandler(GLOBAL_CONFIG_FILE, DEFAULT_GLOBAL)
        cfg_global = gcfg_handler.read()

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

        if not authfile:
            authfile = cfg_global["default_authfile"]
        auth = TwitchOAuth2Helper(authfile)

        if not channel:
            channel = auth.user_id

        telemetry_setting = cfg_global["telemetry"]
        if telemetry_setting == TelemetryLevel.NOT_ASKED:
            telemetry_setting = TelemetryLevel.NONE

            user_wants_send_errors = (
                input(
                    "Would you like to send errors to help us improve rasbot? (y/n) - "
                ).lower()
                == "y"
            )
            if not user_wants_send_errors:
                telemetry_setting = TelemetryLevel.EXCEPTIONS_ONLY

                user_wants_send_usage_data = (
                    input(
                        "Would you like to additionally send usage statistics? (y/n) - "
                    ).lower()
                    == "y"
                )
                if user_wants_send_usage_data:
                    cfg_global["telemetry"] = TelemetryLevel.USAGE_DATA

            cfg_global["telemetry"] = telemetry_setting
            gcfg_handler.write(cfg_global)

        notify_instance()
        tb = TwitchBot(auth, channel)
        tb.start()

    except KeyboardInterrupt:
        if isinstance(tb, TwitchBot):
            tb.__del__()
        sys.exit(0)

    except SystemExit:
        pass

    except:
        traceback.print_exc()
        report_exception(traceback.format_exc())


if __name__ == "__main__":
    main()
