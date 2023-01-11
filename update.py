import io
import os
import requests
import subprocess
import sys

import click
import semantic_version

import src.config as config

# Master option to ALWAYS OPT OUT OF UPDATES and ignore any in the future!
# Set this to True if you want, but things might break eventually.
# You will need to run the command `update.py --force`, or set this back to False to get updates again.
ALWAYS_OPT_OUT = False

try:
    cfg = config.read_global()
    branch = cfg['release_branch']
except:
    branch = 'main'

BASE_URL = f"https://raw.githubusercontent.com/jack-avery/rasbot/{branch}/"
"""The base URL to get raw text from and download rasbot from."""

RASBOT_BASE_UPDATER = 'update.py'
"""The rasbot updater. This needs to be updated first for the update to work fully."""

RASBOT_BASE = ['bot.py', 'setup.py']
"""Remaining built-in base files to update after the updater."""

RASBOT_SRC = [
    'authentication.py',
    'commands.py',
    'config.py',
    'definitions.py'
]
"""Files inside `./src` to update."""

BUILTIN_MODULES = [
    'admin.py',
    'caller.py',
    'cmd.py',
    'cmdadd.py',
    'cmddel.py',
    'help.py',
    'prefix.py',
    'sample.py',
    'uptime.py',
    'user.py',
    'xp.py',
    'osu/request.py',
    'osu/np.py',
]
"""Modules to always update alongside rasbot."""
# TODO: customization for which to update maybe? idk?


@click.command()
@click.option(
    "--silent/--loud",
    help="Whether the update check should be silent.",
    default=False
)
@click.option(
    "--force/--no-force",
    help="Whether or not to force an update. Use if your installation is broken.",
    default=False
)
@click.option(
    "-l/-nl",
    help="For update order. Probably shouldn't manually set this.",
    default=False
)
def main(silent=False, force=False, l=False):
    check(silent, force, l)


def check(silent=False, force=False, l=False):
    """Checks for updates.

    :param silent: Whether the check should announce itself.

    :param force: Whether or not to force an update.
    """
    if force:
        force_update()
    if l:
        update_after_updater()

    if ALWAYS_OPT_OUT:
        return

    current = get_current_version()

    if not silent:
        print("Checking for updates...")
        print(f"You are running on rasbot version: {current}")

    latest = semantic_version.Version(requests.get(f"{BASE_URL}/version").text)

    if current < latest:
        prompt()

    else:
        if not silent:
            input()


def get_current_version():
    """Read the version file and return the contents.
    """
    with open('version', 'r') as verfile:
        try:
            return semantic_version.Version(verfile.read())
        except ValueError:
            input("Your version file is invalid.\nYou can use the command 'update.py --force' to fix your installation.")
            sys.exit(1)


def prompt():
    """Prompts the user to update rasbot.
    """
    print("--")
    print("HEY! Your version of rasbot is running out of date!")
    print("Updating is recommended, but will overwrite any changes you've made to the files rasbot comes with.")
    print("This does not include anything found in your module config.")
    print("--\n")

    if input("Would you like to update? (y/Y for yes): ").lower() == 'y':
        update()


def force_update():
    """Update the updater and the rest of rasbot without opening a new instance of the updater.
    """
    do_files('', [RASBOT_BASE_UPDATER])
    update_after_updater()

    # Close this process, so we don't use a broken bot.py from autoupdate
    input("rasbot has reinstalled. You may need to run the updater again to fully fix your installation.")
    sys.exit(0)


def update():
    """Updates the rasbot updater first, then updates the rest.
    """
    do_files('', [RASBOT_BASE_UPDATER])
    print("Finished updating updater. Updating rasbot...\n")

    # Open a new instance of Python to run the updated file
    p = subprocess.Popen([sys.executable, RASBOT_BASE_UPDATER, "-l"])
    p.wait()

    # Close this process, so we don't use a broken bot.py from autoupdate
    input("See what's changed in the #news channel in the Discord https://discord.gg/qpyT4zx.\n"
          + "rasbot is now up to date, and will close to apply changes.")
    sys.exit(0)


def update_after_updater():
    # Update base files
    do_files('', RASBOT_BASE)

    # Update source files
    do_files('src/', RASBOT_SRC)
    print("Finished updating rasbot.\n")

    # Update commands
    do_files('modules/', BUILTIN_MODULES)
    print("Finished updating built-in modules.\n")

    # Check for new requirements
    do_files('', ['requirements.txt'])

    subprocess.check_call([sys.executable, "-m", "pip",
                          "install", "-r", "requirements.txt"])
    print("All requirements checked.\n")

    # Update README files
    do_files('', ['README.md'])
    do_files('modules/', ['README.md'])
    print("Finished updating README files.\n")

    # Increment version
    do_files('', ['version'])


def do_files(path: str, files: list):
    """Update multiple files at once.

    :param path: The path to the folder of the files.

    :param files: The list of files to update, including extensions.
    """
    verify_folder_exists(f"{path}{file}")
    for file in files:
        print(f"Updating {path}{file}...")

        # if the file doesn't exist don't write anything
        req = requests.get(f"{BASE_URL}{path}{file}")
        if req.status_code == 404:
            print("Failed to fetch: ignoring...")
            continue

        # make the folder if it doesn't exist
        if not path == '':
            if not os.path.exists(path):
                os.mkdir(path)

        # write the text to file
        with io.open(f"{path}{file}", 'w', encoding="utf8") as local:
            local.write(req.text)


def verify_folder_exists(path: str):
    """Create `path` if it does not exist.

    :param path: The path to verify the entire trace exists for.
    """
    folder_list = path.split("/")
    folders = []
    for i, name in enumerate(folder_list):
        # assume file and end of path reached, break
        if '.' in name:
            break

        folder = f"{'/'.join(folder_list[:i+1])}"
        folders.append(folder)

    # Verify config folder exists
    for folder in folders:
        if not os.path.exists(folder):
            os.mkdir(folder)


if __name__ == "__main__":
    main()
