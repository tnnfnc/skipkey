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
# import kivy_environment
import threading
import kivy
import base64
import json
import re
import os
import sys
from datetime import datetime, timedelta
#
import webbrowser as browser
#
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
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.app import App
from kivy import utils
#
from writer import TypewriteThread
from uilist import (ItemList, Item, ItemComposite,
                    Comparison, ProgressItem, SubItem, WarningItem)
from uifilemanager import OpenFilePopup, SaveFilePopup
import cryptofachade
import password
import model
from localize import translate
from uicontroller import GuiController
#
dummy = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dummy)

# =============================================================================
# Kivy config
# =============================================================================
kivy.require('1.11.0')  # Current kivy version

MAJOR = 1
MINOR = 1
MICRO = 1
RELEASE = True
__version__ = '%d.%d.%d' % (MAJOR, MINOR, MICRO)

current_dir = os.path.dirname(os.path.realpath(__file__))
icons_dir = '%s\data\icons' % (current_dir)
locale_dir = '%s\locale' % (current_dir)


# Screen Names
ENTER = 'Enter'
LIST = 'List'
EDIT = 'Edit'
CHANGES = 'changes'
IMPORT = 'import'

# App
ICON = 'skip.png'
TAGS = ('...')  # Default for all tags


_ = translate(domain='skipkey', localedir=locale_dir, languages=['it'])


def dp(pix):
    return metrix.dp(pix)


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


Builder.load_file('kv/commons.kv')
Builder.load_file('kv/dynamic.kv')
Builder.load_file('kv/popup.kv')
Builder.load_file('kv/widgets.kv')
Builder.load_file('kv/popups.kv')
Builder.load_file('kv/enter.kv')
Builder.load_file('kv/list.kv')
Builder.load_file('kv/edit.kv')
Builder.load_file('kv/import.kv')
Builder.load_file('kv/changes.kv')


class MessagePopup(Popup):
    # Widget hooks
    pr_message = ObjectProperty(None)
    pr_image = ObjectProperty(None)

    def __init__(self, *args, **kwargs):
        super(MessagePopup, self).__init__(**kwargs)

    def show(self, title='', text='', type='i'):
        text = utils.escape_markup(f'{text}')
        if type == 'e':
            text = ''.join(('[b][color=ff0000]', text, '[/color][/b]'))
            self.pr_image.source = 'data/icons/bug.png'
        elif type == 'w':
            text = ''.join(('[b][color=ffff00]', text, '[/color][/b]'))
            self.pr_image.source = 'data/icons/pen.png'
        elif type == 'i':
            text = ''.join(('[b][color=00ff00]', text, '[/color][/b]'))
            self.pr_image.source = 'data/icons/ok.png'
        else:
            pass

        self.title = title
        self.pr_message.text = text
        self.open()


class DecisionPopup(Popup):
    # Widget hooks
    pr_message = ObjectProperty(None)
    fn_ok = ObjectProperty(None)
    fn_canc = ObjectProperty(None)
    ok_kwargs = ObjectProperty(None)
    canc_kwargs = ObjectProperty(None)

    def __init__(self, title='', text='', *args, **kwargs):
        super(DecisionPopup, self).__init__(**kwargs)
        self.pr_message.text = text
        self.title = title

    def show(self, title, text, fn_ok=None, fn_canc=None, ok_kwargs={}, canc_kwargs={}, **kwargs):
        self.title = title
        self.pr_message.text = ''.join(
            ('[b]', utils.escape_markup(text), '[/b]'))
        self.fn_ok = fn_ok
        self.fn_canc = fn_canc
        self.canc_kwargs = canc_kwargs
        self.ok_kwargs = ok_kwargs

        self.open()

    def cmd_ok(self):
        if self.fn_ok:
            try:
                self.fn_ok(**self.ok_kwargs)
                return True
            except Exception:
                return False
        return True

    def cmd_cancel(self):
        if self.fn_canc:
            try:
                self.fn_canc(**self.canc_kwargs)
                return False
            except Exception:
                return False
        return False


message, decision = MessagePopup().show, DecisionPopup().show


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
            app.root.get_screen(IMPORT).file = selection
            app.root.transition.direction = 'left'
            app.root.current = IMPORT
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
        self.action = self.save

    def openCopy(self):
        self.open()
        self.action = self.copy

    def cmd_save(self, path, selection):
        """
        Save the file: worns when it exsts.
        """
        if selection:
            if not os.path.dirname(selection):
                selection = os.path.join(path, selection)
            if not os.path.exists(selection):
                self.action(selection)
            else:
                decision(
                    self.title,
                    _('%s exists:\noverwrite?') % (
                        os.path.basename(selection)),
                    fn_ok=self.action,
                    ok_kwargs={'file': selection, })
            self.dismiss()
        return False

    def save(self, file):
        """
        Save and exit the popup.
        """
        popup = CipherPopup()
        popup.title = f'{self.title} {file}'
        popup.openSave(file)

    def copy(self, file):
        """
        Save and exit the popup.
        """
        popup = CipherPopup()
        popup.title = f'{self.title} {file}'
        popup.openCopy(file)

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
            message(_('Export failed: %s') % (str(*e.args)),
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

    def cmd_enter(self):
        """Button callback: enter the 'ListScreen'.
        Preconditions: enter decipher password and casual seed."""
        app = App.get_running_app()
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

            # if app.open(file=self.file, passwd=p, seed=s):
            #     app.root.transition.direction = 'left'
            #     app.root.current = LIST
            #     self.reset()
            #     self.dismiss()
            # else:
            #     app.unsecure()

            try:
                app.open(file=self.file, passwd=p, seed=s)
                app.root.transition.direction = 'left'
                app.root.current = LIST
                self.reset()
                self.dismiss()
            except IOError as e:
                message(_('Open File: %s') %
                        (os.path.basename(self.file)), e, 'e')
                app.unsecure()
            except Exception as e:
                message(_('Open File: %s') %
                        (os.path.basename(self.file)), e, 'e')
                app.unsecure()
            #
        else:
            message(_('Login warning'), _('Fill password and seed'), 'w')
            return False
        return True

    def cmd_exit(self):
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
    and an algorithm for encrypring the file and generating the casual secret key
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
        self.action = self._save

    def openSave(self, file):
        self.file = file
        self.action = self._save
        self.open()
        pass

    def openCopy(self, file):
        self.file = file
        self.action = self._copy
        self.open()
        pass

    def _save(self, cryptod, passwd, seed):
        app = App.get_running_app()
        try:
            app.secure(cryptod, passwd, seed)
            app.save(file=self.file, force=True)
            app.file = self.file
            self.dismiss()
            app.root.transition.direction = 'left'
            app.root.current = LIST
        except Exception as e:
            app.unsecure()
            message(title=_('Save File: %s') % (os.path.basename(self.file)),
                    text=_('Exception:\n%s') % (e.args[0]), type='e')
        else:
            message(title=_('Save File: %s') % (os.path.basename(self.file)),
                    text=_('File saved'), type='i')

    def _copy(self, cryptod, passwd, seed):
        try:
            app = App.get_running_app()
            app.copy(file=self.file, cryptod=cryptod, passwd=passwd, seed=seed)
            self.dismiss()
            app.root.transition.direction = 'left'
            app.root.current = LIST
        except Exception as e:
            message(_('File Copy Error'), e, 'e')
        else:
            message(title=_('Copy file: %s') % (os.path.basename(self.file)),
                    text=_('File copy successful'), type='i')

    def cmd_enter(self):
        """Set the security and enter the list screen."""
        if self.pr_login_wid.pr_password.text and self.pr_seed_wid.pr_seed.text:
            # Check login was successful (file opened) and check the key was set
            if isinstance(self.file, list):
                self.file = self.file[0]
            # Build security:
            if self.pr_kderive.text and self.pr_cipher.text and self.pr_iters.text:
                cryptod = cryptofachade.cryptodict(
                    **cryptofachade.default_cryptod)
                cryptod['algorithm'] = self.pr_cipher.text
                cryptod['pbkdf'] = self.pr_kderive.text
                cryptod['iterations'] = int(self.pr_iters.text)
                p = bytes(self.pr_login_wid.pr_password.text, encoding='utf-8')
                s = bytes(self.pr_seed_wid.pr_seed.text, encoding='utf-8')
                self.action(cryptod=cryptod, passwd=p, seed=s)
            else:
                message(_('Security setup'), _(
                    'Please choose an algorithm'), 'w')
                return False
            self.reset()
        else:
            message(_('Login warning'), _('Fill password and seed'), 'w')
            return False
        return True

    def cmd_exit(self):
        """Exit the popup doing nothing"""
        self.reset()
        self.dismiss()

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
        self.value = None

    def openAdd(self, value):
        self.value = value
        self.mode = 1
        self.open()
        pass

    def openDelete(self, value):
        self.value = value
        self.mode = -1
        self.pr_tag.text = value
        self.open()
        pass

    def openRename(self, value):
        self.value = value
        self.mode = 0
        self.open()
        pass

    def cmd_cancel(self, args):
        """Cancel without change anything. """
        self.mode = self.value = None
        self.dismiss()
        return True

    def cmd_save(self):
        """Save and apply change to items."""
        app = App.get_running_app()
        tag = self.pr_tag.text

        if tag == _(TAGS):
            message(tag, _('Action failed because: %s is already used.') %
                    (tag), 'w')
            return False
        # Delete = tag is ''
        if self.mode == -1 and self.value:
            tag = ''
        # Add a new tag
        elif self.mode == 1 and self.value == '':
            if model.contains(items=app.items, value=tag, key='tag', casefold=True):
                message(
                    tag, _('Action failed because: %s is already used.') % (tag), 'w')
                return False
            # else:
            #     app.root.get_screen(EDIT).pr_tag.text = tag
        # Rename a tag
        elif self.mode == 0:  # and self.value:
            pass
            # app.root.get_screen(EDIT).pr_tag.text = tag
        else:
            return False

        app.root.get_screen(EDIT).pr_tag.text = tag
        #
        for item in model.iterator(items=app.items, key='tag', value=self.value):
            item_old = item.copy()
            item['tag'] = tag
            app.add_history(new=item, old=item_old, action='update')
        return self.cmd_cancel(None)


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
        self.app.root.get_screen(EDIT).pr_tag.values = tags

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
        tags = [TAGS, ] + t
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
            elapse = elapsed_days(i, date_keys)
            w_item.add(WarningItem(sid='warning',
                                   header=self.pr_item_list_wid,
                                   kwparams={'max': pwd_lifetime, 'elapsed': elapse}))
        self.counter()

    def counter(self):
        """Return the number of displayed item accounts over the total item."""
        self.ids['_lab_counter'].text = f'{self.pr_item_list_wid.count} / {len(self.app.items)}'

    def cmd_info(self):
        """Screen menu command."""
        app = App.get_running_app()
        if not self.infopopup:
            self.infopopup = InfoPopup()
            self.infopopup.title = _('Info')
        self.infopopup.set_fields(app.cryptod, file=app.file)
        self.infopopup.open()

    def cmd_copy(self):
        """Screen menu command."""
        app = App.get_running_app()
        popup = SaveFile()
        popup.filechooser.rootpath = os.path.dirname(app.file)
        popup.title = _('Copy %s to:') % (os.path.basename(app.file))
        popup.openCopy()

    def cmd_import(self):
        """Screen menu command."""
        app = App.get_running_app()
        popup = ImportFile()
        popup.title = _('Import from a CSV file:')
        popup.open()

    def cmd_export(self):
        """Screen menu command."""
        app = App.get_running_app()
        popup = ExportFile()
        popup.title = _('Export %s to CSV:') % (os.path.basename(app.file))
        popup.open()

    def cmd_changes(self):
        """Screen menu command."""
        app = App.get_running_app()
        app.root.transition.direction = 'left'
        app.root.current = CHANGES

    def cmd_tag_selected(self, after=False):
        """Filter list everytime a tag is selected."""
        if self.pr_search.text:
            self.pr_search.text = ''

        if after:
            if self.pr_tag.text == TAGS:
                self._fill_items(self.app.items)
            else:
                sublst = model.select(
                    items=self.app.items, value=self.pr_tag.text, key='tag')
                # sublst.sort(key=lambda x: str.lower(x['name']))
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
            if len(self.find.sublist) != self.pr_item_list_wid.count:
                self._fill_items(self.find.sublist)
                self.counter()
        else:
            # Start search from at least two characters
            if len(self.pr_search.text) > 1:
                # Search text: add characters -> search on sublist
                if self.find.pattern and str(self.pr_search.text).casefold().startswith(str(self.find.pattern).casefold()):
                    sublist = model.search(
                        items=self.find.sublist, text=self.pr_search.text)
                    # sublist.sort(key=lambda x: str.lower(x['name']))
                    self.find = ListScreen.Find(self.pr_search.text, sublist)
                else:
                    sublist = model.search(
                        items=self.app.items, text=self.pr_search.text)
                    self.find = ListScreen.Find(self.pr_search.text, sublist)
            else:
                self.find = ListScreen.Find(
                    self.pr_search.text, self.app.items)

            Clock.schedule_once(lambda dt: self.cmd_search(after=True), 0.1)
        return True

    def cmd_add(self, args):
        """Add a new item account. Call 'EditScreen'."""
        # Apply configuration
        app = App.get_running_app()
        config = self.app.config
        item = model.new_item(template=app.item_template)
        item['length'] = str(config.getdefault(
            SkipKeyApp.SETTINGS, SkipKeyApp.PWDLEN, 10))
        item['auto'] = str(config.getdefault(
            SkipKeyApp.PWDAUTO, SkipKeyApp.PWDLEN, True))

        self.manager.get_screen(EDIT).set_item(item=item, is_new=True)
        self.manager.transition.direction = 'left'
        self.manager.current = EDIT
        return True

    def cmd_back(self, after=False):
        """Return to login: stop the running mode and return
        to login screen. Warns the user that everything is cleared and
        data are going to be lost."""
        app = App.get_running_app()
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
                         fn_ok=self.cmd_back, ok_kwargs={'after': True})
            else:
                self.cmd_back(app=app, after=True)
        return False

    def cmd_save(self):
        """Save the current file"""
        try:
            app = App.get_running_app()
            if app.file:
                app.save(app.file)
            else:
                raise Exception(_('No file is opened'))
        except Exception as e:
            message(_('Error'), _('Save file error:\n%s') % (e), 'e')
            return False
        return True

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
    pr_tabbedb_wid = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(EditScreen, self).__init__(**kwargs)
        # Item currently edit
        self.item = None
        self.guic = GuiController(self)
        self.is_new = False

    def set_item(self, item, is_new):
        """Initialise screen fields from a dictionary."""
        self.item = item
        self.is_new = is_new
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

    def cmd_back(self):
        """Discard all changes, return to list screen."""
        self.manager.transition.direction = 'right'
        self.manager.current = LIST
        return True

    def cmd_delete(self, schedule=False):
        """Delete this account, return to list screen."""
        if schedule:
            try:
                App.get_running_app().delete_item(self.item)
                self.manager.transition.direction = 'right'
                self.manager.current = LIST
            except Exception as e:
                message(title=_('Delete Item Error'), text=e, type='e')
        else:
            Clock.schedule_once(lambda dt: self.cmd_delete(schedule=True), 0)

    def cmd_save(self):
        """Save this account, return to list screen."""
        app = App.get_running_app()
        tag = self.pr_tag.text
        if tag == TAGS:
            tag = ''
        auto = self.item['auto'] == 'True'
        # Password generation mode
        if self.pr_tabbedb_wid.current_tab is self.pr_tabbedb_wid.tab_list[1] \
                and self.pr_auto_wid.changed():
            auto = True
            self.pr_user_wid.pr_password.text = ''
            self.pr_user_wid.pr_confirm.text = ''
        # User mode
        if self.pr_tabbedb_wid.current_tab is self.pr_tabbedb_wid.tab_list[0] \
                and self.pr_user_wid.changed():
            auto = False
            self.pr_auto_wid.pr_length.text = ''
            self.pr_auto_wid.pr_symbols.text = ''
            self.pr_auto_wid.pr_numbers.text = ''
            self.pr_auto_wid.pr_letters.active = False
            try:
                self.pr_cipherpwd.text = app.encrypt(
                    self.pr_user_wid.pr_password.text)
            except Exception as e:
                message(title=_('Password Error'), text=e.args[0], type='e')
                return False
        else:
            # No pasword changed
            pass

        item = model.new_item(template=app.item_template,
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
                              history=self.item['history'])
        if not self.item_check(item):
            return False
        if self.item == item:
            message(_('Info'), _('No changes.'), 'i')
            return True
        # If the item is a new one from the add check name is not in items
        if self.is_new and model.contains(items=app.items, value=item['name'], key='name'):
            message(title=_('Duplicate key'), text=_(
                '"%s" exists. Choose another name' % (item['name'])), type='e')
            return False

        # if app.save_item(item):
        #     self.manager.transition.direction = 'right'
        #     self.manager.current = LIST
#
        try:
            Clock.schedule_once(lambda dt: app.save_item(item=item), 0)
            self.manager.transition.direction = 'right'
            self.manager.current = LIST
        except Exception as e:
            message(_('Save item'), _('Exception: %s') % (str(*e.args)), 'e')
#
        return True

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

    # def cmd_selectiontag(self, spinner):
    #     """Nothing to do here."""
    #     return True

    def cmd_renametag(self, instance, spinner):
        """Rename the current tag and updates all items accordingly
        to the renamed tag. """
        popup = EditTagPopup()
        popup.title = ': '.join((instance.text, spinner.text))
        popup.openRename(value=spinner.text)

    def cmd_deletetag(self, instance, spinner):
        """Delete the current tag and deletes the items tag accordingly."""
        popup = EditTagPopup()
        popup.title = ': '.join((instance.text, spinner.text))
        popup.openDelete(value=spinner.text)

    def cmd_addtag(self, instance, spinner):
        """Add a tag."""
        popup = EditTagPopup()
        popup.title = ': '.join((instance.text, ))
        popup.openAdd(value='')


class ImportScreen(Screen):
    """
    GUI element. Screen enabling the import of a '.csv' password file
    into the current one."""
    # pr_mapping = ObjectProperty(None)

    class MappingList(ItemList):
        def __init__(self, *args, **kwargs):
            super(ImportScreen.MappingList, self).__init__(**kwargs)

    def __init__(self, **kwargs):
        super(ImportScreen, self).__init__(**kwargs)
        self.file = None
        self.initialized = False
        self.guic = GuiController(self)
        self.mapping = {
            'name': 'name',
            'url': 'url',
            'login': 'login',
            'email': 'email',
            'password': 'password',
            'tag': '',
            'description': '',
            'created': '',
            'changed': '',
        }
        #  'color': '',
    #     'history': ''
    # }

        self.mapping_list = ImportScreen.MappingList()
        container = self.ids['_grid_container']
        container.add_widget(self.mapping_list)

    def on_enter(self, **kwargs):
        """Load a template for mapping the column headers of the input
        file to the headers of the current file."""
        super(ImportScreen, self).on_enter(**kwargs)
        text = ',\n'.join(
            [f"('{i}', '{j}')" for i, j in self.mapping.items()])
        if not self.initialized:
            for k, v in self.mapping.items():
                item = self.mapping_list.add(
                    item_class=ItemComposite, target=k)
                source = TextInput()
                source.text = v
                item.add(source)
            self.initialized = True

    def cmd_back(self):
        """Go back to the list screen without doing anything."""
        app = App.get_running_app()
        app.root.transition.direction = 'right'
        app.root.current = LIST

    def cmd_import(self):
        """Import the '.csv' into current file. Once the mapping is applied,
        new accounts are formed and appended to the current list.
        New records are normalized by adding calculated values in place of missing
        information. Nevertheless errors may occurs."""
        app = App.get_running_app()
        try:
            mapping = {i.cells[list(i.cells)[0]].text: i.cells[list(
                i.cells)[1]].text for i in self.mapping_list.items}

            items = model.import_csv(
                file=self.file, delimiter='\t', mapping=mapping)
            # Add default keys
            items_ = []
            for item in items:
                item = model.new_item(template=app.item_template, **item)
                item['password'] = app.encrypt(item['password'])
                item['auto'] = 'False'
                model.normalize(item)
                items_.append(item)
        except Exception as e:
            message(_('Error'), _(
                'Check the syntax:\n%s') % (str(*e.args)), 'w')
            return False
        if len(items_) > 0:
            # Check and manage double input!
            duplicated = imported = 0
            for item in items_:
                if model.contains(app.items, item['name'], 'name'):
                    item['tag'] = _('Import error')
                    item['name'] = '_'.join([item['name'], str(id(item))])
                    duplicated += 1
                else:
                    imported += 1
                app.save_item(item, history=True)
            app.root.transition.direction = 'right'
            app.root.current = LIST
            message(title=_('Import report'),
                    text=_('Imported items: %d \n -New items: %d \n -Duplicated items: %d') % (
                        imported + duplicated, imported, duplicated),
                    type='i' if duplicated == 0 else 'w')
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

    def _fill_fields(self, history):
        """
        Fetch changes from the app history.
        # Parameters
        -----------
        - history: list of changes. 
        """
        self.pr_changed_item_list_wid.clear()
        try:
            # Doesn't work with deleted records
            former = history[self.pr_actions.values.index(
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

    def cmd_back(self):
        """Return to list, discard all changes."""
        self.manager.transition.direction = 'right'
        self.manager.current = LIST
        return True

    def cmd_undo(self, *args):
        """Set the original item and discard the last changed one,
        deletes it from history. Undo of Undo is, at present, impossible."""
        try:
            pos = self.pr_actions.values.index(self.pr_actions.text)
            item = self.app.history[pos]['body']
            # del self.app.history[pos]
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

    def generate(self, **kwargs):
        # app, length, letters, numbers, symbols
        app = App.get_running_app()
        try:
            pwd, salt = app.generate(**kwargs)
            # Update strenght
            edit_screen = app.root.get_screen(EDIT)
            self.pr_password.text = pwd
            self.pr_strenght.set_strength(pwd)
            # Put in the ciphered
            edit_screen.pr_cipherpwd.text = str(
                base64.b64encode(salt), encoding='utf-8')
        except ValueError as e:
            message(_('Password'), *e.args, 'e')


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

        It evaluates the password strength.
        """
        self.pr_strenght.value = password.strength(text)


class AccountItemList(ItemList):
    """
    GUI element. Accounts list container.
    The list is managed in EditScreen.
    """
    columns = {'name': dp(200),
               'login': dp(180),
               'url': dp(200),
               'elapsed': dp(180),
               'warning': dp(180)}

    def __init__(self, *args, **kwargs):
        super(AccountItemList, self).__init__(
            cols=AccountItemList.columns, **kwargs)
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
    # Menu options:
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

    def cmd_url(self):
        # System call to browser
        app = App.get_running_app()
        item = app.items[model.index_of(
            items=app.items, value=self.item.kwparams['name'], key='name')]
        url = item['url']
        try:
            browser.open(url, new=0, autoraise=True)
        except Exception as e:
            self._publish(app, url)

        return True

    def cmd_user(self):
        """
        Publish user.
        """
        app = App.get_running_app()
        item = app.items[model.index_of(
            items=app.items, value=self.item.kwparams['name'], key='name')]
        user = item['login']
        self._publish(app, user)
        return True

    def cmd_password(self):
        """
        Publish password.
        """
        app = App.get_running_app()
        p = self._password(app)
        self._publish(app, p)
        return True

    def cmd_login(self):
        """
        Publish 'user TAB password' and dismiss bubble.
        """
        app = App.get_running_app()
        item = app.items[model.index_of(
            items=app.items, value=self.item.kwparams['name'], key='name')]
        p = self._password(app)
        login = f'{item["login"]}\t{p}'
        self._publish(app, login)
        self.reset()
        return True

    def _password(self, app):
        try:
            item = app.items[model.index_of(
                items=app.items, value=self.item.kwparams['name'], key='name')]
            if item['auto'] == 'False':
                p = app.decrypt(item['password'])
            # Clipboard.copy(self.item.item['login'])
            else:
                p = app.show(item)
            return p
        except Exception as e:
            message(title=_('Password Error'), text=e.args[0], type='e')

    def _publish(self, app, text):
        autocompletion = app.config.getdefault(
            SkipKeyApp.SETTINGS, SkipKeyApp.AUTOCOMP, True) == '1'
        pwd_timeout = int(app.config.getdefault(
            SkipKeyApp.SETTINGS, SkipKeyApp.PWDTIME, '15'))
        if text == False:
            return False
        if autocompletion:
            daemon = TypewriteThread(text=text, timeout=pwd_timeout)
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
    def cmd_edit(self):
        """
        Edit the account item. 
        Leave the screen and enter 'EditScreen'.
        """
        app = App.get_running_app()
        item = app.items[model.index_of(
            items=app.items, value=self.item.kwparams['name'], key='name')]
        app.root.get_screen(EDIT).set_item(item=item, is_new=False)
        app.root.transition.direction = 'left'
        app.root.current = EDIT
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


class SkipKeyApp(App, model.SkipKey):
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

    def __init__(self, *args, **kwargs):
        App.__init__(self, *args, **kwargs)
        model.SkipKey.__init__(self, *args, **kwargs)

        # App timeout
        self.MAXF = 10
        self.files = dict()
        # App timeout Clock-event - interface or App?
        self.evt_timeout = None
        # Clipboard timeout Clock-event - App
        self.evt_clipboard = None
        # - inteface or App?
        self.count_down = 0

    # App
    def build(self):
        self.title = 'SkipKey %s' % (__version__)
        # path = os.path.dirname(os.path.realpath(__file__))
        self.icon = '%s\\%s' % (icons_dir, ICON)
        # ----------------> App configuration
        sm = ScreenManager()
        self.root = sm

        # kivy.core.window.Window.clearcolor = (1, 0, 0, 1)

        sm.add_widget(EnterScreen(name=ENTER))
        sm.add_widget(ListScreen(name=LIST))
        sm.add_widget(EditScreen(name=EDIT))
        sm.add_widget(ImportScreen(name=IMPORT))
        sm.add_widget(ChangesScreen(name=CHANGES))
        # look&feel manager
        self.guic = GuiController(sm)
        return sm

    # App & interface
    def build_settings(self, settings):
        """Build settings from a JSON file / data first.
        """
        # JSON template is needed ONLY to create the panel
        path = os.path.dirname(os.path.realpath(__file__))
        with open(f'{path}\settings.json') as f:
            s = json.dumps(eval(f.read()))
        settings.add_json_panel(SkipKeyApp.SETTINGS, self.config, data=s)

    # App
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

    # App
    def on_start(self):
        """
        Event handler for the on_start event which is fired after initialization
        (after build() has been called) but before the application has started running."""
        # Init screens:
        return super().on_start()

    # App
    def on_pause(self):
        """
        Event handler called when Pause mode is requested. You should return
        True if your app can go into Pause mode, otherwise return False and your
        application will be stopped."""
        return super().on_pause()

    # App
    def on_resume(self):
        """
        Event handler called when your application is resuming from the Pause mode."""
        return super().on_resume()

    # App
    def on_stop(self):
        """
        Event handler for the on_stop event which is fired when the application
        has finished running (i.e. the window is about to be closed)."""
        self.save(file=self.file)
        return super().on_stop()

    # App
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

    # App
    def clear_recent_files(self):
        """
        Clear the list of recently opened files"""
        for i in range(self.MAXF):
            self.config.set(SkipKeyApp.RECENT_FILES, f'_{i}', '')
        self.config.write()
        return True

    # App
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

    # App
    def timeout(self, after=False):
        """Security timeout"""
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

    # interface
    def open(self, file, passwd, seed):
        """
        Open the file and prepare the records. Raises excepions."""
        self.update_recent_files(file)
        return super().open(file, passwd, seed)

    # interface
    def delete_item(self, item):
        """
        Delete an item from the item list.
        """
        return super().delete_item(item)

    # interface
    def save_item(self, item, history=True):
        """
        Add a new item or update an existing one.
        """
        return super().save_item(item, history)

    # interface
    def add_history(self, new, old, action=''):
        """
        Add an object to the history of changes
        """
        return super().add_history(new, old, action)

    # interface
    def encrypt(self, text):
        """
        Encrypt a text using the security algorithm and seed.
        """
        return super().encrypt(text)

    # interface
    def decrypt(self, text):
        """
        Decrypt a text using the security algorithm and seed.
        """
        return super().decrypt(text)

    # interface
    def generate(self, length, letters, numbers, symbols):
        """
        Generate a password.
        """
        return super().generate(length, letters, numbers, symbols)

    # interface

    def show(self, item):
        """
        Show a generated password.
        """
        return super().show(item)

    # interface
    def secure(self, cryptod, passwd, seed):
        """
        Turn the security on (call once)."""
        self.timeout()
        return super().secure(cryptod, passwd, seed)

    # interface
    def unsecure(self):
        """Turn the security off."""
        return model.SkipKey.unsecure(self)

    # interface TODO decouple this method from view App
    def initialize(self):
        """Initializes app context"""
        # Stop count down
        if self.evt_timeout:
            self.evt_timeout.cancel()
        return super().initialize()

    # interface
    def save(self, file, force=False):
        """
        Save items into a file.
        """
        return super().save(file, force)

    # interface
    def copy(self, file, cryptod, passwd, seed, thread=False):
        """
        Save items into a file with new password and random seed.
        """
        self.update_recent_files(file)
        return super().copy(file, cryptod, passwd, seed, thread)

    # interface
    def export(self, file):
        return super().export(file)


if __name__ == '__main__':
    search_fields = ('name',
                     'tag',
                     'description',
                     'login',
                     'url',
                     'email')

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

    SkipKeyApp(search_fields=search_fields, item_template=item_template).run()
