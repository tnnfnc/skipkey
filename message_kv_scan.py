# -*- coding: utf-8 -*-
"""
Created on Thu Jan 31 08:39:17 2019

@author: Franco Toninato
# ~
"""
# Look for files into a dir
# Create a new file and append all files into that
# Loop at files

# Include your modules resources:
import re
import os
import sys
sys.path.append("C:\\Users\\it280\\Google Drive\\Projects\\python")
sys.path.append("C:\\Users\\franco\\Google Drive\\Projects\\python\\demos")
sys.path.append("C:\\Users\\blufr\\Google Drive\\Projects\\python\\demos")
sys.path.append("C:\\Users\\it280\\Google Drive\\Projects\\python\\demos")
import utility
# Import your modules
f_ext = 'py'

HEADER = '# {} \n'
print("This program extracts all text from files in the selected directory into a new file \
appending the results in a python .py file.")
print(f"Current directory: {os.getcwd()}\nSet the directory to explore:\n")
#home_folder = 'C:\\Users\\IT280\\Dropbox\\Franco\\The modern Python 3'

home_folder = utility.file_manager_ui(os.getcwd())
merge_file = 'messages.txt'

while True:
    f_ext = input(
        'Write the file extension: py for python, or kv for kivy graphic script: ')
    if not f_ext:
        print(f"{f_ext} is not a valid name!")
    else:
        break
while True:
    merge_file = input(f'Write the main class file name: es. {merge_file}.py ')
    if not merge_file:
        print(f"{merge_file} is not a valid name!")
    else:
        break

if merge_file.endswith('.py'):
    n = merge_file[:-3]
else:
    n = merge_file
merge_file = f'{n}_{f_ext}_messages.py'

f_path = os.path.join(home_folder, merge_file)

# Scan dir and build an DirEntry array
f_list = []
with os.scandir(home_folder) as it:
    for entry in it:
        # Is a file
        if not entry.name.startswith('.') and entry.is_file() and entry.name[-2:] == f_ext:
            f_list.append(entry)

# Sort in place by creation date
f_list.sort(key=lambda k: k.stat().st_ctime)

log = []

pattern = re.compile("[^_]_\((.*?)\)")

with open(f_path, mode='w') as f_w:
    f_w.write("""# Translations
def _(text):
    return text
""")
    for entry in f_list:
        log.append(f"{entry.stat().st_ctime} {entry.name}")
        with open(entry.path, mode='rt') as f_r:
            h = HEADER.format(entry.name)
            f_w.write(h)
            content = f_r.read()
            for text in re.findall(pattern=pattern, string=content):
                f_w.write(f'_({text})\n')


for i, l in enumerate(log):
    print(f" merged {i+1} of {len(log)}: {l}")
print(f'FILE COMPLETED: {f_path}')
