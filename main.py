from src.definitions import check_dependencies

# Automatically install dependencies listed in manifests
check_dependencies()

import logging
import os
import sys
import time
import traceback

log_handlers = []
formatter = logging.Formatter("%(asctime)s %(levelname)s %(module)s | %(message)s")
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.INFO)
stdout_handler.setFormatter(formatter)
log_handlers.append(stdout_handler)
if not os.path.exists("logs"):
    os.mkdir("logs")
file_handler = logging.FileHandler(
    f"logs/{time.asctime().replace(':','-').replace(' ','_')}.log"
)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
log_handlers.append(file_handler)
logging.basicConfig(handlers=log_handlers, level=logging.DEBUG)

import click

from update import check_manifests
from src.config import ConfigHandler, GLOBAL_CONFIG_FILE, DEFAULT_GLOBAL
from src.authentication import TwitchOAuth2Helper
from src.bot import TwitchBot
from src.telemetry import report_exception, notify_instance, TelemetryLevel


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
