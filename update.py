import subprocess
import sys
import requests
import click
from definitions import BUILTIN_COMMANDS,\
    BUILTIN_MODULES

@click.command()
@click.option(
    "--silent",
    help="Whether the update check should be silent."
)
@click.option(
    "--force",
    help="Whether or not to force an update. Useful if your installation is broken."
)
def check(silent=False,force=False):
    """Checks for updates.

    :param silent: Whether the check should announce itself.

    :param silent: Whether or not to force an update.
    """
    if force:
        update()

    if not silent: print("Checking for updates...")

    with open('version','r') as verfile:
        try:
            version = int(verfile.read())
        except ValueError:
            if not silent: input("Your version file is invalid.")
            exit()
    
    if not silent: print(f"You are running on rasbot version: {version}")

    latest = int(requests.get("https://raw.githubusercontent.com/raspy-on-osu/rasbot/master/version").text)

    if version < latest:
        prompt(latest-version)
    else:
        if not silent: input("rasbot is up to date. You may close this window.")

def prompt(ood:int):
    """Prompts the user to update rasbot.

    :param ood: How many versions the user is running out of date.
    """
    print("--")
    print(f"HEY! Your version of rasbot is running {ood} version(s) out of date!")
    print("Updating is recommended, but will overwrite any changes you've made to the files rasbot comes with.")
    print("--\n")

    if input("Would you like to update? (y/Y for yes): ").lower() == 'y':
        update()

def update():
    """Updates rasbot.
    """
    for command in BUILTIN_COMMANDS:
        print(f"Updating built-in method {command}...")
        text = requests.get(f"https://raw.githubusercontent.com/raspy-on-osu/rasbot/master/methods/{command}.py").text
        
        with open(f"methods/{command}.py",'w') as commandfile:
            commandfile.write(text)
    print("Finished updating commands.")

    for module in BUILTIN_MODULES:
        print(f"Updating built-in module {module}...")
        text = requests.get(f"https://raw.githubusercontent.com/raspy-on-osu/rasbot/master/{module}.py").text
        
        with open(f"{module}.py",'w') as modulefile:
            modulefile.write(text)
    print("Finished updating modules.")

    print("Running requirements.txt...")
    requirements = requests.get("https://raw.githubusercontent.com/raspy-on-osu/rasbot/master/requirements.txt").text.split("\n")
    for requirement in requirements:
        pip_install(requirement)
    print("All requirements checked.")

    print("Incrementing version...")
    version = requests.get("https://raw.githubusercontent.com/raspy-on-osu/rasbot/master/version").text
    with open("version",'w') as versionfile:
        versionfile.write(version)

    input(f"Finished! rasbot is now up to date on version {version}.\nPress enter to continue.")
    
def pip_install(package:str):
    """Attempts to install a package.
    """
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

if __name__ == "__main__":
    check()