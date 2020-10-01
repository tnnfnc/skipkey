# SkipKey, a program for personal password management

author: Franco Toninato

SkipKey is a simple program for personal password management developed in python with [kivy](https://kivy.org "Kivy") graphical user interface.
The design principles are:
- a password for encrypting the file containing all user passwords,
- a user 'casual code' (like a password) used internally to derive passwords automatically (if the password 'mode'preference is set to 'auto').

BOTH *password* and *casual `code`* are needed and must be remembered by the user: the password is responsible of protecting the file, the casual code is responsible of password generating ('auto' mode) or encrypting ('user' mode).
To enhance security no checks was implemented on password or casual code input.

The strenght of this program is fully exploited when user choses to have only generated passwords, anyway he/she can choose custom passwords for specific accounts.
To be more precise the cryptographic secrets are always derived by user password or casual code through one of the recommended algorithms (PBKDF2).
During a program run the secret keys are wrapped by temporary random keys valid only for one that run: this increases security against reading the memory in the attempt of stealing them.

The app comprises **start** screen, a **list** screen (the main one), an **edit** account screen.

## How to lauch the app
After cloning the repository the app is launched by:

	$python3>main.py
or

	$python3>skipkey.py

### GUI
Make sure you have the following python modules installed in your python environment:
* [kivy](https://kivy.org "Kivy"), graphycal user interface,
## Start screen
It is the screen you see when start app: on the right corner there are file operations: **open**, **create**, **quit**, **delete recent files**. The list of recently opened files is available clicking on the **recent files** spinner widget.
### Settings
By pressing 'F1' the app settings are displayed. At present you can change also 'Kivy' settings. Not all new values are effective on the current app run. 
### Login
It is the popup where user must input *password* and the *seed for password generation*. When create a new file a password confirmation is requested. When opening an existing file and the password provided by the user isn't right, an error message is pop up to the user.
## List screen
This is the main screen and all app's available actions is addressed from there. From this screen you **add** your accounts and manage them. To **manage** an existing account you click on the item and select the option **edit**. 
#### How to use your accounts
* Find the account you want to login into by writing few letters in the search field,
* click on the proper item, then a _popup-menu_ will appear pointing to it.
##### Menu options:
All these menu options make the corresponding datum available in the memory and ready to be pasted into the target login field.
There are two option for app settings *Login auto-completion*:
* If _Disabled_ the login datum is made available to the system clipboard for a short time, then cleared.
* If _Enabled_ the login datum is made available to the program memory and can be input to the target field by a double click on it, it is then cleared.
 According to the _popup-menu_ option selected, the following data are made available for pasting into their target:
    - account url,
    - account user, 
    - account password 
    - full login: 'user' 'tab' 'password'.
### Copy to
Menu item: copy the current content to another file. Before copying the user must input a passord and a casual code. The app's current file does not change to the new one. 
FAQ 'How to change my password and casual code?'
### Export to
Menu item: export the content as a .csv file with password in plain text. This option can be useful if you decide to print a snapshot of all your accounts to save them into a secure place. Otherwise this option can be used to have a standard .csv file to feed another password management app.
### Import from
Menu item: import existing accounts from another password management app. The imported file must be a .csv file with header. Before importing you must define the matching between the **skipkey** header and the **other app**'s one. 
### Info
Menu item: display information about the current file and settings.
### Changes
Menu item: this screen provides the list of changes during the current program run. You can select the change and undo, please note that 'undo of undo' is not allowed.
## Edit screen
This is the screen you get when touches the **edit** button in the bubble menu over a specific access item in the *list* screen. Only the name and password fields are mandatory. The *name* is the key of the access item, so if you change it and save, a new identical account item will be created with the new name. To rename an item you must rename it and then delete the previous one.
# More to do
## Store more than one secret for each access
Sometimes it's useful to have more than one secret information, generated or user's defined, to be stored inside an access. For example a password and a pin.
## Installation checker
First time a file is opened or created an installation check is made and stored inside the file, hashing of installed files. In such a way the user can verify the installation integrity.
# On Windows systems:
In order to making skipkey available as an executable on Windows systems it is possible to compile it with [pyinstaller](https://www.pyinstaller.org/).

Here you are my packaging hint with pyinstaller to avoiding hassles:

Note:
If you use [conda](https://www.anaconda.com/) environments or python virtual environments please install pyinstaller into the environment of the app you want to package.
* Make a <my_project> directory in the environment you use for compiling the app by cloning the git repository.
* Make a <my_package> directory in the environment where you decided to have the compiled app.
* Open a terminal and change the current directory to the <my_package> 
* Activate your virtual environment
* Run `pyinstaller` command from the **virtual environment** including the following options.
### Details
Run the command without line breaks, enclosing values between quotation marks: " ", remember to substitute windows backslash `\` to slash `/` in the following.

Command/option | value | Result
--- | --- | ---
`../Scripts/pyinstaller` | `../<my_project>/main.py`
--name | `<my app>`| app executable name
--noconsole | launch app without a terminal
--onedir | build the app into one dir
--paths |`../<my_project>` | relative path to the project directory
--add-data |`../<my_project>/*.json; . `| add the .json files
--add-data |`../<my_project>/locale/<lang>/LC_MESSAGES/*; locale/<lang>/LC_MESSAGES/.` | add localizations files
--add-data |`../<my_project>/data/icons/*; data/icons/.` | add icons
--add-data |`../<my_project>/data/\*.*; data/.` | add other resources
--add-data |`../<my_project>/kv/*;kv/.` | add .kv kivy lang files
--add-data |`../<my_project>/*.kv;.` | add .kv kivy lang files
--icon | `../<my_project>/data/icons/skip_big.ico`| add the icon to the .exe executable
--hidden-import | `win32timezone` | add dll
--hidden-import | `pkg_resources.py2_warn` | add python 2 adapter

