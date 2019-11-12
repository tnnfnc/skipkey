# SkipKey, a program for personal password management

author: Franco Toninato

SkipKey is a simple program for personal password management developed in python with [kivy](https://kivy.org "Kivy") graphical user interface.
The design principles are:
- a password for encrypting the file containing all user passwords,
- a user 'casual code' (like a password) used internally to derive passwords automatically (if the password 'mode'preference is set to 'auto').

BOTH password and casual code are needed: the password is responsible of protecting the file, the casual code is responsible of password generating ('auto' mode) or encrypting ('user' mode).
To enhance security no checks was implemented on password or casual code input.

The strenght of this program is fully exploited when user choses to have only generated passwords, anyway he/she can choose custom passwords for specific accounts.
To be more precise the cryptographic secrets are always derived by user password or casual code through one of the recommended algorithms (PBKDF2).
During a program run the secret keys are wrapped by temporary random keys valid only for one that run: this increases security against reading the memory in the attempt of stealing them.

The app comprises **start** screen, a **list** screen (the main one), an **edit** account screen.

## Start screen
It is the screen you see when start app: on the right corner there are file operations: **open**, **create**, **quit**, **delete recent files**. The list of recently opened files is available clicking on the **recent files** spinner widget.

### login
It is the popup where user must input *password* and the *seed for password generation*. When create a new file a password confirmation is requested. When opening an existing file and the password provided by the user isn't right, an error message is pop up to the user.

## List screen
This is the main screen and all app's available actions is addressed from there.
### Copy to
### Export to
### Import from
### Info
### Changes

## Edit screen
This is the screen you get when touches the **edit** button in the bubble menu over a specific access item in the *list* screen. Only the name and password fields are mandatory. The *name* is the key of the access item, so if you change it and save, a new identical account item will be created with the new name. To rename an item you must rename it and then delete the previous one.

## How to install:
How to compile (pyinstaller):

Packaging with pyinstaller 'golden rules' for avoiding hassles:

1) If you use conda environments please install pyinstaller into the environment of the app you wanto to package. Then, when pakaging follows these rules:
    a) change your directory to a <mydir> created in the app conda environment where package will be built.
	b) launch the pyinstaller.exe instance installed in your conda app environment and compile the app.
	c) launch the app from its directory
	
FINAL SCRIPT with local pyinstaller:
environment = skipkey

..\Scripts\pyinstaller --name skipkey --noconsole --paths="..\skipkey" --add-data="..\skipkey\*.json;." --add-data="..\skipkey\locale\it\LC_MESSAGES\*;locale\it\LC_MESSAGES\." --add-data="..\skipkey\data\icons\*;data\icons\." --add-data="..\skipkey\data\*.*;data\." --add-data="..\skipkey\kv\*.*;kv\." --icon ..\skipkey\data\icons\skip_big.ico --hidden-import=win32timezone ..\skipkey\skipkey.py

How to use:

Future enhance:
Make it available on Android devices.
