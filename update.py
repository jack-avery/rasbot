import io
import subprocess
import sys
import requests
import click
import semantic_version

# Master option to ALWAYS OPT OUT OF UPDATES and ignore any in the future!
# Set this to True if you want, but things might break eventually.
# You will need to run the command `update.py --force`, or set this back to False to get updates again.
ALWAYS_OPT_OUT = False

BASE_URL = "https://raw.githubusercontent.com/jack-avery/rasbot/main/"
"""The base URL to get raw text from and download rasbot from."""

RASBOT_BASE_UPDATER = 'update.py'
"""The rasbot updater. This needs to be updated first for the update to work fully."""

RASBOT_BASE = ['authentication.py', 'bot.py', 'commands.py', 
               'config.py', 'definitions.py', 'setup.py']
"""Remaining built-in base files to update after the updater."""

BUILTIN_MODULES = ['caller.py', 'cmdadd.py', 'cmddel.py', 'help.py',
                   'np.py', 'prefix.py', 'request.py', 'sample.py', 
                   'target.py', 'uptime.py', 'xp.py']
"""Built-in command modules."""


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
    help="Used in updating, performs the rest of the update after updating itself and definitions.",
    default=False
)
def check_cli(silent=False, force=False, l=False):
    check(silent, force, l)


def check(silent=False, force=False, l=False):
    """Checks for updates.

    :param silent: Whether the check should announce itself.

    :param force: Whether or not to force an update.
    """
    if force:
        update()
    if l:
        update_after_updater()

    if ALWAYS_OPT_OUT:
        return

    if not silent:
        print("Checking for updates...")

    with open('version', 'r') as verfile:
        try:
            current = semantic_version.Version(verfile.read())
        except ValueError:
            if not silent:
                input(
                    "Your version file is invalid.\nYou can use the command 'update.py --force' to fix your installation.")
            exit()

    if not silent:
        print(f"You are running on rasbot version: {current}")

    latest = semantic_version.Version(requests.get(f"{BASE_URL}/version").text)

    if current < latest:
        prompt()


def prompt():
    """Prompts the user to update rasbot.
    """
    print("--")
    print(
        f"HEY! Your version of rasbot is running out of date!")
    print("Updating is recommended, but will overwrite any changes you've made to the files rasbot comes with.")
    print("This does not include anything found in your module config.")
    print("--\n")

    if input("Would you like to update? (y/Y for yes): ").lower() == 'y':
        update()


def update():
    """Updates the rasbot updater first, then updates the rest.
    """
    # Update updater first!
    do_files('',[RASBOT_BASE_UPDATER])

    print("Finished updating updater. Updating rasbot...")

    p = subprocess.Popen([sys.executable, RASBOT_BASE_UPDATER, "-l"], shell=True)
    p.wait()

    input("\nrasbot is up to date. rasbot will now close to apply changes.")
    sys.exit(0)


def update_after_updater():
    # Update base files
    do_files('',RASBOT_BASE)
    print("Finished updating rasbot.\n")

    # Update commands
    do_files('modules/',BUILTIN_MODULES)
    print("Finished updating built-in modules.\n")

    # Check for new requirements
    do_files('',['requirements.txt'])

    check_requirements()
    print("All requirements checked.\n")

    # Update README files
    do_files('',['README.md'])
    do_files('modules/',['README.md'])
    print("Finished updating README files.\n")

    # Increment version
    do_files('',['version'])

def do_files(path: str, files: list):
    """Update multiple files at once.

    :param path: The path to the folder of the files.
    
    :param files: The list of files to update, including extensions.
    """
    for file in files:
        print(f"Updating {path}{file}...")
        text = requests.get(
            f"{BASE_URL}{path}{file}").text

        with open(f"{path}{file}", 'w') as local:
            local.write(text)

def check_requirements():
    subprocess.check_call([sys.executable, "-m", "pip",
                          "install", "-r", "requirements.txt"])


if __name__ == "__main__":
    check_cli()
