import hashlib
import io
import json
import logging
import os
import subprocess
import sys

import click
import requests
import semantic_version

from src.config import read_global

# Master option to ALWAYS OPT OUT OF UPDATES and ignore any in the future!
# Set this to True if you want, but things might break eventually.
# You will need to run the command `update.py --force`, or set this back to False to get updates again.
ALWAYS_OPT_OUT = False

try:
    cfg = read_global()
    rasbot_branch = cfg["release_branch"]
except:
    rasbot_branch = "main"

BASE_URL = f"https://raw.githubusercontent.com/jack-avery/rasbot/{rasbot_branch}/"
"""The base URL to get raw text from and download rasbot from."""

RASBOT_BASE_UPDATER = {
    "file": "update.py",
    "source": "https://raw.githubusercontent.com/jack-avery/rasbot/$BRANCH/update.py",
}
"""The rasbot updater. This needs to be updated first for the update to work fully."""

MANIFEST_DIR = "src/manifests/"
"""Base directory that should contain all manifests."""

RASBOT_BASE_MANIFEST = f"{MANIFEST_DIR}rasbot.manifest"
"""Manifest of all items to update within rasbot and their source."""


@click.command()
@click.option(
    "--force/--no-force",
    help="Whether or not to force an update. Use if your installation is broken.",
    default=False,
)
@click.option(
    "-l/-nl",
    help="For update order. Probably shouldn't manually set this.",
    default=False,
)
def main(force=False, l=False):
    check_manifests(force, l)


def check_manifests(force=False, l=False):
    """Checks for updates.

    :param force: Whether or not to force an update.
    """
    if force:
        prompt_update(forced=True)
    if l:
        update_from_manifests()

    if ALWAYS_OPT_OUT:
        return

    logging.info("Checking for updates...")

    updated = check_manifests_for_updates()
    if updated:
        prompt_update(updated=updated)

    missing = check_manifests_files_exist()
    if missing:
        prompt_update(updated=missing)


def prompt_update(forced: bool = False, updated: str = None):
    """
    Prompts the user to update rasbot.
    """
    user_wants_update = True
    if not forced:
        logging.info("--")
        logging.info(
            "These manifests indicate that updates are available (or files are missing):"
        )
        logging.info(f"{', '.join(updated)}")
        logging.info("--\n")
        user_wants_update = (
            input("Would you like to update? (y/Y for yes): ").lower() == "y"
        )

    if user_wants_update:
        update()


def update():
    """Updates the rasbot updater first, then updates the rest."""
    do_file(RASBOT_BASE_UPDATER)
    logging.info("Finished updating updater. Updating rasbot...\n")

    # Open a new instance of Python to run the updated file
    p = subprocess.Popen([sys.executable, RASBOT_BASE_UPDATER["file"], "-l"])
    p.wait()

    # Close this process, so we don't use a broken bot.py from autoupdate
    input(
        "See what's changed in the #news channel in the Discord https://discord.gg/qpyT4zx.\n"
        + "rasbot is now up to date, and will close to apply changes."
    )
    exit()


def get_manifest_list():
    """
    Returns all manifests contained in `src/manifests`.
    """
    manifests = []
    for manifestfile in os.listdir(MANIFEST_DIR):
        if manifestfile.endswith(".manifest"):
            manifests.append(manifestfile)
    return manifests


def get_manifest(manifest: str):
    """
    Returns the `dict` contents of `manifest`.

    :param manifest: The filename of the manifest in `src/manifests`.
    """
    try:
        with open(f"{MANIFEST_DIR}{manifest}", "r") as file:
            return json.loads(file.read())
    except json.JSONDecodeError | FileNotFoundError:
        return False


def get_updated_manifest(manifest):
    """
    Get the latest version of `manifest`.

    :param manifest: The manifest to get the latest version for.
    """
    source = manifest["source"].replace("$BRANCH", rasbot_branch)

    request = requests.get(source)

    if request.status_code < 200 or request.status_code >= 300:
        return False

    return json.loads(request.text)


def get_manifest_current_version(manifest: str = "rasbot.manifest"):
    """
    Get the current version of `manifest`.

    :param manifest: The filename of the manifest in `src/manifests`.
    """
    path = f"{MANIFEST_DIR}{manifest}"
    if not os.path.exists(path):
        return False
    with open(path, "r") as file:
        manifest = json.loads(file.read())
    if "version" in manifest:
        return manifest["version"]
    return False


get_rasbot_current_version = lambda: get_manifest_current_version()


def check_update_ready(manifest):
    """
    Check for if `manifest` has a newer version available.
    If this fails to grab the latest version, it will mark the manifest as having no update.

    :param manifest: The manifest to check for updates.
    """
    if "version" not in manifest:
        return True

    current = semantic_version.Version(manifest["version"])

    latest_manifest = get_updated_manifest(manifest)
    if not latest_manifest:
        return False

    latest = semantic_version.Version(latest_manifest["version"])
    return current < latest


def check_manifests_for_updates():
    """
    Using all manifests in `src/manifests`,
    checks to make see if any manifests have a newer version.

    If one does, that manifest is marked for updating.
    """
    updated_manifests = []
    for manifestfile in get_manifest_list():
        manifest = get_manifest(manifestfile)
        if not manifest:
            continue

        if check_update_ready(manifest):
            updated_manifests.append(manifestfile)

    if len(updated_manifests) == 0:
        return False

    return updated_manifests


def check_manifests_files_exist():
    """
    Using all manifests in `src/manifests`,
    checks to make sure all files defined in each manifest exists locally.

    If a file does not exist, that manifest is marked for updating.
    """
    missing_files = []
    for manifestfile in get_manifest_list():
        manifest = get_manifest(manifestfile)
        if not manifest:
            continue

        for item in manifest["files"]:
            if not os.path.exists(item["file"]):
                missing_files.append(manifestfile)

    if len(missing_files) == 0:
        return False

    return missing_files


def update_from_manifests():
    """
    Using all manifests in `src/manifests`, grabs the latest version of each manifest,
    then checks to see if the latest version is newer than current.

    If it is, it will update all files defined in the manifest, then the manifest itself.

    Will not overwrite identical files.
    """
    for manifestfile in get_manifest_list():
        manifest = get_manifest(manifestfile)
        if not manifest:
            continue

        new_manifest = get_updated_manifest(manifest)

        if not new_manifest or new_manifest == manifest:
            continue

        logging.info(f"Updating from {manifestfile}...")
        for item in new_manifest["files"]:
            do_file(item)

        with open(f"{MANIFEST_DIR}{manifestfile}", "w") as file:
            file.write(json.dumps(new_manifest, indent=4))


def do_file(item: dict, force: bool = False):
    """Update a file.

    :param item: A `dict` with the file's information.

    :param force: Whether to skip checking if the file is identical before updating.

    See src/manifests/rasbot.manifest for samples:
    ```
    item {
        "file": "relative path to file",
        "source": "remote source, likely githubusercontent
    }
    ```
    """
    file = item["file"]
    source = item["source"]

    if "$BRANCH" in source:
        source = source.replace("$BRANCH", rasbot_branch)

    verify_folder_exists(file)

    # if the file doesn't exist don't write anything
    req = requests.get(source)
    if req.status_code < 200 or req.status_code >= 300:
        logging.info("Failed to fetch: ignoring...")
        return
    remote = req.text

    if not force:
        if os.path.exists(file):
            with io.open(file, "r", encoding="utf8") as localfile:
                local = localfile.read()

            shalocal = hashlib.sha256(str.encode(local)).hexdigest()
            sharemote = hashlib.sha256(str.encode(remote)).hexdigest()

            if shalocal == sharemote:
                return

    # if it doesn't or the files aren't identical overwrite with remote
    logging.info(f"Updating {file}...")
    with io.open(file, "w", encoding="utf8") as localfile:
        localfile.write(remote)


def verify_folder_exists(path: str):
    """Create `path` if it does not exist.

    :param path: The path to verify the entire trace exists for.
    """
    folder_list = path.split("/")
    folders = []
    for i, name in enumerate(folder_list):
        # assume file and end of path reached, break
        if "." in name:
            break

        folder = f"{'/'.join(folder_list[:i+1])}"
        folders.append(folder)

    # Verify config folder exists
    for folder in folders:
        if not os.path.exists(folder):
            os.mkdir(folder)


if __name__ == "__main__":
    main()
