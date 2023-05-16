import re

from discord import SyncWebhook

from src.config import read_global
from update import get_rasbot_current_version

WEBHOOK_URL = "https://discord.com/api/webhooks/1106454348172632155/GAT0mrLq-BB651fy4GtxulQuBf6LJgKuUALTmV_C8lXeQgoMrBMCktRJnH-lTiinnMBa"
# Please don't do anything weird with this! This webhook is for private exception reporting so anyone noted as a developer can take a look.

WEBHOOK = SyncWebhook.from_url(WEBHOOK_URL)

GLOBAL_CONFIG = read_global()

HOME_PATH_WIN_RE = r"\"C:\\Users\\\w+"
HOME_PATH_LINUX_RE = r"\"/home/\w+"


def report_exception(message: str, username: str):
    # Turn this off if you don't want it, but it helps me fix issues.
    if not GLOBAL_CONFIG["telemetry"] > 0:
        return

    # Remove potential personal information
    message = re.sub(HOME_PATH_WIN_RE, '"~', message)
    message = re.sub(HOME_PATH_LINUX_RE, '"~', message)

    WEBHOOK.send(content=message, username=username)


def notify_instance(username: str):
    # Nice to have for me to know who is using it as well as what version.
    if not GLOBAL_CONFIG["telemetry"] > 1:
        return

    message = f"New instance started with version {get_rasbot_current_version()}"
    WEBHOOK.send(content=message, username=username)
