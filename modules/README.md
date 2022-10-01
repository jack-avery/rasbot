<div align="center">

# Creating your own custom module

</div>

Name the file after your module: `sample.py`.<br/>
You can then reference your module as the response of a command, for example, `r!cmdadd sample &sample&`.

Your module must have a `Module` class that extends `commands.BaseModule`.<br/>
> If you're overriding \_\_init__, be sure to call BaseModule.\_\_init__(self, bot).

The code that replaces `&sample&` in the response goes in a method called `main`.<br/>
You can find the `TwitchBot` instance as `self.bot`.<br/>

> Wiki page containing useful information about this coming soon!

Your module can have a help message, stored in the `helpmsg` static variable.
Whatever it contains will be shown if the method is provided as an argument for the `help` command.<br/>

Otherwise, you're free to add whatever you want to the module, as long as you know how to code it.

**Be very careful as this can be abused!**<br/>
*A sample module is available as `sample.py`.*

![firefox_p0K7PPEJBs](https://user-images.githubusercontent.com/47289484/193102564-6245c687-6e25-4f90-a1a8-37d6d2fb91da.png)
