# mskipkey
Password management tool for Android

# Create a virtual environment
python -m venv path/to/my/venv

## Create e project directory in the virtual environment

# Install kivy and kivyMD
pip install kivy==2.0.0rc3
pip install kivymd

**See [Cython](https://cython.org/)** Cython is an optimising static compiler for both the Python programming language and the extended Cython programming language (based on Pyrex).

# Install buildozer for Android package
[buildozer documentation](https://buildozer.readthedocs.io/en/latest/)
pip install buildozer

### Install other packages
sudo apt install -y git zip unzip openjdk-8-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev

## Init buildozer
buildozer init and configure buildozer settings file: `buildozer.spec`
    
    # (list) Application requirements
    # comma separated e.g. requirements = sqlite3,kivy
    requirements = python3,kivy,kivymd,certifi

## Internet permissions
    # (list) Permissions
    android.permissions = INTERNET


## First run

buildozer -v android debug

## Run and deploy 
buildozer -v android debug deploy run logcat > my_log.txt

### Warnings
1. \[WARNING\]: lld not found, linking without it. Consider installing lld if linker errors occur.
1. reStructuredText renderer [class kivy.uix.rst.RstDocument](https://kivy.org/doc/stable/api-kivy.uix.rst.html?highlight=rstdocument#kivy.uix.rst.RstDocument) is not supported and the app doesn't run on the phone
2. Kivy ActionBar limitations:
   1. No more than 5 ActionButtons is supported, but android app crashes in managing the menu overlap with other contents: so you must avoid adding more than the number of buttons fitting the app width.
   2. ActionGroup is not supported 
   3. ActionOverflow is supported, but it seems have no effect, so avoid using it