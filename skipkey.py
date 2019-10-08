"""SkipKey: a help to password management
    Program for password management.
    Conventions:

        - Define kv field as _<prefix>_<name>, prefixes:

            _inp_ : input text widget
            _lab_ : label widgets
            _spi_ : spinner widget
            _out_ : output text widget
            _wid_ : widget container
            _btn_ : button widget
            _swi_ : switch widget
            _scr_ : scroll widget
            _prb_ : progress bar widget

        - Define kivy properties prefixes:

            pr_<name> :
            pr_<name>_wid : container widget property

        - Field convention:

            Fields are dictionary key - value, the input field in a .kv screen
            is _inp_key, the kivy property is pr_key.

    """
#import kivy_environment
import threading
import kivy
import base64
import json
import re
from kivy.core.clipboard import Clipboard
import kivy.metrics as metrix
from kivy.metrics import dp
from kivy.graphics import InstructionGroup
from kivy.graphics import Rectangle
from kivy.graphics import Color
from kivy.factory import Factory
from kivy.properties import StringProperty
from kivy.properties import ObjectProperty
from kivy.lang.builder import Builder
from kivy.uix.bubble import Bubble
from kivy.uix.spinner import Spinner
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.screenmanager import ScreenManager
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.app import App
from datetime import datetime, timedelta
from daemon import LoginDaemon
from polyitemlist import ItemList, ItemComposite, Comparison, ProgressItem
# from comparator import Comparator, Comparison
# from filemanager import decision as decision
# from filemanager import message as message
# from filemanager import message, decision
from filemanager import OpenFilePopup, SaveFilePopup, message, decision
import cryptofachade
import passwordmeter
import model
import gettext
import os
import sys
dummy = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dummy)

# from fields import Comparate
kivy.require('1.11.0')  # Current kivy version

MAJOR = 1
MINOR = 0
MICRO = 3
RELEASE = True

__version__ = '%d.%d.%d' % (MAJOR, MINOR, MICRO)

# Global
current_dir = os.path.dirname(os.path.realpath(__file__))


# print(f'Current dir: {current_dir}')
icons_dir = '%s\data\icons' % (current_dir)
data_dir = '%s\data' % (current_dir)

# Translations


locale_dir = '%s\locale' % (current_dir)
# locale_dir = 'locale'
try:
    it = gettext.translation('skipkey', localedir=locale_dir, languages=['it'])
    it.install()
    _ = it.gettext
except FileNotFoundError as e:
    def _(x): return x
    print(f'No translation found: {e}')


def dp(pix):
    return metrix.dp(pix)


Builder.load_file('kv/commons.kv')


''' Tag list:
1) initialized at new file or at opening from all values found in items list
2) updated from the EditTagPopup
3) accessed everywere is is needed
4) tag element must be present, it disables all filters
'''
TAGS = _('all...')  # Default standinf for all tags
# Command specification
COPY = 'copy'
SAVE = 'save'
DELETE = 'delete'
ADD = 'add'
RENAME = 'rename'
UPDATE = 'update'
APPEND = 'append'
INFO = 'info'
IMPORT = 'import'  # & screen name
EXPORT = 'export'  # & screen name
# Screen Names
ENTER = 'Enter'
LIST = 'List'
EDIT = 'Edit'
CHANGES = 'changes'
# Constants:
ITERATIONS = 100000  # key generation from seed
# App
ICON = 'skip.png'

# =============================================================================
# Kivy config
# =============================================================================


def selection(widget, select=False):
    group = len(widget.canvas.get_group('sel')) > 0
    if not group:
        sel = InstructionGroup(group='sel')
        sel.add(Color(1, 1, 1, 0.3))
        sel.add(Rectangle(pos=widget.pos, size=widget.size))
    with widget.canvas:
        if select and not group:
            widget.canvas.add(sel)
        elif not select and group:
            widget.canvas.remove_group('sel')
        else:
            pass  # Nothing to do here!


# Builder.load_file('commons.kv')

def hh_mm_ss(seconds):
    hh = int(seconds/3600)
    mm = int((seconds % 3600)/60)
    ss = int((seconds % 3600) % 60)
    out = 'Timeout: {hh:02}:{mm:02}:{ss:02}'.format(hh=hh, mm=mm, ss=ss)
    return out


'''Items:
1) initialized at new file or at opening from the items
2) updated from the Edit screen
3) accessed everywere is is needed
'''
new_item = model.new_item
test_items = []
test_items.extend([
    new_item(name='item 1', tag='Free'),
    new_item(name='item 2', tag='Free'),
    new_item(name='item 3', tag='Web'),
    new_item(name='item 4', tag='Free'),
    new_item(name='item 5', tag='Web'),
    new_item(name='item 6', tag='Free'),
    new_item(name='item 7', tag='Gov'),
    new_item(name='item 8', tag='Gov')]
)
'''Column mask'''
# item_mask = ('name', 'login', 'url')
item_mask = {'name': dp(200), 'login': dp(200), 'url': ''}
# item_mask = None


class SecurityException(Exception):

    def __init__(self, *args, **kwargs):
        super(SecurityException, self).__init__(*args, **kwargs)


class OpenFile(OpenFilePopup):

    def __init__(self, *args, **kwargs):
        super(OpenFile, self).__init__(**kwargs)
        self.filechooser.dirselect = False

    def cmd_load(self, path, selection):
        '''Call login to decipher file'''
        if selection:
            popup = LoginPopup()
            popup.title = _('Login to: %s') % (", ".join(selection))
            popup.open()
            popup.file = selection
            self.dismiss()
        return False

    def cmd_cancel(self):
        #        Window.width += 1
        self.dismiss()

    def is_valid(self, folder, file):
        return True


class ImportFile(OpenFilePopup):

    def __init__(self, *args, **kwargs):
        super(ImportFile, self).__init__(**kwargs)

    def cmd_load(self, path, selection):
        '''Call the import screen'''
        app = App.get_running_app()
        if app and selection:
            if isinstance(selection, list):
                selection = selection[0]
            app.root.get_screen(IMPORT).file = selection
            app.root.transition.direction = 'left'
            app.root.current = IMPORT
            self.dismiss()
        return False

    def is_valid(self, folder, file):
        return str(file).endswith('csv') or str(file).endswith('txt')


class SaveFile(SaveFilePopup):

    def __init__(self, *args, **kwargs):
        super(SaveFile, self).__init__(**kwargs)
        self.filechooser.dirselect = False
        self.mode = SAVE  # or NEW

    def cmd_save(self, path, selection):
        if selection:
            if not os.path.dirname(selection):
                selection = '%s\\%s' % (path, selection)
            if not os.path.exists(selection):
                self.do_save(selection)
            else:
                decision(
                    self.title,
                    _('%s exists:\noverwrite?') % (
                        os.path.basename(selection)),
                    fn_ok=self.do_save,
                    ok_kwargs={'file': selection, })
        return False

    def do_save(self, file):
        f = file
        popup = CipherPopup()
        popup.title = f'{self.title} to: {f}'
        popup.file = f
        popup.mode = self.mode
        popup.open()
        self.dismiss()

    def cmd_cancel(self):
        self.dismiss()


class ExportFile(SaveFilePopup):

    def __init__(self, *args, **kwargs):
        super(ExportFile, self).__init__(**kwargs)

    def cmd_save(self, path, selection):
        if selection:
            if not os.path.dirname(selection):
                selection = '%s\\%s' % (path, selection)
            if not os.path.exists(selection):
                self.do_save(selection)
            else:
                decision(
                    self.title,
                    _('%s exists:\noverwrite?') % (
                        os.path.basename(selection)),
                    fn_ok=self.do_save,
                    ok_kwargs={'file': selection, })
        return False

    def do_save(self, file):
        f = file
        if isinstance(file, list):
            f = file[0]
        try:
            App.get_running_app().export(file=f)
            message(_('Export successful'), f'{os.path.basename(file)}', 'i')
            self.dismiss()
            return True
        except Exception as e:
            message(_('Export failed: %s') % (e.args),
                    f'{os.path.basename(file)}', 'e')
        return False


class LoginPopup(Popup):
    # Widget hooks
    pr_login_wid = ObjectProperty(None)
    pr_seed_wid = ObjectProperty(None)

    def __init__(self, title='', *args, **kwargs):
        super(LoginPopup, self).__init__(**kwargs)
        # Current file
        self.file = None
        self.title = title

    def cmd_enter(self, app):
        '''Button callback:
        Check login was successful (file opened)
        Check the key was set
        Recover tags from the list
        Then enter the list screen'''
        if self.pr_login_wid.pr_password.text and self.pr_seed_wid.pr_seed.text:
            # Check login was successful (file opened) and check the key was set
            if isinstance(self.file, list):
                self.file = self.file[0]
            if not os.path.exists(self.file):
                message(
                    f'{self.title}', _('The file %s does not exists') % (os.path.basename(self.file)), 'e')
                return False
            p = bytes(self.pr_login_wid.pr_password.text, encoding='utf-8')
            s = bytes(self.pr_seed_wid.pr_seed.text, encoding='utf-8')
            if app.open(file=self.file, passwd=p, seed=s):
                app.root.transition.direction = 'left'
                app.root.current = LIST
                self.reset()
                self.dismiss()
            else:
                app.unsecure()
        else:
            message(_('Login warning'), _('Fill password and seed'), 'w')
            return False
        return True

    def cmd_exit(self, app):
        '''Button callback:
        Check login was successful (file opened)
        Check the key was set
        Then enter the list screen'''
        self.reset()
        self.dismiss()
        return True

    def reset(self):
        self.pr_login_wid.pr_password.text = ''
        # self.pr_login.confirm.text = ''
        self.pr_seed_wid.pr_seed.text = ''


class CipherPopup(Popup):
    # Widget hooks
    pr_login_wid = ObjectProperty(None)
    pr_seed_wid = ObjectProperty(None)
    pr_kderive = ObjectProperty(None)
    pr_cipher = ObjectProperty(None)
    pr_iters = ObjectProperty(None)

    def __init__(self, *args, **kwargs):
        super(CipherPopup, self).__init__(**kwargs)
        # Current file
        self.file = None
        self.mode = SAVE  # or COPY

    def cmd_enter(self, app):
        '''Enter the list screen.'''
        if self.pr_login_wid.pr_password.text and self.pr_seed_wid.pr_seed.text:
            # Check login was successful (file opened) and check the key was set
            if isinstance(self.file, list):
                self.file = self.file[0]
            # Build security:
            if self.pr_kderive.text and self.pr_cipher.text and self.pr_iters.text:
                cd = cryptofachade.cryptodict(**cryptofachade.default_cryptod)
                cd['algorithm'] = self.pr_cipher.text
                cd['pbkdf'] = self.pr_kderive.text
                cd['iterations'] = int(self.pr_iters.text)
                p = bytes(self.pr_login_wid.pr_password.text, encoding='utf-8')
                s = bytes(self.pr_seed_wid.pr_seed.text, encoding='utf-8')
            else:
                message(_('Security setup'), _(
                    'Please selectan algorithm'), 'w')
                return False
            if self.mode is SAVE and app.secure(cryptod=cd, passwd=p, seed=s) and app.save(file=self.file, force=True):
                self.dismiss()
                app.root.transition.direction = 'left'
                app.root.current = LIST
            elif self.mode is COPY and app.copy(file=self.file, cryptod=cd, passwd=p, seed=s):
                self.dismiss()
                app.root.transition.direction = 'left'
                app.root.current = LIST
            self.reset()
        else:
            message(_('Login warning'), _('Fill password and seed'), 'w')
            return False
        return True

    def cmd_exit(self, app):
        '''Button callback:
        Check login was successful (file opened)
        Check the key was set
        Then enter the list screen'''
        self.reset()
        self.dismiss()
        return True

    def cipher_algorithms(self):
        '''List of available ciphers algorithm'''
        return list(cryptofachade.cipher_algorithms().keys())

    def key_derivators(self):
        '''List of available key derivation functions'''
        return list(cryptofachade.key_derivators().keys())

    def reset(self):
        self.pr_login_wid.pr_password.text = ''
        self.pr_login_wid.pr_confirm.text = ''
        self.pr_seed_wid.pr_seed.text = ''


class InfoPopup(Popup):
    # Properties: Login and seed
    pr_keyderive = ObjectProperty(None)
    pr_algorithm = ObjectProperty(None)
    pr_mode = ObjectProperty(None)
    pr_keysize = ObjectProperty(None)
    pr_iterations = ObjectProperty(None)
    pr_file = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(InfoPopup, self).__init__(**kwargs)
        pass

    def set_fields(self, cryptod, **kwargs):
        try:
            self.pr_file.text = kwargs['file']
            self.pr_algorithm.text = cryptod['algorithm']
            self.pr_mode.text = cryptod['mode']
            self.pr_keysize.text = str(cryptod['keysize'])
            self.pr_pbkdf.text = cryptod['pbkdf']
            self.pr_iterations.text = str(cryptod['iterations'])
        except KeyError:
            self.pr_algorithm.text = ''
            self.pr_mode.text = ''
            self.pr_keysize.text = ''
            self.pr_keyderive.text = ''
            self.pr_iterations.text = ''


class EditTagPopup(Popup):
    # Widget hooks
    pr_tag = ObjectProperty(None)

    def __init__(self, *args, **kwargs):
        super(EditTagPopup, self).__init__(**kwargs)
        self.mode = None
        self.old = None

    def cmd_cancel(self, args):
        '''Cancel without change anything. '''
        self.mode = self.old = None
        self.dismiss()
        return True

    def cmd_save(self, app):
        '''Delete the current tag and deletes the items tag accordingly'''
        tag = self.pr_tag.text
        if tag == _(TAGS):
            message(tag, _('Action failed because: %s is already used.') %
                    (tag), 'w')
            return False

        if self.mode == DELETE and self.old:
            tag = ''
        elif self.mode == ADD and self.old == '':
            # tag = tag
            if model.in_items(items=app.items, value=tag, key='tag', casefold=True):
                message(
                    tag, _('Action failed because: %s is already used.') % (tag), 'w')
                return False
            else:
                app.root.get_screen(EDIT).pr_tag.text = tag
        elif self.mode == RENAME and self.old:
            tag = tag
        else:
            return False

        for item in model.item_iterator(items=app.items, key='tag', value=self.old):
            item_old = item.copy()
            item['tag'] = tag
            app.add_memento(new=item, old=item_old, action=UPDATE)
        self.mode = self.old = None
        self.dismiss()
        return True


class EnterScreen(Screen):
    pr_recentfiles = ObjectProperty(None)

    def __init__(self, *args, **kwargs):
        super(EnterScreen, self).__init__(**kwargs)
        self.app = None

    def on_enter(self):
        '''Load recent files'''
        self.app = App.get_running_app()
        self.pr_recentfiles.values = self.app.get_recent_files()

    def cmd_recent(self):
        '''Choose a recent file and go to login'''
        if self.pr_recentfiles.text == 'Recent files':
            return False
        file = self.pr_recentfiles.text
        if file and file in self.app.files:
            self.pr_recentfiles.text = 'Recent files'
            file = self.app.files[file]
            popup = LoginPopup()
            popup.title = _('Login to: %s') % (file)
            popup.file = file
            popup.open()
        else:
            message(_('Recent files'), _('%s not found') % (file), 'e')
            return False
        return True

    def cmd_new(self):
        '''Create a new file e go to login'''
        file = ''
        popup = SaveFile()
        popup.title = _('New file: %s') % (file)
        popup.open()
        return True

    def cmd_open(self):
        '''Open a file from filesystem'''
        popup = OpenFile()
        popup.title = _('Open')
        popup.open()
        return True

    def cmd_clear(self):
        self.app.clear_recent_files()
        self.pr_recentfiles.values = self.app.get_recent_files()
        return True

    def cmd_exit(self):
        '''Exit app'''
        self.app.stop()
        # sys.exit()
        return True


class ListScreen(Screen):

    # Widget hooks
    pr_tag = ObjectProperty(None)
    pr_search = ObjectProperty(None)
    pr_expiring = ObjectProperty(None)
    pr_item_list_wid = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(ListScreen, self).__init__(**kwargs)
        self.app = App.get_running_app()
        self.infopopup = None
        self.state_method = self.on_enter_default

    def on_enter(self):
        '''Call when enter screen'''
        self.state_method()

    def on_enter_default(self):
        if self.pr_tag.disabled:
            self.pr_tag.disabled = False
            self.pr_search.disabled = False
        tags = self.build_tags()
        self.pr_tag.values = tags
        self.app.root.get_screen(EDIT).pr_tag.values = tags

        if not self.pr_tag.text:
            self.pr_tag.text = self.pr_tag.values[0]
        elif self.pr_tag.text != self.pr_tag.values[0]:
            self.cmd_tag_selected()
        elif self.pr_search.text:
            self.cmd_search()
        else:
            self._fill_items()
            pass
        self.counter()

    def on_leave(self):
        '''Call when leave screen'''
        pass

    def build_tags(self):
        t = list(set(i['tag'] for i in self.app.items))
        t.sort(key=str.lower)
        tags = [TAGS, ] + t
        return tags

    def _fill_items(self):
        # if self.pr_item_list_wid.count < len(self.app.items):
        self.pr_item_list_wid.clear()
        for i in self.app.items:
            self.pr_item_list_wid.add(ItemComposite, **i)
        self.counter()

    def cmd_option(self, action, app):
        '''This is a menu'''
        if action == INFO:
            if not self.infopopup:
                self.infopopup = InfoPopup()
                self.infopopup.title = _('Info')
            self.infopopup.set_fields(app.cryptod, file=app.file)
            self.infopopup.open()
        elif action == COPY:
            popup = SaveFile()
            popup.filechooser.rootpath = app.file
            popup.title = _('Copy to')
            popup.mode = COPY
            popup.open()
        elif action == IMPORT:
            popup = ImportFile()
            popup.title = _('Import from:')
            popup.open()
        elif action == EXPORT:
            popup = ExportFile()
            popup.title = _('Export to:')
            popup.open()
        elif action == CHANGES:
            app.root.transition.direction = 'left'
            app.root.current = CHANGES
        else:
            pass
        return True

    def cmd_tag_selected(self):
        '''On tag selected'''
        self.pr_search.text = ''
        if self.pr_tag.text == TAGS:
            self._fill_items()
        else:
            sublst = model.filter_items(
                items=self.app.items, value=self.pr_tag.text, key='tag')
            sublst.sort(key=lambda x: str.lower(x['name']))
            self.pr_item_list_wid.clear()
            for i in sublst:
                self.pr_item_list_wid.add(ItemComposite, **i)
        self.counter()
        return True

    def clear_search(self):
        '''Clear the search text field'''
        if len(self.pr_search.text) > 0:
            self.pr_search.text = ''
        self._fill_items()

    def cmd_search(self, after=False, at_least=3):
        '''Search items for the input text'''
        if len(self.pr_search.text) < at_least:
            self._fill_items()
            return False
        items = self.app.items
        self.pr_item_list_wid.clear()
        if after:
            sublst = model.search_items(items=items, text=self.pr_search.text)
            sublst.sort(key=lambda x: str.lower(x['name']))
            for i in sublst:
                self.pr_item_list_wid.add(ItemComposite, **i)
            self.counter()
        else:
            Clock.schedule_once(lambda dt: self.cmd_search(after=True), 0.5)
        return True

    def cmd_add(self, args):
        '''Add a new account'''
        # Apply configuration
        config = self.app.config
        item = new_item()
        item['length'] = str(config.getdefault(
            SkipKeyApp.SETTINGS, SkipKeyApp.PWDLEN, 10))
        item['auto'] = str(config.getdefault(
            SkipKeyApp.PWDAUTO, SkipKeyApp.PWDLEN, True))

        self.manager.get_screen(EDIT).set_item(item)
        self.manager.transition.direction = 'left'
        self.manager.current = EDIT
        return True

    def cmd_back(self, app, after=False):
        '''Return to login:
        Stop the running mode Return to login screen'''
        if after:
            self.pr_item_list_wid.clear()
            self.pr_tag.text = ''
            app.initialize()
            self.manager.transition.direction = 'right'
            self.manager.current = ENTER
            return True
        else:
            if app.file:
                decision(_('Leave'), _('Exit %s without saving?') % (os.path.basename(app.file)),
                         fn_ok=self.cmd_back, ok_kwargs={'app': app, 'after': True})
            else:
                self.cmd_back(app=app, after=True)
        return False

    def counter(self):
        self.ids['_lab_counter'].text = f'{self.pr_item_list_wid.count} / {len(self.app.items)}'

    def cmd_expiring(self, widget, state, after=False):
        if state == 'down':
            self.state_method = self.on_enter_expiring
        else:
            self.state_method = self.on_enter_default
        self.on_enter()

    def on_enter_expiring(self, after=False):
        if after:
            if not self.pr_tag.disabled:
                self.pr_tag.disabled = True
                self.pr_search.disabled = True
            pwd_warn = float(self.app.config.getdefault(
                SkipKeyApp.SETTINGS, SkipKeyApp.PWDWARN, 7))
            pwd_lifetime = float(self.app.config.getdefault(
                SkipKeyApp.SETTINGS, SkipKeyApp.PWDLIFETIME, 6))
            today = datetime.now()
            self.pr_item_list_wid.clear()
            for i in self.app.items:
                try:
                    if i['changed']:
                        changed = datetime.fromisoformat(i['changed'])
                    elif i['created']:
                        changed = datetime.fromisoformat(i['created'])
                    else:
                        continue
                    expire_date = changed + timedelta(days=30*pwd_lifetime)
                    left = expire_date - today
                    if left.days <= pwd_warn:
                        self.pr_item_list_wid.add(
                            item_cls=ProgressItem, max=pwd_warn, name=i['name'], date=expire_date)
                except Exception:
                    continue
            self.counter()
        else:
            Clock.schedule_once(lambda dt: self.on_enter_expiring(after=True))
        return True


class EditScreen(Screen):
    # Widget hooks
    pr_name = ObjectProperty(None)
    pr_tag = ObjectProperty(None)
    pr_url = ObjectProperty(None)
    pr_login = ObjectProperty(None)
    pr_email = ObjectProperty(None)
    pr_description = ObjectProperty(None)
    pr_color = ObjectProperty(None)
    pr_created = ObjectProperty(None)
    pr_changed = ObjectProperty(None)
    pr_cipherpwd = ObjectProperty(None)
    # Classes hooks
    pr_auto_wid = ObjectProperty(None)
    pr_user_wid = ObjectProperty(None)
    pr_tabbedb_wid = ObjectProperty(None)  # Feed auto = True/False

    def __init__(self, **kwargs):
        super(EditScreen, self).__init__(**kwargs)
        # Item currently edit
        self.item = None

    def set_item(self, item):
        '''Initialise field from a dictionary'''
        self.item = item
        self.pr_name.text = item['name']
        self.pr_login.text = item['login']
        self.pr_url.text = item['url']
        self.pr_email.text = item['email']
        self.pr_description.text = item['description']
        self.pr_tag.text = item['tag']

        self.pr_auto_wid.set_item(item)
        self.pr_user_wid.set_item(item)

        self.pr_created.text = item['created']
        self.pr_changed.text = item['changed']
        self.pr_cipherpwd.text = item['password']
        if item['auto'] == 'True':
            tab = self.pr_tabbedb_wid.tab_list[1]
        else:
            tab = self.pr_tabbedb_wid.tab_list[0]
        self.pr_tabbedb_wid.switch_to(tab, do_scroll=False)
        pass

    def cmd_back(self, app):
        '''Return to list, discard all changes.'''
        self.manager.transition.direction = 'right'
        self.manager.current = LIST
        return True

    def cmd_delete(self, app):
        '''Delete this account, return to list.'''
        if app.delete_item(self.item):
            self.manager.transition.direction = 'right'
            self.manager.current = LIST
        return True

    def cmd_save(self, app):
        '''Save this account, return to list.'''
        tag = self.pr_tag.text
        if tag == TAGS:
            tag = ''
        auto = self.item['auto'] == 'True'
        if self.pr_tabbedb_wid.current_tab is self.pr_tabbedb_wid.tab_list[1] \
                and self.pr_auto_wid.changed():
            auto = True
            self.pr_user_wid.pr_password.text = ''
            self.pr_user_wid.pr_confirm.text = ''
        if self.pr_tabbedb_wid.current_tab is self.pr_tabbedb_wid.tab_list[0] \
                and self.pr_user_wid.changed():
            auto = False
            self.pr_auto_wid.pr_length.text = ''
            self.pr_auto_wid.pr_symbols.text = ''
            self.pr_auto_wid.pr_numbers.text = ''
            self.pr_auto_wid.pr_letters.active = False
            self.pr_cipherpwd.text = app.encrypt(
                self.pr_user_wid.pr_password.text)
        else:
            # No pasword changed
            pass

        item = new_item(
            name=self.pr_name.text,
            login=self.pr_login.text,
            url=self.pr_url.text,
            email=self.pr_email.text,
            description=self.pr_description.text,
            tag=tag,
            length=self.pr_auto_wid.pr_length.text,
            symbols=self.pr_auto_wid.pr_symbols.text,
            numbers=self.pr_auto_wid.pr_numbers.text,
            letters=self.pr_auto_wid.pr_letters.active,
            password=self.pr_cipherpwd.text,
            color=self.pr_color.text,
            auto=auto,
            created=self.pr_created.text,
            changed=self.pr_changed.text,
            history=self.item['history']
        )

        if not self.item_check(item):

            return False

        if self.item == item:
            message(_('Info'), _('No changes.'), 'i')
            return True
        if app.save_item(item):
            self.manager.transition.direction = 'right'
            self.manager.current = LIST
        return True

    def _call_tag_popup(self, instance, spinner, mode):
        popup = EditTagPopup()
        if mode == DELETE:
            popup.title = ': '.join((instance.text, spinner.text))
            popup.pr_tag.text = spinner.text
            popup.old = spinner.text
            popup.mode = DELETE
        elif mode == ADD:
            popup.title = ': '.join((instance.text, ))
            popup.mode = ADD
            popup.old = ''
        elif mode == RENAME:
            popup.title = ': '.join((instance.text, spinner.text))
            popup.mode = RENAME
            popup.old = spinner.text
        popup.open()

    def item_check(self, item):
        log = []
        if item['name'] == '':
            log.append(_('Name is mandatory'))
        if item['password'] == '':
            log.append(_('No password defined'))
        if item['email']:
            m = re.search(
                r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", item['email'])
            if not m:
                log.append(_('Check email adress: %s') % (item['email']))
        if len(log) > 0:
            message(_('Warning'), '\n'.join(
                [f'{j+1} - {x}' for j, x in enumerate(log)]), 'w')
            return False
        return True

    def cmd_selectiontag(self, spinner):
        '''Nothing to do here'''
        # print(f'select {spinner.text}')
        return True

    def cmd_renametag(self, instance, spinner):
        '''Rename the current tag and updates all items accordingly
        to the renamed tag. '''
        return self._call_tag_popup(instance, spinner, RENAME)

    def cmd_deletetag(self, instance, spinner):
        '''Delete the current tag and deletes the items tag accordingly'''
        return self._call_tag_popup(instance, spinner, DELETE)

    def cmd_addtag(self, instance, spinner):
        '''Delete the current tag and deletes the items tag accordingly'''
        return self._call_tag_popup(instance, spinner, ADD)


class ImportScreen(Screen):
    pr_mapping = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(ImportScreen, self).__init__(**kwargs)
        self.file = None

    def on_enter(self, **kwargs):
        '''Load a template'''
        text = ',\n'.join(
            [f"('{i}', '{j}')" for i, j in model.mapping.items()])
        self.pr_mapping.text = text
        super(ImportScreen, self).on_enter(**kwargs)

    def cmd_back(self, app):
        app.root.transition.direction = 'right'
        app.root.current = LIST

    def cmd_import(self, app, mapping):
        try:
            match = re.findall(
                r"(\(\'[^,^\']+?\',.\'[^,^\']+?\'\),?)", mapping)
            mapping = dict(eval(''.join(match)))
            items = model.import_csv(
                file=self.file, delimiter='\t', mapping=mapping)
            # Add default keys
            items_ = []
            for item in items:
                item = model.new_item(**item)
                item['password'] = app.encrypt(item['password'])
                item['auto'] = 'False'
                model.normalize(item)
                items_.append(item)
        except Exception as e:
            message(_('Error'), _(
                'Check the syntax:\n%s') % (e.args[0]), 'w')
            return False
        if len(items_) > 0:
            for item in items_:
                app.items.append(item)
                app.add_memento(new=None, old=item, action=IMPORT)
            app.root.transition.direction = 'right'
            app.root.current = LIST
        return True

    def mapping_help(self):
        return _('Write couples separated by comma:\n(\'<source>\', \'<target>\').')


class ChangesScreen(Screen):
    # Widget hooks
    #pr_accounts = ObjectProperty(None)
    pr_actions = ObjectProperty(None)
    pr_comparator_wid = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(ChangesScreen, self).__init__(**kwargs)
        self.app = App.get_running_app()

    def _fill_fields(self, mementos):
        self.pr_comparator_wid.clear()
        try:
            formers = mementos[self.pr_actions.values.index(
                self.pr_actions.text)]['body']
            values = self.app.items[model.index_of(
                items=self.app.items, key='name', value=formers['name'])]

            for key, former in formers.items():
                self.pr_comparator_wid.add(item_cls=Comparison,
                                           key=key, name=SkipKeyApp.LABELS[key],
                                           last=values[key],
                                           former=former)
                # self.pr_comparator_wid.add(
                #     field=Comparison, key=key, name=SkipKeyApp.LABELS[key], last=values[key], former=former)
        except ValueError:
            pass
        except IndexError:
            pass

    def on_enter(self):
        if len(self.app.history) > 0:
            self.pr_actions.values = ['{: <10s} - {: <10s} - {:s}'.format(
                m['name'], m['action'], m['timestamp'].isoformat(sep=' ', timespec='seconds')) for m in self.app.history]
            self.pr_actions.text = self.pr_actions.values[0]
            self._fill_fields(self.app.history)
        else:
            self.pr_actions.values = [_('No changes'), ]
            self.pr_actions.text = self.pr_actions.values[0]

    def cmd_back(self, app):
        '''Return to list, discard all changes.'''
        self.manager.transition.direction = 'right'
        self.manager.current = LIST
        return True

    def cmd_undo(self, *args):
        '''set the last changed, delete from history'''
        try:
            pos = self.pr_actions.values.index(self.pr_actions.text)
            item = self.app.history[pos]['body']
            #del self.app.history[pos]
            self.app.history.pop(pos)
            self.app.save_item(item, history=False)  # no history
            self.on_enter()
        except ValueError:
            # Nothing to restore
            pass
        except IndexError:
            pass

    def cmd_actions(self, text):
        self._fill_fields(self.app.history)


class TagSpinner(Spinner):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # global tags
        # self.text = TAGS


class LoginPanel(BoxLayout):
    # Widget hooks
    pr_password = ObjectProperty(None)
    pr_strenght = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(LoginPanel, self).__init__(**kwargs)

    def cmd_text(self, text):
        '''Check input for non allowed characters, and update password strenght
        '''
        self.pr_strenght.set_strength(text)

    def changed(self):
        '''Return if the pasword has been changed'''
        if self.pr_password.text:
            return self.pr_password.text != ''
        return False


class UserPanel(BoxLayout):
    # Widget hooks
    pr_password = ObjectProperty(None)
    pr_confirm = ObjectProperty(None)
    pr_strenght = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(UserPanel, self).__init__(**kwargs)
        self.size_hint_max_y = None
        self.bind(minimum_height=self.setter('height'))

    def cmd_text(self, text):
        '''Check input for non allowed characters, and update password strenght
        '''
        self.pr_strenght.set_strength(text)

    def set_item(self, item):
        self.pr_password.text = ''
        self.pr_confirm.text = ''

    def changed(self):
        '''Return if the pasword has been changed'''
        if self.pr_password.text and self.pr_confirm.text:
            return self.pr_password.text != '' and self.pr_password.text == self.pr_confirm.text
        return False


class SeedPanel(BoxLayout):
    # Widget hooks
    pr_seed = ObjectProperty(None)
    pr_strenght = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(SeedPanel, self).__init__(**kwargs)

    def cmd_text(self, text):
        '''Check input for non allowed characters, and update password strenght
        '''
        self.set_strength(text)

    def set_strength(self, value):
        self.pr_strenght.set_strength(value)

    def changed(self):
        '''Return if the seed has been changed'''
        if self.pr_seed.text:
            return self.pr_seed.text != ''
        return False


class AutoPanel(BoxLayout):
    # Widget hooks
    pr_length = ObjectProperty(None)
    pr_letters = ObjectProperty(None)
    pr_symbols = ObjectProperty(None)
    pr_numbers = ObjectProperty(None)
    pr_strenght = ObjectProperty(None)
    pr_password = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(AutoPanel, self).__init__(**kwargs)
        self.size_hint_max_y = None
        self.bind(minimum_height=self.setter('height'))

    def set_strength(self, text):
        self.pr_strenght.set_strength(text)

    def set_item(self, item):
        self.pr_length.text = item['length']
        self.pr_symbols.text = item['symbols']
        self.pr_numbers.text = item['numbers']
        self.pr_letters.active = item['letters'] == 'True'
        self.pr_strenght.set_strength('')
        self.pr_password.text = ''

    def changed(self):
        '''Return if the pasword has been changed'''
        if self.pr_password.text:
            return self.pr_password.text != ''
        return False


class PasswordStrenght(BoxLayout):
    # Widget hooks
    pr_strenght = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(PasswordStrenght, self).__init__(**kwargs)

    def set_strength(self, text):
        '''Set the password strenght value.
        '''
        self.pr_strenght.value = passwordmeter.strength(text)


class AccessList(ItemList):
    def __init__(self, *args, **kwargs):
        cell_widths = {'name': dp(200), 'login': dp(200)}
        super(AccessList, self).__init__(mask=item_mask, **kwargs)
        self.add_bubble(Factory.ItemActionBubble())


class FieldDiff(ItemList):
    def __init__(self, *args, **kwargs):
        super(FieldDiff, self).__init__(*args, **kwargs)


class ItemActionBubble(Bubble):

    def __init__(self, **kwargs):
        super(ItemActionBubble, self).__init__(**kwargs)
        # Current selected item
        self.item = None
        # Clear clipboard scheduled event
        self.evt_clipboard = None

    def cmd_url(self, app):
        # TODO System call to browser
        item = app.items[model.index_of(items=app.items, value=self.item.kwargs['name'], key='name')]
        url = item['url']
        self._publish(app, url)
        return True

    def cmd_user(self, app):
        '''Publish user.'''
        item = app.items[model.index_of(items=app.items, value=self.item.kwargs['name'], key='name')]
        user = item['login']
        self._publish(app, user)
        return True

    def cmd_password(self, app):
        '''Publish password.'''
        p = self._password(app)
        self._publish(app, p)
        return True

    def cmd_login(self, app):
        '''Publish 'user TAB password'.'''
        item = app.items[model.index_of(items=app.items, value=self.item.kwargs['name'], key='name')]
        p = self._password(app)
        login = f'{item["login"]}\t{p}'
        self._publish(app, login)
        self.reset()
        return True

    def _password(self, app):
        item = app.items[model.index_of(items=app.items, value=self.item.kwargs['name'], key='name')]
        if item['auto'] == 'False':
            p = app.decrypt(item['password'])
        # Clipboard.copy(self.item.item['login'])
        else:
            p = app.show(item)
        return p

    def _publish(self, app, text):
        autocompletion = app.config.getdefault(
            SkipKeyApp.SETTINGS, SkipKeyApp.AUTOCOMP, True) == '1'
        timeout = int(app.config.getdefault(
            SkipKeyApp.SETTINGS, SkipKeyApp.PWDTIME, '15'))
        if text == False:
            return False
        if autocompletion:
            daemon = LoginDaemon(text=text, timeout=timeout)
            daemon.start()
        else:
            Clipboard.copy(text)
            # Once at a time
            if app.evt_clipboard:
                app.evt_clipboard.cancel()
            app.evt_clipboard = Clock.schedule_once(self.cb_clean, timeout)
        return True

    def cmd_edit(self, app):
        item = app.items[model.index_of(
            items=app.items, value=self.item.kwargs['name'], key='name')]
        app.root.get_screen(EDIT).set_item(item)
        # app.root.get_screen(EDIT).set_item(self.item.kwargs)
        app.root.transition.direction = 'left'
        app.root.current = EDIT
        self.reset()
        return True

    def reset(self):
        # Free the selection to enable re-selection
        self.item = None
        self.parent.remove_widget(self)

    def cb_clean(self, dt):
        Clipboard.copy(' ')

    def on_touch_down(self, touch):
        '''Remove bubble when click outside it'''
        if not self.collide_point(touch.x, touch.y):
            self.reset()
        return super(ItemActionBubble, self).on_touch_down(touch)


class SkipKeyApp(App):
    # Defaults constants
    SETTINGS = 'Settings'
    RECENT_FILES = 'Recent Files'
    TIMEOUT = 'deftimeout'
    AUTOCOMP = 'defautocompletion'
    PWDTIME = 'defsecrettimeout'
    PWDLEN = 'defplen'
    PWDAUTO = 'defauto'
    PWDLIFETIME = 'deflifetime'
    PWDWARN = 'defwarn'
    LOG = 'deflog'
    # Translations
    LABELS = {
        'name': _('Name'),  # new name
        'url': _('Web site'),  # Check valid url
        'login': _('Login user'),  # Any string
        'email': _('e-mail'),  # @-mail
        'description': _('Free text'),  # Any string
        'tag': _('Tag'),  # Any string
        'color': _('Color'),  # Basic colors as string
        'created': _('Created'),  # Date
        'changed': _('Changed'),  # Date
        'auto': _('Auto'),  # True, False=user
        'length': _('Length'),  # Integer
        'letters': _('Letters'),  # True / False
        'numbers': _('Numbers'),  # At least [0 length]
        'symbols': _('Symbols'),  # At least [0 length]
        # User encrypted password or salt Base64 encoded
        'password': _('Cipher Data'),
        'history': ''  # Record history - not yet managed
    }

    pr_timer = StringProperty('')
    use_kivy_settings = True

    def __init__(self, **kwargs):
        super(SkipKeyApp, self).__init__(**kwargs)
        self.MAXF = 10
        # Data model
        self.items = []
        # Mementos Data model
        self.history = []
        # Current file
        self.file = None
        # Recent files
        self.files = dict()
        # Secret key wrapper
        self.keywrapper = None
        # Session key
        self.session_key = None
        # Sectret seed wrapper
        self.seedwrapper = None
        # Session seed
        self.session_seed = None
        # Cipher / Decipher
        self.cipher_fachade = None
        # Crypto parameters
        self.cryptod = None
        # App timeout Clock-event
        self.evt_timeout = None
        # Clipboard timeout Clock-event
        self.evt_clipboard = None
        #
        self.count_down = 0

    def build(self):
        self.title = 'SkipKey %s' % (__version__)
        # path = os.path.dirname(os.path.realpath(__file__))
        self.icon = '%s\\%s' % (icons_dir, ICON)
        # ----------------> App configuration
        self.user_data_dir
        # Create the screen manager
        # Builder.load_file('commons.kv')
        # Builder.load_file('screens_test.kv')
        sm = ScreenManager()
        self.root = sm

        sm.add_widget(EnterScreen(name=ENTER))
        sm.add_widget(ListScreen(name=LIST))
        sm.add_widget(EditScreen(name=EDIT))
        sm.add_widget(ImportScreen(name=IMPORT))
        sm.add_widget(ChangesScreen(name=CHANGES))

        return sm

    def build_settings(self, settings):
        """Build settings from a JSON file / data first.
        """
        # JSON template is needed ONLY to create the panel
        path = os.path.dirname(os.path.realpath(__file__))
        with open(f'{path}\settings.json') as f:
            s = json.dumps(eval(f.read()))
        settings.add_json_panel(SkipKeyApp.SETTINGS, self.config, data=s)

    def build_config(self, config):
        """The App class handles ‘ini’ files automatically add sections and
        default parameters values. """
        config.adddefaultsection(SkipKeyApp.SETTINGS)
        config.setdefault(SkipKeyApp.SETTINGS, SkipKeyApp.TIMEOUT, 5)  # min
        config.setdefault(SkipKeyApp.SETTINGS, SkipKeyApp.AUTOCOMP, True)
        # Parte user+tab+password
        config.setdefault(SkipKeyApp.SETTINGS, SkipKeyApp.PWDTIME, 15)  # sec.
        config.setdefault(SkipKeyApp.SETTINGS, SkipKeyApp.PWDLEN, 10)
        config.setdefault(SkipKeyApp.SETTINGS, SkipKeyApp.PWDAUTO, True)
        config.setdefault(SkipKeyApp.SETTINGS, SkipKeyApp.PWDLIFETIME, 6)
        config.setdefault(SkipKeyApp.SETTINGS, SkipKeyApp.PWDWARN, 7)
        config.setdefault(SkipKeyApp.SETTINGS, SkipKeyApp.LOG, 0)
        config.adddefaultsection(SkipKeyApp.RECENT_FILES)

    # def cmd_config_change(self, config, section, key, value):
    #     """Event handler fired when a configuration token has been changed by
    #     the settings page."""
    #     if config is self.config:
    #         token = (section, key)
    #         if token == ('section1', 'key1'):
    #             print('Our key1 has been changed to', value)
    #         elif token == ('section1', 'key2'):
    #             print('Our key2 has been changed to', value)
    #         else:
    #             print(f'Settings {section}-{key}: {value}')

    # def display_settings(self, settings):
        """Overrride to change how settings are displayed.
        To check preferences manually call App.open_settings() and App.close_settings()"""
        # super().display_settings(settings)
        # if not self.sm.has_screen(SkipKeyApp.SETTINGS):
        #     s = SettingsScreen(name=SkipKeyApp.SETTINGS)
        #     s.add_widget(settings)
        #     self.sm.add_widget(s)
        # self.sm.current = SkipKeyApp.SETTINGS

    def on_start(self):
        """Event handler for the on_start event which is fired after initialization
        (after build() has been called) but before the application has started running."""
        # print('app: on_start()')
        # Init screens:
        # self.root.get_screen(ENTER).files.values = []
        return super().on_start()

    def on_pause(self):
        """Event handler called when Pause mode is requested. You should return
        True if your app can go into Pause mode, otherwise return False and your
        application will be stopped."""
        # print('app: on_pause()')
        return super().on_pause()

    def on_resume(self):
        """Event handler called when your application is resuming from the Pause mode."""
        # print('app: on_resume()')
        return super().on_resume()

    def on_stop(self):
        """Event handler for the on_stop event which is fired when the application
        has finished running (i.e. the window is about to be closed)."""
        self.save(file=self.file)
        return super().on_stop()

    def open(self, file, passwd, seed):
        '''Open the file and prepare the records'''
        try:
            with open(file, mode='r') as f:
                cryptod = json.load(f)
            if self.secure(cryptod=cryptod, passwd=passwd, seed=seed):
                self.file = file
                self.items = self.cipher_fachade.decrypt(
                    cryptod,
                    self.keywrapper.secret(self.session_key)
                )
                # self.build_tags()
                self.items.sort(key=lambda x: str.lower(x['name']))
                self.update_recent_files(file)
                return True
        except IOError as e:
            message(
                _('Open'), _('Invalid file: "%s":\n%s') % (os.path.basename(file), e), 'e')
            self.file = None
            return False
        except ValueError as e:
            message(_('Open'), f'"{os.path.basename(file)}":\n{e}', 'e')
            return False

        return False

    def update_recent_files(self, file):
        '''Update the list of recently opened files'''
        # print(f'App.update_recent_files(file: {file})')
        # Total number of saved files: numf
        file = f'{file}'
        flist = dict()
        for i in range(self.MAXF):
            flist[self.config.getdefault(
                SkipKeyApp.RECENT_FILES, f'_{i}', '')] = ''
        if file in flist:
            del flist[file]
        if '' in flist:
            del flist['']
        # Last comes first
        self.config.set(SkipKeyApp.RECENT_FILES, f'_{0}', file)
        # Cut to max records allowed
        for i, key in enumerate(list(flist.keys())):
            if i < self.MAXF:
                self.config.set(SkipKeyApp.RECENT_FILES, f'_{i+1}', key)
        self.config.write()
        return True

    def clear_recent_files(self):
        '''Clear the list of recently opened files'''
        # print(f'App.clear_recent_files()')
        for i in range(self.MAXF):
            self.config.set(SkipKeyApp.RECENT_FILES, f'_{i}', '')
        self.config.write()
        return True

    def get_recent_files(self):
        '''Update the list of recently opened files, these can have the same name,
        but different path: only available files are appended to the list.'''
        # numf = self.config.getdefaultint(SkipKeyApp.RECENT_FILES, 'numf', 0)
        self.files = dict()
        j = 0
        for i in range(0, self.MAXF):
            f = self.config.getdefault(SkipKeyApp.RECENT_FILES, f'_{i}', '')
            if os.path.exists(f):
                j += 1
                self.files[f'{j} - {os.path.basename(f)}'] = f
        return self.files.keys()

    def delete_item(self, item, after=False):
        # print('This item was deleted!')
        if after:
            item_list = self.root.get_screen(LIST).pr_item_list_wid
            index = model.index_of(self.items, item['name'], 'name')
            if index > -1:  # Delete
                self.add_memento(
                    new=item, old=self.items.pop(index), action=DELETE)
            else:
                return False
            self.items.sort(key=lambda k: str(k['name']).lower())
            item_list.clear()
            for i in self.items:
                item_list.add(i)
        else:
            Clock.schedule_once(lambda dt: self.delete_item(
                item=item, after=True), 0)
        return True

    def save_item(self, item, history=True, after=False):
        if after:
            # print(f'This item was saved! {item}')
            index = model.index_of(self.items, item['name'], 'name')
            if index > -1:  # Update
                if history:
                    self.add_memento(
                        new=item, old=self.items[index], action=UPDATE)
                self.items[index] = item
                self.items[index]['changed'] = datetime.now(
                ).isoformat(sep=' ', timespec='seconds')
            else:  # Append
                item['created'] = item['changed'] = datetime.now(
                ).isoformat(sep=' ', timespec='seconds')
                self.items.append(item)
                if history:
                    self.add_memento(new=None, old=item, action=APPEND)
            self.items.sort(key=lambda k: str(k['name']).lower())
            # item_list.clear()
            # for i in self.items:
            #     item_list.add(i)
        else:
            Clock.schedule_once(lambda dt: self.save_item(
                item=item, history=history, after=True), 0)
        return True

    def add_memento(self, new, old, action=''):
        '''History Data model: for the present the history is a back up of
        the data model.
        {'name': item_name, 'changed': timestamp, 'item': item_json_dump}
        '''
        if new != old:
            self.history[0:0] = [model.memento(item=old, action=action)]

    def encrypt(self, text):
        """
        Encrypt a password.
        Encrypt a password using the security algorithm and seed.
            Parameters
        ----------
            text : text to encrypt

            Returns
        ----------
            cipher text as base64 encoded utf-8 string
        -------
        type :
            Raises
        ------
        Exception
        """
        # Get the seed:
        try:
            key = self.seedwrapper.secret(self.session_seed)
            cryptod = self.cipher_fachade.encrypt(text, self.cryptod, key)
            # encoding='utf-8'
            r = bytes(json.dumps(cryptod), encoding='utf-8')
            r = str(base64.b64encode(r), encoding='utf-8')
        except Exception as e:
            message(_('Decipher'), e.args, 'i')
            return None
        return r

    def decrypt(self, text):
        """
        Decrypt the text.
        Decrypt a text using the security algorithm and seed.
            Parameters
        ----------
            text : text to encrypt

            Returns
        ----------
            plain object
        -------
        type :
            Raises
        ------
        Exception
        """
        # Get the seed:
        try:
            cryptod = json.loads(str(base64.b64decode(text), encoding='utf-8'))
            key = self.seedwrapper.secret(self.session_seed)
            t = self.cipher_fachade.decrypt(cryptod, key)
            return t
        except Exception as e:
            message(_('Decipher'), e.args, 'e')
        return False

    def generate(self, length, letters, numbers, symbols):
        """
        Generate a password.
        Generate a password and update the strenght.
            Parameters
        ----------
        length : password length.

        letters : letters are allowed: True/False.

        numbers : a number, numbers allowed at least.

        symbols : a number, symbols allowed at least.

            Returns
        -------
        type :
            Raises
        ------
        Exception
        """
        edit_screen = self.root.get_screen(EDIT)
        if letters:
            letters = 1
        else:
            letters = 0
        try:
            pattern = cryptofachade.Pattern(
                lett=letters,
                num=numbers,
                sym=symbols,
                length=length
            )
            seed = self.seedwrapper.secret(self.session_seed)
            pwd, salt = self.cipher_fachade.secret(seed, ITERATIONS, pattern)
            edit_screen.pr_auto_wid.pr_password.text = pwd
            edit_screen.pr_auto_wid.set_strength(pwd)
            # Put in the ciphered
            edit_screen.pr_cipherpwd.text = str(
                base64.b64encode(salt), encoding='utf-8')
        except ValueError as e:
            message(_('Password'), e.args, 'e')
            return False
        return True

    def show(self, item):
        """
        Show a generated password.
        Generate a password and update the strenght.
            Parameters
        ----------
        length : password length.

        letters : letters are allowed: True/False.

        numbers : a number, numbers allowed at least.

        symbols : a number, symbols allowed at least.

            Returns
        -------
        type :
            Raises
        ------
        Exception
        """
        try:
            if item['letters'] == 'False':
                letters = 0
            else:
                letters = 1
            pattern = cryptofachade.Pattern(
                lett=letters,
                num=item['numbers'],
                sym=item['symbols'],
                length=item['length']
            )
            seed = self.seedwrapper.secret(self.session_seed)
            salt = base64.b64decode(item['password'])
            p = self.cipher_fachade.password(seed, salt, ITERATIONS, pattern)
            return p
        except ValueError as e:
            message(_('Password'), e, 'e')
        return False

    def secure(self, cryptod, passwd, seed):
        '''Set up the security only one time!'''
        try:
            self.cipher_fachade = cryptofachade.CipherFachade()
            self.keywrapper = cryptofachade.KeyWrapper()
            self.seedwrapper = cryptofachade.KeyWrapper()
            # Wrapping secret key
            key = self.cipher_fachade.key_derivation_function(
                cryptod).derive(passwd)
            self.session_key = self.keywrapper.wrap(key)
            # Wrapping secret seed
            seed = self.cipher_fachade.key_derivation_function(
                cryptod).derive(seed)
            self.session_seed = self.seedwrapper.wrap(seed)
            # security settings
            self.cryptod = cryptod
            self.timeout()
        except Exception as e:
            self.unsecure()
            message(title=_('Security error'),
                    text=_('Initialisation error:\n%s') % (e), type='e')
            return False
        return True

    def unsecure(self):
        '''Set up the security'''
        self.cipher_fachade = None
        self.session_key = None
        self.session_seed = None
        self.keywrapper = None
        self.seedwrapper = None
        self.cryptod = None
        return True

    def timeout(self, after=False):
        '''Security timeout'''
        if after:
            self.count_down -= 1
            self.pr_timer = hh_mm_ss(self.count_down)
            if self.count_down < 1:
                self.save(self.file)
                self.initialize()
                self.root.transition.direction = 'right'
                self.root.current = ENTER
                self.evt_timeout.cancel()
        else:
            if self.evt_timeout:
                self.evt_timeout.cancel()
            mins = int(self.config.getdefault(
                SkipKeyApp.SETTINGS, SkipKeyApp.TIMEOUT, 1)) * 60
            self.count_down = mins
            self.evt_timeout = Clock.schedule_interval(
                lambda dt: self.timeout(after=True), 1)
        return True

    def initialize(self):
        '''Initializes app context'''
        self.unsecure()
        # Data model
        self.items = []
        # Current file
        self.file = None
        # Mementos Data model
        self.history = []
        # Keeps recent files
        self.files
        # Stop count down
        if self.evt_timeout:
            self.evt_timeout.cancel()
        return True

    def save(self, file, force=False):
        """
        Save items into a file.
        The file is encrypted.
            Parameters
        ----------
        file : the file path.

        cryptod : the cryprographic stuff for generating the secret key.

            Returns
        -------
        type :
            Raises
        ------
        Exception
        """
        if file and self.session_key and (len(self.history) > 0 or force):
            try:
                data = self.cipher_fachade.encrypt(
                    self.items,
                    cryptod=self.cryptod,
                    secret=self.keywrapper.secret(self.session_key)
                )
                with open(file, mode='w') as f:
                    json.dump(data, f)
                    self.update_recent_files(file)
            except IOError as e:
                message(_('Error'), _('Save file error:\n%s') % (e), 'e')
                return False
            except TypeError as e:
                message(_('Error'), _('Save file error:\n%s') % (e), 'e')
                return False
            except AttributeError as e:
                message(_('Error'), _('Save file error:\n%s') % (e), 'e')
                return False
            return True
        # Nothing to save
        return False

    def copy(self, file, cryptod, passwd, seed, thread=False):
        """
        Save items into a file.
        The file is encrypted.
            Parameters
        ----------
        file : the file path.

        cryptod : the cryprographic stuff for generating the secret key.

            Returns
        -------
        type :
            Raises
        ------
        Exception
        """
        if not thread:
            kwargs = {'file': file, 'cryptod': cryptod,
                      'passwd': passwd, 'seed': seed, 'thread': True}
            copy_thread = threading.Thread(target=self.copy, kwargs=kwargs)
            copy_thread.start()
            message(_('Copy file'),
                    _('File copyed to: %s') % (os.path.basename(file)), 'i')
            return True

        # Before copying all password must be encrypted
        # with the new key, and all generated ones must be
        # converted in user typed
        # Shoul be done in another thread
        items_copy = self.items[0:]

        try:
            # Get the seed:
            try:
                local_cf = cryptofachade.CipherFachade()
                key = local_cf.key_derivation_function(
                    cryptod).derive(passwd)
                seed = local_cf.key_derivation_function(
                    cryptod).derive(seed)
                for item in items_copy:
                    if item['auto'] == 'True':
                        pwd = self.show(item)
                        item['auto'] = 'False'
                        item['length'] = ''
                        item['letters'] = ''
                        item['numbers'] = ''
                        item['symbols'] = ''
                    elif item['auto'] == 'False':
                        pwd = self.decrypt(item['password'])

                    r = local_cf.encrypt(pwd, cryptod, seed)
                    r = bytes(json.dumps(r), encoding='utf-8')
                    r = str(base64.b64encode(r), encoding='utf-8')
                    item['password'] = r
            except Exception as e:
                message(
                    _('Decipher'), _("Item {item['name']}:\nerror %s") % (e), 'i')
                return None

            data = local_cf.encrypt(
                items_copy, cryptod=cryptod, secret=key)
            local_cf = None
            with open(file, mode='w') as f:
                json.dump(data, f)
            self.update_recent_files(file)
        except IOError as e:
            message(_('Error'), _('Copy file error:\n%s') % (e), 'e')
            return False
        except TypeError as e:
            message(_('Error'), _('Copy file error:\n%s') % (e), 'e')
            return False
        except AttributeError as e:
            message(_('Error'), _('Copy file error:\n%s') % (e), 'e')
            return False
        except ValueError as e:
            message(_('Error'), _('Copy file error:\n%s') % (e), 'e')
            return False
        return True

    def export(self, file):
        items_csv = []
        for i in self.items[:]:
            item = model.new_item(**i)
            if item['auto'] == 'True':
                item['password'] = self.show(item)
            elif item['auto'] == 'False':
                item['password'] = self.decrypt(item['password'])
            else:
                pass
            items_csv.append(item)
        try:
            return model.export_csv(file=file, items=items_csv, delimiter='\t', lineterminator='\r\n')
        except Exception:
            raise
        return True


if __name__ == '__main__':
    SkipKeyApp().run()
