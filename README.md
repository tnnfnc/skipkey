# SkipKey, author: Franco Toninato
SkipKey is a simple program for personal password management developed in python with a kivy graphical user interface.
The design principles are:
- a password for encrypting the file containing all user passwords,
- a user 'casual code' (like a password) used internally to derive passwords automatically (mode=auto)
BOTH password and casual code are needed: the password is responsible to protect the file, the casual code is responsible for password generating and encrypting.
To enhance security no checks was implemented on the casual code.
The strenght of this program is fully exploited when user choses to have only generated passwords, anycase he/she can choose custom passwords for different accounts and they will be encrypted using the casual code as the cipher secret key.
To be more precise the cryptographic secrets are always derived by user password or casual code through one of the recommended algorithms (PBKDF2).
During a program run the secret keys are wrapped by temporary random keys valid only for one that run: this increases security against reading the memory in the attempt of stealing them.

How to install:

How to compile (pyinstaller)

How to use:

Future enhance:

