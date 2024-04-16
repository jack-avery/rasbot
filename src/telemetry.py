import logging
import random
import re
import string

# For identifying logs that coincide with eachother
footprint = "".join(
    random.choice(string.ascii_letters + string.digits).lower() for _ in range(8)
)

import requests

from src.config import read_global
from update import get_rasbot_current_version

URL = "https://jackavery.ca/api/rasbot_notify"

HOME_PATH_WIN_RE = r"\"C:[\\/]Users[\\/]\w+"
HOME_PATH_LINUX_RE = r"\"/home/\w+"

USERNAME = "rasbot"


class TelemetryLevel:
    NOT_ASKED = -1
    NONE = 0
    EXCEPTIONS_ONLY = 1
    USAGE_DATA = 2


def send(mode: str, message: str):
    message += f"\n\n> {footprint}"

    headers = {
        "Content-Type": "application/json"
    }

    data = {
        "mode": mode,
        "message": message
    }

    try:
        requests.post(
            f"{URL}",
            headers=headers,
            json=data,
            timeout=2
        )
    except requests.exceptions.ReadTimeout:  # allow failed requests to time out quietly
        logging.warn(
            "Telemetry ping to jackavery.ca/api/rasbot_notify timed out. Is jackavery.ca down?"
        )


def report_exception(message: str):
    if read_global()["telemetry"] < TelemetryLevel.EXCEPTIONS_ONLY:
        return

    # Remove potential personal information
    message = re.sub(HOME_PATH_WIN_RE, '"~', message)
    message = re.sub(HOME_PATH_LINUX_RE, '"~', message)

    send("err", message)


def notify_instance():
    if read_global()["telemetry"] < TelemetryLevel.USAGE_DATA:
        return

    message = f"New instance started with version {get_rasbot_current_version()}"

    send("info", message)
