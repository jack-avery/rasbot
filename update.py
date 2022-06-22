import subprocess
import sys
import requests
import click
from definitions import BUILTIN_COMMANDS,\
    BUILTIN_MODULES

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
def check_cli(silent=False,force=False,l=False):
    check(silent,force,l)

def check(silent=False,force=False,l=False):
    """Checks for updates.

    :param silent: Whether the check should announce itself.

    :param force: Whether or not to force an update.
    """
    if force:
        update_first()
    if l:
        update_inner()

    if not silent: print("Checking for updates...")

    with open('version','r') as verfile:
        try:
            current = int(verfile.read())
        except ValueError:
            if not silent: input("Your version file is invalid.\nYou can use the command 'update.py --force' to fix your installation.")
            exit()
    
    if not silent: print(f"You are running on rasbot version: {current}")

    latest = int(requests.get("https://raw.githubusercontent.com/raspy-on-osu/rasbot/master/version").text)

    if current < latest:
        prompt(latest-current)
    else:
        if not silent: input("\nrasbot is up to date. You may close this window.")

def prompt(diff: int):
    """Prompts the user to update rasbot.

    :param diff: How many versions the user is running out of date.
    """
    print("--")
    print(f"HEY! Your version of rasbot is running {diff} version(s) out of date!")
    print("Updating is recommended, but will overwrite any changes you've made to the files rasbot comes with.")
    print("--\n")

    if input("Would you like to update? (y/Y for yes): ").lower() == 'y':
        update_first()

def update_first():
    """Updates rasbot.

    Reads from `BUILTIN_COMMANDS` and `BUILTIN_MODULES`,
    and updates all files located in each.
    """
    # Update definitions and updater first!
    for module in ['definitions','update']:
        print(f"Updating {module}.py...")
        text = requests.get(f"https://raw.githubusercontent.com/raspy-on-osu/rasbot/master/{module}.py").text

        with open(f"{module}.py",'w') as commandfile:
            commandfile.write(text)

    print("Finished updating important modules. Updating remainder...")

    p = subprocess.Popen(["update.py", "-l"], shell = True)
    p.wait()

def update_inner():
    # Update commands
    for command in BUILTIN_COMMANDS:
        print(f"Updating built-in method {command}...")
        text = requests.get(f"https://raw.githubusercontent.com/raspy-on-osu/rasbot/master/modules/{command}.py").text
        
        with open(f"modules/{command}.py",'w') as commandfile:
            commandfile.write(text)
    print("Finished updating modules.\n")

    # Update modules
    for module in BUILTIN_MODULES:
        if module not in ['definitions','update']:
            print(f"Updating built-in module {module}...")
            text = requests.get(f"https://raw.githubusercontent.com/raspy-on-osu/rasbot/master/{module}.py").text
            
            with open(f"{module}.py",'w') as modulefile:
                modulefile.write(text)
    print("Finished updating modules.\n")

    # Check for new requirements
    print("Running requirements.txt...")
    requirements = requests.get("https://raw.githubusercontent.com/raspy-on-osu/rasbot/master/requirements.txt").text.split("\n")
    for requirement in requirements:
        pip_install(requirement)
    print("All requirements checked.\n")

    # Update readme
    print("Updating README.md...")
    readme = requests.get("https://raw.githubusercontent.com/raspy-on-osu/rasbot/master/README.md").text
    with open("README.md",'w') as readmemd:
        readmemd.write(readme)
    print("Finished updating README.md.\n")

    # Increment version
    print("Incrementing version...")
    version = requests.get("https://raw.githubusercontent.com/raspy-on-osu/rasbot/master/version").text
    with open("version",'w') as versionfile:
        versionfile.write(version)
    
def pip_install(package:str):
    """Attempts to install a package.
    """
    subprocess.check_call([sys.executable, "-m", "pip", "install", package, "--quiet"])

if __name__ == "__main__":
    check_cli()