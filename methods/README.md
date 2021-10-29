# Creating your own custom method:
**You can take a look at `methods/echofull.py` for an example**

Name the file after your method like `methodname.py`.
For example, if you wanted a method to be called using `&thing&`, you would name your file `thing.py`.
You can then add `&&` code for your method to the response of a command, for example, `r!cmdadd thing 5 &thing&`.

Your file must have a class called `Method` that extends `commands.BaseMethod`.
The code to run on command goes in a method called `main` that accepts **one** argument.
The argument being passed is the `TwitchBot` object, including all variables attached.
>Whatever it returns will be sent to chat.

Your method can have a help message, returned from the `help` method.
Whatever it returns will be returned if the method is provided as an argument for the `help` command.
>Example: `r!help thing` would print the help message for `thing.py`, if it exists.

Otherwise, you're free to add whatever you want to the method, as long as you know how to code it.

__**Be very careful as this can be abused!**__