<div align="center">

# Using Modules
</div>

To use modules, all you need to do is drop the module -- named similar to `something.py` -- into this folder and then mention it in a command.

You can mention modules in commands by surrounding the name of it in **ampersands**: `&module&`
> e.g. `r!cmdadd help &help&` would create a command using the `help` module.

<div align="center">

# Module Configs
</div>

Some modules use a config to store parameters on how they should work. Modules that use a config store it under `userdata/[your Twitch ID]/modules`. By default, the only configs in here will be for `cmdadd` and `prefix`.

It's recommended you look at the module (it will have the same name in `modules`, just with the `.py` suffix, or given **Type** "Python File" by Windows) in your text editor of choice to see a better description of each option before changing anything.

Some modules require configuration before they can work, e.g. the `request` module which requires you to grant it some credentials for interfacing with the osu! API.

> Modules only create their default config when first imported, so you'll have to create a command with it first to create the file.

---

<div align="center">

# Creating your own custom module
</div>

*For advanced users, a sample module showing most things with comments is available as `sample.py`.*

Name the file after your module: `sample.py`.<br/>
You can then reference your module as the response of a command, for example, `r!cmdadd sample &sample&`.

Your module must have a `Module` class that extends `commands.BaseModule`.<br/>
> If you're overriding \_\_init__, be sure to call BaseModule.\_\_init__(self, bot, name).

The code that replaces `&sample&` in the response goes in a method called `main`.<br/>
You can find the `TwitchBot` instance as `self.bot`.<br/>

If your module intends to use arguments, get them by setting the `consume` static variable and calling `self.get_args(message)`.<br/>
*This helps bunch up arguments together, allowing multiple modules in the same command to interact predictably.*

Your module can have a help message, stored in the `helpmsg` static variable.<br/>
Whatever it contains will be shown if the method is provided as an argument for the `help` command.

Otherwise, you're free to add whatever you want to the module, as long as you know how to code it.
> Wiki page containing more useful information about modules coming soon™️!

### **Be very careful as this can be abused!**<br/>

![image](https://user-images.githubusercontent.com/47289484/193102564-6245c687-6e25-4f90-a1a8-37d6d2fb91da.png)
