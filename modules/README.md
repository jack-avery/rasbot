<div align="center">

# Creating your own custom module

</div>

Name the file after your module: `thing.py`.<br/>
You can then reference your module as the response of a command, for example, `r!cmdadd thing &thing&`.

Your module must have a `Module` class that extends `commands.BaseModule`.<br/>
The code that replaces `&thing&` goes in a method called `main` that accepts **one** argument: the TwitchBot instance.<br/>
You can use this TwitchBot instance to get command arguments and information about the commanding user.<br/>

Your module can have a help message, stored in the `helpmsg` static variable.
Whatever it contains will be shown if the method is provided as an argument for the `help` command.<br/>

Otherwise, you're free to add whatever you want to the module, as long as you know how to code it.

__**Be very careful as this can be abused!**__
