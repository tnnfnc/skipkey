"""SkipKey: a help to password management.
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
from polyitemlist import (ItemList, ItemComposite,
                          Comparison, ProgressItem, SubItem, WarningItem)
from filemanager import OpenFilePopup, SaveFilePopup, message, decision
import cryptofachade
import passwordmeter
import model
from layoutdelegate import GuiController
import appconfig as conf
import os
import sys
import webbrowser as browser
dummy = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dummy)

# =============================================================================
# Kivy config
# =============================================================================
kivy.require('1.11.0')  # Current kivy version

MAJOR = 1
MINOR = 1
MICRO = 0
RELEASE = True
__version__ = '%d.%d.%d' % (MAJOR, MINOR, MICRO)

_ = conf.translate(['it'])


def dp(pix):
    return metrix.dp(pix)


Builder.load_file('kv/commons.kv')


def hh_mm_ss(seconds):
    """
    Converts seconds into hh:mm:ss padded with zeros.

    """
    hh = int(seconds/3600)
    mm = int((seconds % 3600)/60)
    ss = int((seconds % 3600) % 60)
    out = 'Timeout: {hh:02}:{mm:02}:{ss:02}'.format(hh=hh, mm=mm, ss=ss)
    return out


def expire_on(item, keys, lifetime):
    today = datetime.now()
    try:
        changed = None
        for key in keys:
            if item[key]:
                changed = datetime.fromisoformat(item[key])
                break
        if changed:
            expire_date = changed + timedelta(days=lifetime)
            # left = expire_date - today
            return expire_date
    except Exception:
        pass
    return today


def elapsed_days(item, keys):
    """Return elapsed days since password was set."""
    today = datetime.now()
    try:
        changed = None
        for key in keys:
            if item[key]:
                changed = datetime.fromisoformat(item[key])
                break
        if changed:
            days = (today - changed).days
            # left = expire_date - today
            return days
    except Exception:
        pass
    return 0


"""Items:
1) initialized at new file or at opening from the items
2) updated from the Edit screen
3) accessed everywere is is needed
"""
model.new_item
item_mask = {'name': dp(200),
             'login': dp(180),
             'url': dp(200),
             'elapsed': dp(180),
             #  'progress': dp(160),
             'warning': dp(180)
             }


class SecurityException(Exception):

    def __init__(self, *args, **kwargs):
        super(SecurityException, self).__init__(*args, **kwargs)


class OpenFile(OpenFilePopup):
    """
    GUI element. Open file pop up. 
    """

    def __init__(self, *args, **kwargs):
        super(OpenFile, self).__init__(**kwargs)
        self.filechooser.dirselect = False
        self.guic = GuiController(self)

    def cmd_load(self, path, selection):
        """
        Call login screen to decipher file.
        """
        if selection:
            popup = LoginPopup()
            popup.title = _('Login to: %s') % (", ".join(selection))
            popup.open()
            popup.file = selection
            self.dismiss()
        return False

    def cmd_cancel(self):
        """
        Cancel without doing nothing.
        """
        self.dismiss()

    def is_valid(self, folder, file):
        return True


class ImportFile(OpenFilePopup):
    """
    GUI element. Import a '.csv' file containing password.
    """

    def __init__(self, *args, **kwargs):
        super(ImportFile, self).__init__(**kwargs)

    def cmd_load(self, path, selection):
        """
        Call the import screen 'ImportScreen'.
        """
        app = App.get_running_app()
        if app and selection:
            if isinstance(selection, list):
                selection = selection[0]
            app.root.get_screen(conf.IMPORT).file = selection
            app.root.transition.direction = 'left'
            app.root.current = conf.IMPORT
            self.dismiss()
        return False

    def is_valid(self, folder, file):
        """
        Filter: displays only '.csv' files.
        """
        return str(file).endswith('csv') or str(file).endswith('txt')


class SaveFile(SaveFilePopup):
    """
    GUI element. Save file popup.
    """

    def __init__(self, *args, **kwargs):
        super(SaveFile, self).__init__(**kwargs)
        self.filechooser.dirselect = False
        self.mode = conf.SAVE

    def cmd_save(self, path, selection):
        """
        Save the file: worns when it exsts.
        """
        if selection:
            if not os.path.dirname(selection):
                selection = os.path.join(path, selection)
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
        """
        Save and exit the popup.
        """
        f = file
        popup = CipherPopup()
        popup.title = f'{self.title} to: {f}'
        popup.file = f
        popup.mode = self.mode
        popup.open()
        self.dismiss()

    def cmd_cancel(self):
        """
        Cancel and exit the popup.
        """
        self.dismiss()


class ExportFile(SaveFilePopup):
    """
    GUI element. Export file popup.
    """

    def __init__(self, *args, **kwargs):
        super(ExportFile, self).__init__(**kwargs)

    def cmd_save(self, path, selection):
        """
        Save the file: worns when it exsts.
        """
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
        """
        Export the current file to '.csv' password file.
        It calls 'SkipKeyApp.export()'.
        """
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
    """"
    GUI element. Login popup to decipher and set the random key.
    """
    # Widget hooks
    pr_login_wid = ObjectProperty(None)
    pr_seed_wid = ObjectProperty(None)

    def __init__(self, title='', *args, **kwargs):
        super(LoginPopup, self).__init__(**kwargs)
        # Current file
        self.file = None
        self.title = title

    def cmd_enter(self, app):
        """Button callback: enter the 'ListScreen'. 
        Preconditions: enter decipher password and casual seed."""
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
                app.root.current = conf.LIST
                self.reset()
                self.dismiss()
            else:
                app.unsecure()
        else:
            message(_('Login warning'), _('Fill password and seed'), 'w')
            return False
        return True

    def cmd_exit(self, app):
        """Exit login screen doing nothing."""
        self.reset()
        self.dismiss()
        return True

    def reset(self):
        """Reset user input."""
        self.pr_login_wid.pr_password.text = ''
        # self.pr_login.confirm.text = ''
        self.pr_seed_wid.pr_seed.text = ''


class CipherPopup(Popup):
    """
    GUI element. Cipher file popup enable user to choose a password and a casual seed,
    and an algorithm for cripring the file and generating the casual secret key
    from the seed.
    """
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
        self.mode = conf.SAVE  # or COPY

    def cmd_enter(self, app):
        """Set the security and enter the list screen."""
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
            if self.mode is conf.SAVE and app.secure(cryptod=cd, passwd=p, seed=s) and app.save(file=self.file, force=True):
                app.file = self.file
                self.dismiss()
                app.root.transition.direction = 'left'
                app.root.current = conf.LIST
            elif self.mode is conf.COPY and app.copy(file=self.file, cryptod=cd, passwd=p, seed=s):
                self.dismiss()
                app.root.transition.direction = 'left'
                app.root.current = conf.LIST
            self.reset()
        else:
            message(_('Login warning'), _('Fill password and seed'), 'w')
            return False
        return True

    def cmd_exit(self, app):
        """Exit the popup doing nothing"""
        self.reset()
        self.dismiss()
        return True

    def cipher_algorithms(self):
        """Returns the list of available ciphers algorithms."""
        return list(cryptofachade.cipher_algorithms().keys())

    def key_derivators(self):
        """Returns the list of available key derivation functions."""
        return list(cryptofachade.key_derivators().keys())

    def reset(self):
        """Clear user input."""
        self.pr_login_wid.pr_password.text = ''
        self.pr_login_wid.pr_confirm.text = ''
        self.pr_seed_wid.pr_seed.text = ''


class InfoPopup(Popup):
    """
    GUI element. Popup to display information about current file and
    security settings."""
    # Properties: Login and seed
    pr_keyderive = ObjectProperty(None)
    pr_algorithm = ObjectProperty(None)
    pr_mode = ObjectProperty(None)
    pr_keysize = ObjectProperty(None)
    pr_iterations = ObjectProperty(None)
    pr_file = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(InfoPopup, self).__init__(**kwargs)
        self.guic = GuiController(self)
        pass

    def set_fields(self, cryptod, **kwargs):
        """Set the value of widget fields."""
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
    """
    GUI element. Tag management popup. Tag can be added, deleted and renamed.
    When renamed: all item list entry tag is replaced with the renamed one.
    When deleted: all items with the deleted tag are cleared."""
    # Widget hooks
    pr_tag = ObjectProperty(None)

    def __init__(self, *args, **kwargs):
        super(EditTagPopup, self).__init__(**kwargs)
        self.mode = None
        self.old = None

    def cmd_cancel(self, args):
        """Cancel without change anything. """
        self.mode = self.old = None
        self.dismiss()
        return True

    def cmd_save(self, app):
        """Save and apply change to items."""
        tag = self.pr_tag.text
        if tag == _(conf.TAGS):
            message(tag, _('Action failed because: %s is already used.') %
                    (tag), 'w')
            return False

        if self.mode == conf.DELETE and self.old:
            tag = ''
        elif self.mode == conf.ADD and self.old == '':
            # tag = tag
            if model.in_items(items=app.items, value=tag, key='tag', casefold=True):
                message(
                    tag, _('Action failed because: %s is already used.') % (tag), 'w')
                return False
            else:
                app.root.get_screen(conf.EDIT).pr_tag.text = tag
        elif self.mode == conf.RENAME and self.old:
            tag = tag
        else:
            return False

        for item in model.item_iterator(items=app.items, key='tag', value=self.old):
            item_old = item.copy()
            item['tag'] = tag
            app.add_memento(new=item, old=item_old, action=conf.UPDATE)
        self.mode = self.old = None
        self.dismiss()
        return True


class EnterScreen(Screen):
    """GUI element. App enter screen."""
    pr_recentfiles = ObjectProperty(None)

    def __init__(self, *args, **kwargs):
        super(EnterScreen, self).__init__(**kwargs)
        self.app = None

    def on_enter(self):
        """Load recent files."""
        self.app = App.get_running_app()
        self.pr_recentfiles.values = self.app.get_recent_files()

    def cmd_recent(self):
        """Choose a recent file and call login screen."""
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
        """Create a new file e go to login screen."""
        file = ''
        popup = SaveFile()
        popup.title = _('New file: %s') % (file)
        popup.open()
        return True

    def cmd_open(self):
        """Open an existing file from filesystem and call login screen."""
        popup = OpenFile()
        popup.title = _('Open')
        popup.open()
        return True

    def cmd_clear(self):
        """Clear recent files."""
        self.app.clear_recent_files()
        self.pr_recentfiles.values = self.app.get_recent_files()
        return True

    def cmd_exit(self):
        """Exit the app doing nothing. """
        self.app.stop()
        # sys.exit()
        return True


class ListScreen(Screen):
    """GUI element. Main screen with the list of user accounts."""
    # Widget hooks
    pr_tag = ObjectProperty(None)
    pr_search = ObjectProperty(None)
    pr_expiring = ObjectProperty(None)
    pr_item_list_wid = ObjectProperty(None)

    class Find():
        def __init__(self, pattern=None, sublist=[], *args, **kwargs):
            self.sublist = sublist
            self.pattern = pattern

    def __init__(self, **kwargs):
        super(ListScreen, self).__init__(**kwargs)
        self.app = App.get_running_app()
        self.infopopup = None
        self.on_enter_callback = self.on_enter_default
        self.find = ListScreen.Find()  # Working sublist of items
        self.guic = GuiController(self)

    def on_enter(self):
        """Call when enter screen."""
        self.on_enter_callback()

    def on_enter_default(self):
        """Call back 'on_enter'. Prepare data to display the list.
        Default view."""
        if self.pr_tag.disabled:
            self.pr_tag.disabled = False
            self.pr_search.disabled = False
        tags = self.build_tags()
        self.pr_tag.values = tags
        self.app.root.get_screen(conf.EDIT).pr_tag.values = tags

        if not self.pr_tag.text:
            self.pr_tag.text = self.pr_tag.values[0]
        elif self.pr_tag.text != self.pr_tag.values[0]:
            self.cmd_tag_selected()
        elif self.pr_search.text:
            # Refresh list to take into account possible deleted items
            self.find = ListScreen.Find()
            self.cmd_search()
        else:
            self._fill_items(self.app.items)
            pass
        self.counter()

    def on_enter_expiring(self, after=False):
        """Call back 'on_enter'. Prepare data to display the list.
        Expiring accounts view."""
        if after:
            if not self.pr_tag.disabled:
                self.pr_tag.disabled = True
                self.pr_search.disabled = True
            pwd_warn = float(self.app.config.getdefault(
                SkipKeyApp.SETTINGS, SkipKeyApp.PWDWARN, 7))
            pwd_lifetime = float(self.app.config.getdefault(
                SkipKeyApp.SETTINGS, SkipKeyApp.PWDLIFETIME, 6)) * 30.45
            today = datetime.now()
            self.pr_item_list_wid.clear()
            date_keys = ['changed', 'created']  # Where to search for dates
            for i in self.app.items:
                try:
                    elapse = elapsed_days(i, date_keys)
                    if (expire_on(i, date_keys, pwd_lifetime) - today).days <= pwd_warn:
                        w_item = self.pr_item_list_wid.add(
                            item_class=ItemComposite, name=i['name'])
                        text = _('Set %s days ago') % (str(elapse))
                        w_item.add(SubItem(sid='elapsed', text=text))
                        w_item.add(WarningItem(sid='warning',
                                               header=self.pr_item_list_wid,
                                               kwparams={'max': pwd_lifetime, 'elapsed': elapse}))
                except Exception:
                    continue
            self.counter()
        else:
            Clock.schedule_once(lambda dt: self.on_enter_expiring(after=True))
        return True

    def on_leave(self):
        """Call when leave screen. Do nothing."""
        pass

    def build_tags(self):
        """Internal. Extract a list of tag alphabetically
        ordered from the item list."""
        t = list(set(i['tag'] for i in self.app.items))
        t.sort(key=str.lower)
        tags = [conf.TAGS, ] + t
        return tags

    def _fill_items(self, items):
        """
        Internal. Fill the item list.

        Every item is an account.
        """
        # pwd_warn = float(self.app.config.getdefault(
        #     SkipKeyApp.SETTINGS, SkipKeyApp.PWDWARN, 7))
        pwd_lifetime = float(self.app.config.getdefault(
            SkipKeyApp.SETTINGS, SkipKeyApp.PWDLIFETIME, 6)) * 30.45
        self.pr_item_list_wid.clear()
        date_keys = ['changed', 'created']  # Where to search for dates
        for i in items:
            w_item = self.pr_item_list_wid.add(ItemComposite, **i)
            # text = _('Set %s days ago') % (str(elapsed_days(i, date_keys)))
            # w_item.add(SubItem(sid='elapsed', text=text))
            elapse = elapsed_days(i, date_keys)
            w_item.add(WarningItem(sid='warning',
                                   header=self.pr_item_list_wid,
                                   kwparams={'max': pwd_lifetime, 'elapsed': elapse}))
        self.counter()

    def counter(self):
        """Return the number of displayed item accounts over the total item."""
        self.ids['_lab_counter'].text = f'{self.pr_item_list_wid.count} / {len(self.app.items)}'

    def cmd_option(self, action, app):
        """Screen menu command."""
        if action == conf.INFO:
            if not self.infopopup:
                self.infopopup = InfoPopup()
                self.infopopup.title = _('Info')
            self.infopopup.set_fields(app.cryptod, file=app.file)
            self.infopopup.open()
        elif action == conf.COPY:
            popup = SaveFile()
            popup.filechooser.rootpath = app.file
            popup.title = _('Copy to')
            popup.mode = conf.COPY
            popup.open()
        elif action == conf.IMPORT:
            popup = ImportFile()
            popup.title = _('Import from:')
            popup.open()
        elif action == conf.EXPORT:
            popup = ExportFile()
            popup.title = _('Export to:')
            popup.open()
        elif action == conf.CHANGES:
            app.root.transition.direction = 'left'
            app.root.current = conf.CHANGES
        else:
            pass
        return True

    def cmd_tag_selected(self, after=False):
        """Filter list everytime a tag is selected."""
        if self.pr_search.text:
            self.pr_search.text = ''

        if after:
            if self.pr_tag.text == conf.TAGS:
                self._fill_items(self.app.items)
            else:
                sublst = model.filter_items(
                    items=self.app.items, value=self.pr_tag.text, key='tag')
                sublst.sort(key=lambda x: str.lower(x['name']))
                self.pr_item_list_wid.clear()
                self._fill_items(sublst)
            self.counter()
            return True
        else:
            Clock.schedule_once(
                lambda dt: self.cmd_tag_selected(after=True), 0.1)

    def clear_search(self):
        """Clear the search text field."""
        if len(self.pr_search.text) > 0:
            self.pr_search.text = ''
        self._fill_items(self.app.items)

    def cmd_search(self, after=False, at_least=3):
        """
        Search items from the field input text.

        For performance reasons it's better search for sublist.
        """
        if after:
            # Search text: add characters -> search on sublist
            if self.find.pattern and str(self.pr_search.text).casefold().startswith(str(self.find.pattern).casefold()):
                sublist = model.search_items(
                    items=self.find.sublist, text=self.pr_search.text)
                sublist.sort(key=lambda x: str.lower(x['name']))
                self.find = ListScreen.Find(self.pr_search.text, sublist)
            # Search text: less characters - search on full list
            # Search text: changed characters - search on full list
            else:
                sublist = model.search_items(
                    items=self.app.items, text=self.pr_search.text)
                sublist.sort(key=lambda x: str.lower(x['name']))
                self.find = ListScreen.Find(self.pr_search.text, sublist)
                pass

            self.pr_item_list_wid.clear()
            self._fill_items(sublist)
            self.counter()
        else:
            Clock.schedule_once(lambda dt: self.cmd_search(after=True), 0.1)
        return True

    def cmd_add(self, args):
        """Add a new item account. Call 'EditScreen'."""
        # Apply configuration
        config = self.app.config
        item = model.new_item()
        item['length'] = str(config.getdefault(
            SkipKeyApp.SETTINGS, SkipKeyApp.PWDLEN, 10))
        item['auto'] = str(config.getdefault(
            SkipKeyApp.PWDAUTO, SkipKeyApp.PWDLEN, True))

        self.manager.get_screen(conf.EDIT).set_item(item)
        self.manager.transition.direction = 'left'
        self.manager.current = conf.EDIT
        return True

    def cmd_back(self, app, after=False):
        """Return to login: stop the running mode and return
        to login screen. Warns the user that everything is cleared and
        data are going to be lost."""
        if after:
            self.pr_item_list_wid.clear()
            self.pr_tag.text = ''
            app.initialize()
            self.manager.transition.direction = 'right'
            self.manager.current = conf.ENTER
            return True
        else:
            if app.file:
                decision(_('Leave'), _('Exit %s without saving?') % (os.path.basename(app.file)),
                         fn_ok=self.cmd_back, ok_kwargs={'app': app, 'after': True})
            else:
                self.cmd_back(app=app, after=True)
        return False

    def cmd_expiring(self, widget, state, after=False):
        """Toggle the view between the standard account list
        and the password expiring list."""
        if state == 'down':
            self.on_enter_callback = self.on_enter_expiring
        else:
            self.on_enter_callback = self.on_enter_default
        self.on_enter()


class EditScreen(Screen):
    """GUI element. Account editing screen."""
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
        self.guic = GuiController(self)

    def set_item(self, item):
        """Initialise screen fields from a dictionary."""
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
        """Discard all changes, return to list screen."""
        self.manager.transition.direction = 'right'
        self.manager.current = conf.LIST
        return True

    def cmd_delete(self, app):
        """Delete this account, return to list screen."""
        if app.delete_item(self.item):
            self.manager.transition.direction = 'right'
            self.manager.current = conf.LIST
        return True

    def cmd_save(self, app):
        """Save this account, return to list screen."""
        tag = self.pr_tag.text
        if tag == conf.TAGS:
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

        item = model.new_item(
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
            self.manager.current = conf.LIST
        return True

    def _call_tag_popup(self, instance, spinner, mode):
        """Edit tag: call edit tag popup."""
        popup = EditTagPopup()
        if mode == conf.DELETE:
            popup.title = ': '.join((instance.text, spinner.text))
            popup.pr_tag.text = spinner.text
            popup.old = spinner.text
            popup.mode = conf.DELETE
        elif mode == conf.ADD:
            popup.title = ': '.join((instance.text, ))
            popup.mode = conf.ADD
            popup.old = ''
        elif mode == conf.RENAME:
            popup.title = ': '.join((instance.text, spinner.text))
            popup.mode = conf.RENAME
            popup.old = spinner.text
        popup.open()

    def item_check(self, item):
        """Check mandatory fields before saving the account item."""
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
        """Nothing to do here."""
        return True

    def cmd_renametag(self, instance, spinner):
        """Rename the current tag and updates all items accordingly
        to the renamed tag. """
        return self._call_tag_popup(instance, spinner, conf.RENAME)

    def cmd_deletetag(self, instance, spinner):
        """Delete the current tag and deletes the items tag accordingly."""
        return self._call_tag_popup(instance, spinner, conf.DELETE)

    def cmd_addtag(self, instance, spinner):
        """Delete the current tag from the items."""
        return self._call_tag_popup(instance, spinner, conf.ADD)


class ImportScreen(Screen):
    """
    GUI element. Screen enabling the import of a '.csv' password file
    into the current one."""
    pr_mapping = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(ImportScreen, self).__init__(**kwargs)
        self.file = None
        self.guic = GuiController(self)

    def on_enter(self, **kwargs):
        """Load a template for mapping the column headers of the input
        file to the headers of the current file."""
        text = ',\n'.join(
            [f"('{i}', '{j}')" for i, j in model.mapping.items()])
        self.pr_mapping.text = text
        super(ImportScreen, self).on_enter(**kwargs)

    def cmd_back(self, app):
        """Go back to the list screen without doing anything."""
        app.root.transition.direction = 'right'
        app.root.current = conf.LIST

    def cmd_import(self, app, mapping):
        """Import the '.csv' into current file. Once the mapping is applied,
        new accounts are formed and appended to the current list.
        New records are normalized by adding calculated values in place of missing
        information. Nevertheless errors may occurs."""
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
                app.add_memento(new=None, old=item, action=conf.IMPORT)
            app.root.transition.direction = 'right'
            app.root.current = conf.LIST
        return True

    def mapping_help(self):
        return _('Write couples separated by comma:\n(\'<source>\', \'<target>\').')


class ChangesScreen(Screen):
    """
    GUI element. Screen collecting all changes during a program session. 
    It enables user to restore values unintentionally changed.
    The new account is replaced with the unchanged one. 
    At present, once the program is closed changes history is lost."""
    # Widget hooks
    pr_actions = ObjectProperty(None)
    pr_changed_item_list_wid = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(ChangesScreen, self).__init__(**kwargs)
        self.app = App.get_running_app()
        self.guic = GuiController(self)

    def _fill_fields(self, mementos):
        """
        Fetch changes from the app history.

        Parameters:
        -----------
        - mementos:
        list of memento objects. 
        """
        self.pr_changed_item_list_wid.clear()
        try:
            # Doesn't work with deleted records
            former = mementos[self.pr_actions.values.index(
                self.pr_actions.text)]['body']
            try:  # No records found
                current = self.app.items[model.index_of(
                    items=self.app.items, key='name', value=former['name'])]
            except Exception:
                current = former

            for key, value in former.items():
                self.pr_changed_item_list_wid.add(item_class=Comparison,
                                                  key=key, name=SkipKeyApp.LABELS[key],
                                                  last=current[key],
                                                  former=value)
        except Exception:
            pass

    def on_enter(self):
        """Screen initialization."""
        if len(self.app.history) > 0:
            self.pr_actions.values = ['{: <10s} - {: <10s} - {:s}'.format(
                m['name'], m['action'], m['timestamp'].isoformat(sep=' ', timespec='seconds')) for m in self.app.history]
            self.pr_actions.text = self.pr_actions.values[0]
            self._fill_fields(self.app.history)
        else:
            self.pr_actions.values = [_('No changes'), ]
            self.pr_actions.text = self.pr_actions.values[0]

    def cmd_back(self, app):
        """Return to list, discard all changes."""
        self.manager.transition.direction = 'right'
        self.manager.current = conf.LIST
        return True

    def cmd_undo(self, *args):
        """Set the original item and discard the last changed one,
        deletes it from history. Undo of Undo is, at present, impossible."""
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
    """
    GUI element. Generic tag spinner."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class LoginPanel(BoxLayout):
    """
    GUI element. Panel for user login.
    """
    # Widget hooks
    pr_password = ObjectProperty(None)
    pr_strenght = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(LoginPanel, self).__init__(**kwargs)
        self.guic = GuiController(self)

    def cmd_text(self, text):
        """
        Callback for TextInput on_text event. 
        """
        self.pr_strenght.set_strength(text)

    def changed(self):
        """
        Return if the pasword has been changed.
        """
        if self.pr_password.text:
            return self.pr_password.text != ''
        return False


class UserPanel(BoxLayout):
    """
    GUI element. Panel for changing password.
    It is used by LoginPopup, CipherPopup. 
    """
    # Widget hooks
    pr_password = ObjectProperty(None)
    pr_confirm = ObjectProperty(None)
    pr_strenght = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(UserPanel, self).__init__(**kwargs)
        self.size_hint_max_y = None
        self.bind(minimum_height=self.setter('height'))
        self.guic = GuiController(self)

    def cmd_text(self, text):
        """
        Callback for TextInput on_text event. 
        """
        self.pr_strenght.set_strength(text)

    def set_item(self, item):
        """
        Initialize the input fields. 
        """
        self.pr_password.text = ''
        self.pr_confirm.text = ''

    def changed(self):
        """
        Return True if the pasword has been changed.
        """
        if self.pr_password.text and self.pr_confirm.text:
            return self.pr_password.text != '' and self.pr_password.text == self.pr_confirm.text
        return False


class SeedPanel(BoxLayout):
    """
    GUI element. Panel for random seed input.

    It is used by LoginPopup, CipherPopup.
    """
    # Widget hooks
    pr_seed = ObjectProperty(None)
    pr_strenght = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(SeedPanel, self).__init__(**kwargs)
        self.guic = GuiController(self)

    def cmd_text(self, text):
        """
        Callback for TextInput on_text event. 
        """
        self.pr_strenght.set_strength(text)

    def changed(self):
        """
        Return True if the seed has been changed.
        """
        if self.pr_seed.text:
            return self.pr_seed.text != ''
        return False


class AutoPanel(BoxLayout):
    """
    GUI element. Panel for generating the password.

    It is used in EditScreen.
    """
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
        self.guic = GuiController(self)

    def set_strength(self, text):
        self.pr_strenght.set_strength(text)

    def set_item(self, item):
        """
        Initialize the input fields from currently edited account item.
        """
        self.pr_length.text = item['length']
        self.pr_symbols.text = item['symbols']
        self.pr_numbers.text = item['numbers']
        self.pr_letters.active = item['letters'] == 'True'
        self.pr_strenght.set_strength('')
        self.pr_password.text = ''

    def changed(self):
        """
        Return True if the pasword has been changed.
        """
        if self.pr_password.text:
            return self.pr_password.text != ''
        return False


class PasswordStrenght(BoxLayout):
    """
    GUI element. Password strength gauge.
    """
    # Widget hooks
    pr_strenght = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(PasswordStrenght, self).__init__(**kwargs)

    def set_strength(self, text):
        """
        Set the password strenght value.

        It evaluates the password strength from the algorithm
        in passwordmeter.py.
        """
        self.pr_strenght.value = passwordmeter.strength(text)


class AccountItemList(ItemList):
    """
    GUI element. Accounts list container.

    The list is managed in EditScreen.
    """

    def __init__(self, *args, **kwargs):

        super(AccountItemList, self).__init__(mask=item_mask, **kwargs)
        self.add_bubble(Factory.ItemActionBubble())


class ChangedItemList(ItemList):
    """
    GUI element. Container of changed account items.

    The list is managed in ChangesScreen.
    """

    def __init__(self, *args, **kwargs):
        super(ChangedItemList, self).__init__(*args, **kwargs)


class ItemActionBubble(Bubble):
    """
    GUI element. Bubble context menu for a selected account item.

    Menu options:
    -------------
    - Get the account url. 
    - Get the account user. 
    - Get the account password. 
    - Get the account login: 'user' [tab] 'password'. 
    - Edit the account item: leave the screen and enter 'EditScreen'.
    """

    def __init__(self, **kwargs):
        super(ItemActionBubble, self).__init__(**kwargs)
        # Current selected item
        self.item = None
        # Clear clipboard scheduled event
        self.evt_clipboard = None

    def cmd_url(self, app):
        # TODO System call to browser
        item = app.items[model.index_of(
            items=app.items, value=self.item.kwparams['name'], key='name')]
        url = item['url']
        try:
            browser.open(url, new=0, autoraise=True)
        except Exception as e:
            self._publish(app, url)

        return True

    def cmd_user(self, app):
        """
        Publish user.
        """
        item = app.items[model.index_of(
            items=app.items, value=self.item.kwparams['name'], key='name')]
        user = item['login']
        self._publish(app, user)
        return True

    def cmd_password(self, app):
        """
        Publish password.
        """
        p = self._password(app)
        self._publish(app, p)
        return True

    def cmd_login(self, app):
        """
        Publish 'user TAB password' and dismiss bubble.
        """
        item = app.items[model.index_of(
            items=app.items, value=self.item.kwparams['name'], key='name')]
        p = self._password(app)
        login = f'{item["login"]}\t{p}'
        self._publish(app, login)
        self.reset()
        return True

    def _password(self, app):
        item = app.items[model.index_of(
            items=app.items, value=self.item.kwparams['name'], key='name')]
        if item['auto'] == 'False':
            p = app.decrypt(item['password'])
        # Clipboard.copy(self.item.item['login'])
        else:
            p = app.show(item)
        return p

    def _publish(self, app, text):
        autocompletion = app.config.getdefault(
            SkipKeyApp.SETTINGS, SkipKeyApp.AUTOCOMP, True) == '1'
        pwd_timeout = int(app.config.getdefault(
            SkipKeyApp.SETTINGS, SkipKeyApp.PWDTIME, '15'))
        if text == False:
            return False
        if autocompletion:
            daemon = LoginDaemon(text=text, timeout=pwd_timeout)
            daemon.start()
        else:
            Clipboard.copy(text)
            # Once at a time
            if app.evt_clipboard:
                app.evt_clipboard.cancel()
            app.evt_clipboard = Clock.schedule_once(
                lambda dt: Clipboard.copy(' '), pwd_timeout)
            # app.evt_clipboard = Clock.schedule_once(self.cb_clean, timeout)
        return True

    # def cb_clean(self, dt):
    #     Clipboard.copy(' ')
    def cmd_edit(self, app):
        """
        Edit the account item. 

        Leave the screen and enter 'EditScreen'.
        """
        item = app.items[model.index_of(
            items=app.items, value=self.item.kwparams['name'], key='name')]
        app.root.get_screen(conf.EDIT).set_item(item)
        # app.root.get_screen(EDIT).set_item(self.item.kwparams)
        app.root.transition.direction = 'left'
        app.root.current = conf.EDIT
        self.reset()
        return True

    def reset(self):
        # Free the selection to enable re-selection
        self.item = None
        self.parent.remove_widget(self)

    def on_touch_down(self, touch):
        """
        Remove bubble when click outside it.
        """
        if not self.collide_point(touch.x, touch.y):
            self.reset()
        return super(ItemActionBubble, self).on_touch_down(touch)


class SkipKeyApp(App):
    """
    GUI element. Main App. 
    """
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
        self.icon = '%s\\%s' % (conf.icons_dir, conf.ICON)
        # ----------------> App configuration
        self.user_data_dir
        # Create the screen manager
        # Builder.load_file('commons.kv')
        # Builder.load_file('screens_test.kv')
        sm = ScreenManager()
        self.root = sm

        # kivy.core.window.Window.clearcolor = (1, 0, 0, 1)

        sm.add_widget(EnterScreen(name=conf.ENTER))
        sm.add_widget(ListScreen(name=conf.LIST))
        sm.add_widget(EditScreen(name=conf.EDIT))
        sm.add_widget(ImportScreen(name=conf.IMPORT))
        sm.add_widget(ChangesScreen(name=conf.CHANGES))
        # look&feel manager
        self.guic = GuiController(sm)
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
        """The App class handles '.ini' files automatically add sections and
        default parameters values. """
        config.adddefaultsection(SkipKeyApp.SETTINGS)
        config.setdefault(SkipKeyApp.SETTINGS, SkipKeyApp.TIMEOUT, 5)  # min
        config.setdefault(SkipKeyApp.SETTINGS, SkipKeyApp.AUTOCOMP, True)
        # Part user+tab+password
        config.setdefault(SkipKeyApp.SETTINGS, SkipKeyApp.PWDTIME, 15)  # sec.
        config.setdefault(SkipKeyApp.SETTINGS, SkipKeyApp.PWDLEN, 10)
        config.setdefault(SkipKeyApp.SETTINGS, SkipKeyApp.PWDAUTO, True)
        config.setdefault(SkipKeyApp.SETTINGS, SkipKeyApp.PWDLIFETIME, 6)
        config.setdefault(SkipKeyApp.SETTINGS, SkipKeyApp.PWDWARN, 7)
        config.setdefault(SkipKeyApp.SETTINGS, SkipKeyApp.LOG, 0)
        config.adddefaultsection(SkipKeyApp.RECENT_FILES)

    def on_start(self):
        """
        Event handler for the on_start event which is fired after initialization
        (after build() has been called) but before the application has started running."""
        # Init screens:
        return super().on_start()

    def on_pause(self):
        """
        Event handler called when Pause mode is requested. You should return
        True if your app can go into Pause mode, otherwise return False and your
        application will be stopped."""
        return super().on_pause()

    def on_resume(self):
        """
        Event handler called when your application is resuming from the Pause mode."""
        return super().on_resume()

    def on_stop(self):
        """
        Event handler for the on_stop event which is fired when the application
        has finished running (i.e. the window is about to be closed)."""
        self.save(file=self.file)
        return super().on_stop()

    def open(self, file, passwd, seed):
        """
        Open the file and prepare the records"""
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
        """
        Update the list of recently opened files"""
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
        """
        Clear the list of recently opened files"""
        for i in range(self.MAXF):
            self.config.set(SkipKeyApp.RECENT_FILES, f'_{i}', '')
        self.config.write()
        return True

    def get_recent_files(self):
        """
        Get the list of recently opened files, these can have the same name,
        but different path: only available files are appended to the list."""
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
        """
        Delete an item from the item list.
        """
        if after:
            index = model.index_of(self.items, item['name'], 'name')
            if index != None:  # Delete
                self.add_memento(
                    new=None, old=self.items.pop(index), action=conf.DELETE)
            else:
                return False
            self.items.sort(key=lambda k: str(k['name']).lower())
        else:
            Clock.schedule_once(lambda dt: self.delete_item(
                item=item, after=True), 0)
        return True

    def save_item(self, item, history=True, after=False):
        """
        Save a new item and to the item list.

        The item identifier is its name, so it is not possible to have
        more than one item with the same name. 
        The changed date is updated only if password was changed.
        """
        if after:
            index = model.index_of(self.items, item['name'], 'name')
            # Update
            if index != None:
                if history:
                    old = self.items[index]
                    self.add_memento(
                        new=item, old=old, action=conf.UPDATE)
                self.items[index] = item
                # Update the changed only if password was changed
                if old['password'] != item['password']:
                    self.items[index]['changed'] = datetime.now(
                    ).isoformat(sep=' ', timespec='seconds')
            else:  # Append
                item['created'] = item['changed'] = datetime.now(
                ).isoformat(sep=' ', timespec='seconds')
                self.items.append(item)
                if history:
                    self.add_memento(new=None, old=item, action=conf.APPEND)
            self.items.sort(key=lambda k: str(k['name']).lower())
        else:
            Clock.schedule_once(lambda dt: self.save_item(
                item=item, history=history, after=True), 0)
        return True

    def add_memento(self, new, old, action=''):
        """
        History Data model: for the present the history is a back up of
        the data model.
        {'name': item_name, 'changed': timestamp, 'item': item_json_dump}
        """
        if new != old:
            self.history[0:0] = [model.memento(item=old, action=action)]

    def encrypt(self, text):
        """
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
        edit_screen = self.root.get_screen(conf.EDIT)
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
            pwd, salt = self.cipher_fachade.secret(
                seed, conf.ITERATIONS, pattern)
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
        Show a generated password and its strenght.
            Parameters
        ----------
        item : the item.

            Returns
        ----------
        boolean
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
            p = self.cipher_fachade.password(
                seed, salt, conf.ITERATIONS, pattern)
            return p
        except ValueError as e:
            message(_('Password'), e, 'e')
        return False

    def secure(self, cryptod, passwd, seed):
        """
        Turn the security on (call once)."""
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
        """Turn the security off."""
        self.cipher_fachade = None
        self.session_key = None
        self.session_seed = None
        self.keywrapper = None
        self.seedwrapper = None
        self.cryptod = None
        return True

    def timeout(self, after=False):
        """Security timeout"""
        if after:
            self.count_down -= 1
            self.pr_timer = hh_mm_ss(self.count_down)
            if self.count_down < 1:
                self.save(self.file)
                self.initialize()
                self.root.transition.direction = 'right'
                self.root.current = conf.ENTER
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
        """Initializes app context"""
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

        The file is saved if any changes was made, otherwise return
        without saving. If the optional parameter force is True, then
        the file is saved even if no changes were made.
        The file is always encrypted.
        Parameters
        ----------
        - file :
        the file path.
        - force :
        force the saving.

        Returns
        -------
        True :
        if the file was saved, otherwise returns False.
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
