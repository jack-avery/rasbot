<div align="center">

# rasbot

</div>

**rasbot** is a self-hosted Twitch bot that provides an easy-to-use interface for extending your bot with custom Python code.<br/>

rasbot is intended to run locally, so it has access to your Twitch emotes, and companion applications, such as [osu!StreamCompanion](https://github.com/Piotrekol/StreamCompanion):

![image](https://cdn.discordapp.com/attachments/488850419301220352/1063993678575714335/image.png)

# How to Use ✍️
1. Download and install [Python version 3.11.0+](https://www.python.org/downloads/), ensuring you tick "Add python.exe to PATH" at the bottom of the first screen.
2. Download the Source Code:
> Using [git](https://git-scm.com/downloads): `git clone https://github.com/jack-avery/rasbot` <br/>
> Or, click on **Code** at the top right and **Download ZIP**.
3. Run `main.py`. If this is your first time using rasbot, you will be ran through a guided setup for your authentication.

*If you set up rasbot correctly, it will log some information and print something similar to:*
```
Joined #raspy_on_osu! (57511738)
```

> You will be asked about telemetry when you first start rasbot. I would appreciate at least error reporting. <br/>
> **All telemetry is completely anonymous.** You can see exactly what is sent [here](https://github.com/jack-avery/rasbot/blob/main/src/telemetry.py).

> rasbot checks for and performs updates automatically with each start and will let you know if one is ready! <br/>
> You can disable auto-update checking and notifications **entirely** in `update.py`.

# Managing Commands 📋

```
Create a command:
r!cmd add <command name> <cooldown?> <parameters?> <response>

Edit a command:
r!cmd edit <command name> <name/cooldown/modonly/hidden/response> <value?>

Remove a command:
r!cmd remove <name>
```

Valid parameters include:<br/>
`-modonly`: Set the command to be moderator/broadcaster use only.<br/>
`-hidden`: Set the command to be hidden from the `help` command.

# Modules 📦
rasbot is designed modularly and allows you to add to the base application easily with *"plug-and-play"*-style extensions. You can see some sample modules, **including** built-in functions in the `modules` folder.

To include a module as part of a command, encompass the module name in `%`, e.g.:
```
r!cmd add np %np%
```

*For documentation on configuring modules or creating your own, see [this](https://github.com/jack-avery/rasbot/blob/master/modules/README.md).*

# Bug reports & feature suggestions 🐛
Has something gone **horribly** wrong? *Or do you just think something's missing?*

Feel free to [create a new issue](https://github.com/jack-avery/rasbot/issues), join the [Discord](https://discord.gg/qpyT4zx), or message me directly on Discord about it: `raspy#0292`.

> If you're reporting a bug, it's most useful to me if you can get what the console outputs for me.<br/>
> If rasbot is crashing instantly on launch, you'll need to start it from Command Prompt / another terminal:<br/>
> You can use the command `main.py --debug` for rasbot to show more information during startup.
