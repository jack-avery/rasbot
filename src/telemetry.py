import re

from discord import SyncWebhook

from src.config import read_global
from update import get_rasbot_current_version

WEBHOOK_URL = "https://discord.com/api/webhooks/1106454348172632155/GAT0mrLq-BB651fy4GtxulQuBf6LJgKuUALTmV_C8lXeQgoMrBMCktRJnH-lTiinnMBa"
# Please don't do anything weird with this! This webhook is for private exception reporting so anyone noted as a developer can take a look.

WEBHOOK = SyncWebhook.from_url(WEBHOOK_URL)

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

    WEBHOOK.send(content=message, username=USERNAME)


def notify_instance():
    if read_global()["telemetry"] < TelemetryLevel.USAGE_DATA:
        return

    message = f"New instance started with version {get_rasbot_current_version()}"
    WEBHOOK.send(content=message, username=USERNAME)
