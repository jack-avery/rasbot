<div align="center">

# rasbot

</div>

## This project is end-of-life; I am no longer maintaining this project, pending an eventual rewrite from the ground-up. Thank you to all of the users who enjoyed using this while it was actively updated. It should continue to work for the foreseeable future.

**rasbot** is a self-hosted Twitch bot that provides an easy-to-use interface for extending your bot with custom Python code.<br/>

rasbot is intended to run locally, so it has access to your Twitch emotes, and companion applications, such as [osu!StreamCompanion](https://github.com/Piotrekol/StreamCompanion).

Find rasbot useful? [Buy me a coffee ☕](https://ko-fi.com/raspy)!

# How to Use ✍️

rasbot is an old project, and its' functionality depends on pip being easily usable.
**As a result, rasbot only works on Windows.**

1. Download and install [Python version 3.12.0+](https://www.python.org/downloads/), ensuring you tick "Add python.exe to PATH" at the bottom of the first screen.
2. Download the Source Code:
> Using [git](https://git-scm.com/downloads): `git clone https://github.com/jack-avery/rasbot` <br/>
> Or, click on **Code** at the top right and **Download ZIP**.
3. Run `main.py`. If this is your first time using rasbot, you will be ran through a guided setup for your authentication.

*If you set up rasbot correctly, it will log some information and print something similar to:*
```
Joined #raspy_on_osu! (57511738)
```

> rasbot checks for and performs updates automatically with each start and will let you know if one is ready! <br/>
> You can disable auto-update checking and notifications **entirely** in `update.py`.

# Managing Commands 📋

```
Create a command:
r!cmd add <command name> <cooldown?> <parameters?> <response>

Edit a command:
r!cmd edit <command name> <name/cooldown/privilege/hidden/response> <value?>

Remove a command:
r!cmd remove <name>
```

Valid parameters include:<br/>
`-{status}only`: Set the command to be usable by {status} only, e.g. `-modonly` for Moderators and above, `-subonly` for Subscribers and above.<br/>
`-hidden`: Set the command to be hidden from the `help` command.

# Modules 📦
rasbot is designed modularly and allows you to add to the base application easily with *"plug-and-play"*-style extensions. You can see some sample modules, **including** built-in functions in the `modules` folder.

To include a module as part of a command, encompass the module name in `%`, e.g.:
```
r!cmd add np %osu/np%
```

*For documentation on configuring modules or creating your own, see [this](https://github.com/jack-avery/rasbot/blob/master/modules/README.md).*
