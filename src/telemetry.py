import re

import requests
import urllib.parse

from src.config import read_global
from update import get_rasbot_current_version

URL = "https://jackavery.ca/api/rasbot_notify"

HOME_PATH_WIN_RE = r"\"C:\\Users\\\w+"
HOME_PATH_LINUX_RE = r"\"/home/\w+"

USERNAME = "rasbot"


class TelemetryLevel:
    NOT_ASKED = -1
    NONE = 0
    EXCEPTIONS_ONLY = 1
    USAGE_DATA = 2


def report_exception(message: str):
    if read_global()["telemetry"] < TelemetryLevel.EXCEPTIONS_ONLY:
        return

    # Remove potential personal information
    message = re.sub(HOME_PATH_WIN_RE, '"~', message)
    message = re.sub(HOME_PATH_LINUX_RE, '"~', message)
    message = urllib.parse.quote_plus(message)

    requests.get(f"{URL}/err/{message}")


def notify_instance():
    if read_global()["telemetry"] < TelemetryLevel.USAGE_DATA:
        return

    message = f"New instance started with version {get_rasbot_current_version()}"
    message = urllib.parse.quote_plus(message)

    requests.get(f"{URL}/info/{message}")
