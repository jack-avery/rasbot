<div align="center">

# rasbot

</div>

**rasbot** is a Python-based Twitch bot lets you see and modify everything going on behind the scenes.<br/>

rasbot is intended to run locally on your account so it has access to your Twitch emotes and any potential companion applications, such as [osu!StreamCompanion](https://github.com/Piotrekol/StreamCompanion):

![image](https://cdn.discordapp.com/attachments/488850419301220352/1024615808879579188/unknown.png)

# How to Use ✍️
1. Download and install [Python version 3.11.0+](https://www.python.org/downloads/), ensuring you tick "Add python.exe to PATH" at the bottom of the first screen.
2. Download the Source Code:
> Using [git](https://git-scm.com/downloads): `git clone https://github.com/jack-avery/rasbot` <br/>
> Or, click on **Code** at the top right and **Download ZIP**.
3. Run `setup.py` and follow the steps to set up your authentication.
4. Run `bot.py`.

*If you set up rasbot correctly, it will log some information and print something similar to:*
```
Joined #raspy_on_osu! (57511738)
```

# Managing Commands 📋

```
Create/update a command:
r!cmdadd <name> <cooldown?> <parameters?> <response>

Remove a command:
r!cmddel <name>
```

Valid parameters include:<br/>
`-modonly`: Set the command to be moderator/broadcaster use only.<br/>
`-hidden`: Set the command to be hidden from the `help` method.

# Modules 📦
rasbot is designed modularly and allows you to add to the base application easily with *"plug-and-play"*-style extensions. You can see some sample modules, **including** built-in functions in the `modules` folder.

To include a module as part of a command, encompass the module name in `&`, e.g.:
```
r!cmdadd np &np&
```

*For documentation on configuring modules or creating your own, see [this](https://github.com/jack-avery/rasbot/blob/master/modules/README.md).*

# Bug reports & feature suggestions 🐛
Has something gone **horribly** wrong? *Or do you just think something's missing?*

Feel free to [create a new issue](https://github.com/jack-avery/rasbot/issues), join the [Discord](https://discord.gg/qpyT4zx), or message me directly on Discord about it: `raspy#0292`.