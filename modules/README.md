<div align="center">

# Creating your own custom module

</div>

Name the file after your module: `sample.py`.<br/>
You can then reference your module as the response of a command, for example, `r!cmdadd sample &sample&`.

Your module must have a `Module` class that extends `commands.BaseModule`.<br/>
The code that replaces `&sample&` in the response goes in a method called `main` that accepts **one** argument: the TwitchBot instance.<br/>
You can use this TwitchBot instance to get command arguments and information about the commanding user.<br/>

Your module can have a help message, stored in the `helpmsg` static variable.
Whatever it contains will be shown if the method is provided as an argument for the `help` command.<br/>

Otherwise, you're free to add whatever you want to the module, as long as you know how to code it.

**Be very careful as this can be abused!**<br/>
*A sample module is available as `sample.py`.*
