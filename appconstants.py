import os

current_dir = os.path.dirname(os.path.realpath(__file__))
icons_dir = '%s\data\icons' % (current_dir)
data_dir = '%s\data' % (current_dir)
locale_dir = '%s\locale' % (current_dir)

# Command specification
COPY = 'copy'
SAVE = 'save'
DELETE = 'delete'
ADD = 'add'
RENAME = 'rename'
UPDATE = 'update'
APPEND = 'append'
INFO = 'info'
IMPORT = 'import'
EXPORT = 'export'
# Screen Names
ENTER = 'Enter'
LIST = 'List'
EDIT = 'Edit'
CHANGES = 'changes'
IMPORT = 'import'
EXPORT = 'export'
# Constants:
ITERATIONS = 100000  # key generation from seed
# App
ICON = 'skip.png'
TAGS = ('...')  # Default for all tags

item_template = {
    'name': '',  # new name
    'url': '',  # Check valid url
    'login': '',  # Any string
    'email': '',  # @-mail
    'description': '',  # Any string
    'tag': '',  # Any string
    'color': '',  # Basic colors as string
    'created': '',  # Date
    'changed': '',  # Date
    'auto': '',  # True, False=user
    'length': '',  # Integer
    'letters': '',  # True / False
    'numbers': '',  # At least [0 length]
    'symbols': '',  # At least [0 length]
    'password': '',  # User encrypted password or salt Base64 encoded
    'history': ''  # Record history - not yet managed
}

index=('name', 'tag', 'description', 'login', 'url', 'email')