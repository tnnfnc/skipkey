import gettext
import os


current_dir = os.path.dirname(os.path.realpath(__file__))
icons_dir = '%s\data\icons' % (current_dir)
data_dir = '%s\data' % (current_dir)
locale_dir = '%s\locale' % (current_dir)

# Translations
def translate(languages=['il']):
    def f(x): return x
    try:
        lang = gettext.translation(
            'skipkey', localedir=locale_dir, languages=languages)
        lang.install()
    except FileNotFoundError as e:
        # print(f'No translation found: {e}')
        lang = gettext.NullTranslations(fp=None)
        lang.install()
    finally:
        f = lang.gettext
    return f

# def translate(languages=['it']):
#     def f(x): return x
#     try:
#         it = gettext.translation(
#             'skipkey', localedir=locale_dir, languages=languages)
#         it.install()
#         f = it.gettext
#     except FileNotFoundError as e:
#         print(f'No translation found: {e}')
#     return f


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
