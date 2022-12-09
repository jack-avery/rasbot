import io
import subprocess
import sys
import requests
import click
import semantic_version
from definitions import BUILTIN_MODULES, RASBOT_BASE

BASE_URL = "https://raw.githubusercontent.com/jack-avery/rasbot/main"

# Master option to ALWAYS OPT OUT OF UPDATES and ignore any in the future!
# Set this to True if you want, but things might break eventually.
# You will need to run the command `update.py --force`, or set this back to False to get updates again.
ALWAYS_OPT_OUT = False


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
        update_first()
    if l:
        update_inner()

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
        update_first()


def update_first():
    """Updates rasbot.
    """
    # Update definitions and updater first!
    for module in ['definitions', 'update']:
        print(f"Updating {module}.py...")
        text = requests.get(
            f"{BASE_URL}/{module}.py").text

        with open(f"{module}.py", 'w') as commandfile:
            commandfile.write(text)

    print("Finished updating important modules. Updating remainder...")

    p = subprocess.Popen(["update.py", "-l"], shell=True)
    p.wait()

    input("\nrasbot is up to date. rasbot will now close to apply changes.")
    sys.exit(0)


def update_inner():
    # Update commands
    for module in BUILTIN_MODULES:
        print(f"Updating built-in module {module}...")
        text = requests.get(
            f"{BASE_URL}/modules/{module}.py").text

        with open(f"modules/{module}.py", 'w') as modulefile:
            modulefile.write(text)
    print("Finished updating modules.\n")

    # Update modules
    for base in RASBOT_BASE:
        if base not in ['definitions', 'update']:
            print(f"Updating base file {base}...")
            text = requests.get(
                f"{BASE_URL}/{base}.py").text

            with open(f"{base}.py", 'w') as basefile:
                basefile.write(text)
    print("Finished updating base.\n")

    # Check for new requirements
    print("Running requirements.txt...")
    requirements = requests.get(
        f"{BASE_URL}/requirements.txt").text
    with open("requirements.txt", 'w') as requirementsfile:
        requirementsfile.write(requirements)

    check_requirements()
    print("All requirements checked.\n")

    # Update README files
    print("Updating README.md...")
    readme = requests.get(
        f"{BASE_URL}/README.md").text
    with io.open("README.md", 'w', encoding="utf8") as readmemd:
        readmemd.write(readme)
    print("Finished updating README.md.\n")

    print("Updating modules README.md...")
    modreadme = requests.get(
        f"{BASE_URL}/modules/README.md").text
    with open("modules/README.md", 'w') as modreadmemd:
        modreadmemd.write(modreadme)
    print("Finished updating modules README.md.\n")

    # Increment version
    print("Incrementing version...")
    version = requests.get(
        f"{BASE_URL}/version").text
    with open("version", 'w') as versionfile:
        versionfile.write(version)


def check_requirements():
    subprocess.check_call([sys.executable, "-m", "pip",
                          "install", "-r", "requirements.txt"])


if __name__ == "__main__":
    check_cli()
