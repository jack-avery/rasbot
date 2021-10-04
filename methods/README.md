# Creating your own custom method:

Name the file after your method like `methodname.py`.
For example, if you wanted a method to be called using `&thing&`, you would name your file `thing.py`.
You can then add `&&` code for your method to the response of a command, for example, `r!cmdadd thing 5 &thing&`.

Your method must be called `main`, and accept **one** argument.
The argument being passed is the `TwitchBot` object, including all variables attached.
Whatever it returns will be sent to chat. It doesn't *need* to return anything, but if it does, it **must** be a string.

Otherwise, you're free to add whatever you want to the method, as long as you know how to code it.

__**Be very careful as this can be abused!**__