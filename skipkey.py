"""SkipKey: a help to password management.
"""
import base64
import json
from logging import raiseExceptions
import re
import os
import sys
# Third parties modules
import webbrowser as browser
import kivy
#
from kivy.core.clipboard import Clipboard
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivy.properties import ObjectProperty
from kivy.lang.builder import Builder
from kivy.uix.spinner import Spinner
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.app import App
from kivy.uix.behaviors.focus import FocusBehavior
#----------------------------
import commons
#----------------------------
from typewritethread import TypewriteThread
from filemanager import OpenFilePopup, SaveFilePopup
import cipherfachade
# import password
import model
from localize import translate
from uicontroller import GuiController
from bubblemenu import Menu, BubbleBehavior
from mlist import SelectableList, ItemComposite, Selectable, ItemPart
import kvgraphics as ui
import password
from dropdownmenu import DropDownMenu
#
# dummy = os.path.dirname(os.path.realpath(__file__))
# sys.path.append(dummy)

# =============================================================================
# Kivy config
# =============================================================================
kivy.require('1.11.0')  # Current kivy version

MAJOR = 1
MINOR = 2
MICRO = 4
RELEASE = True
__version__ = '%d.%d.%d' % (MAJOR, MINOR, MICRO)


# kivy.resources.resource_add_path(current_dir)

# Screen Names
ENTER = 'Enter'
LIST = 'List'
EDIT = 'Edit'
CHANGES = 'changes'
IMPORT = 'import'
# App
ICON = 'skip.png'
TAGS = ('...')  # Default for all tags

current_dir = commons.current_dir
icons_dir = commons.icons_dir
locale_dir = commons.locale_dir
kivy_dir = commons.kivy_dir
message = commons.message
decision = commons.decision
_ = commons._

# _ = translate(domain='skipkey', localedir=locale_dir, languages=['it'])


def hh_mm_ss(seconds):
    """
    Converts seconds into hh:mm:ss padded with zeros.
    """
    hh = int(seconds/3600)
    mm = int((seconds % 3600)/60)
    ss = int((seconds % 3600) % 60)
    out = '{hh:02}:{mm:02}:{ss:02}'.format(hh=hh, mm=mm, ss=ss)
    return out

# Import of local modules from import directive in .kv
# files works only if module is in the app dir!!
# Builder.load_file(os.path.join('kv', 'userpanel.kv'))
# Builder.load_file(os.path.join('kv', 'autopanel.kv'))

#Popups
commons.import_kivy_rule(os.path.join('kv', 'loginpopup.kv'))
commons.import_kivy_rule(os.path.join('kv', 'cipherpopup.kv'))
commons.import_kivy_rule(os.path.join('kv', 'edittagpopup.kv'))
commons.import_kivy_rule(os.path.join('kv', 'infopopup.kv'))

#Panels building blocks
commons.import_kivy_rule(os.path.join('kv', 'loginpanel.kv'))
commons.import_kivy_rule(os.path.join('kv', 'seedpanel.kv'))
commons.import_kivy_rule(os.path.join('kv', 'itemmenu.kv'))

#Screens
commons.import_kivy_rule(os.path.join('kv', 'enterscreen.kv'))
commons.import_kivy_rule(os.path.join('kv', 'listscreen.kv'))
commons.import_kivy_rule(os.path.join('kv', 'editscreen.kv'))
commons.import_kivy_rule(os.path.join('kv', 'importscreen.kv'))
commons.import_kivy_rule(os.path.join('kv', 'changesscreen.kv'))
#Widgets
# commons.import_kivy_rule(os.path.join('kv', 'passwordstrenght.kv'))
commons.import_kivy_rule(os.path.join('kv', 'tagspinner.kv'))
commons.import_kivy_rule(os.path.join('kv', 'percentprogressbar.kv'))
commons.import_kivy_rule(os.path.join('kv', 'changeview.kv'))


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
        Export the current file to '.csv' password file.
        It calls 'SkipKeyApp.export()'.
        """
        f = file
        if isinstance(file, list):
            f = file[0]
        try:
            log = App.get_running_app().export(file=f)
            if log:
                message(_('Export warning'), '\n'.join(log) , 'w')
            else:
                message(_('Export successful'), f'{os.path.basename(file)}', 'i')
                self.dismiss()
            return True
        except Exception as e:
            message(_('Export failed: %s') % (f'{os.path.basename(file)}'),e, 'e')
        return False


class LoginPopup(FocusBehavior, Popup):
    """"
    GUI element. Login popup to decipher and set the random key.
    """
    # Widget hooks
    login_wid = ObjectProperty(None)
    seed_wid = ObjectProperty(None)

    def __init__(self, title='', *args, **kwargs):
        super(LoginPopup, self).__init__(**kwargs)
        # Current file
        self.file = None
        self.title = title

    def cmd_enter(self):
        """Button callback: enter the 'ListScreen'.
        Preconditions: enter decipher password and casual seed."""
        app = App.get_running_app()
        if self.login_wid.password.text and self.seed_wid.seed.text:
            # Check login successful (file opened) and check the key set
            if isinstance(self.file, list):
                self.file = self.file[0]
            if not os.path.exists(self.file):
                message(
                    f'{self.title}', _('The file %s does not exists') % (os.path.basename(self.file)), 'e')
                return False
            p = bytes(self.login_wid.password.text, encoding='utf-8')
            s = bytes(self.seed_wid.seed.text, encoding='utf-8')

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
        self.login_wid.password.text = ''
        # self.login.confirm.text = ''
        self.seed_wid.seed.text = ''


class CipherPopup(Popup):
    """
    GUI element. Cipher file popup enable user to choose a password and
    a casual seed, and an algorithm for encrypring the file and generating
    the casual secret key from the seed.
    """
    # Widget hooks
    login_wid = ObjectProperty(None)
    seed_wid = ObjectProperty(None)
    kderive = ObjectProperty(None)
    cipher = ObjectProperty(None)
    iters = ObjectProperty(None)

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
        if self.login_wid.password.text and self.seed_wid.seed.text:
            # Check login was successful (file opened) and check the key was set
            if isinstance(self.file, list):
                self.file = self.file[0]
            # Build security:
            if self.kderive.text and self.cipher.text and self.iters.text:

                params = cipherfachade.get_cryptografy_parameters(
                    algorithm=self.cipher.text,
                    pbkdf=self.kderive.text,
                    iterations=int(self.iters.text))

                p = bytes(self.login_wid.password.text, encoding='utf-8')
                s = bytes(self.seed_wid.seed.text, encoding='utf-8')
                self.action(cryptod=params, passwd=p, seed=s)
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
        return list(cipherfachade.cipher_algorithms().keys())

    def key_derivators(self):
        """Returns the list of available key derivation functions."""
        return list(cipherfachade.key_derivators().keys())

    def reset(self):
        """Clear user input."""
        self.login_wid.password.text = ''
        self.login_wid.confirm.text = ''
        self.seed_wid.seed.text = ''


class InfoPopup(Popup):
    """
    GUI element. Popup to display information about current file and
    security settings."""
    # Properties: Login and seed
    keyderive = ObjectProperty(None)
    algorithm = ObjectProperty(None)
    mode = ObjectProperty(None)
    keysize = ObjectProperty(None)
    iterations = ObjectProperty(None)
    file = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(InfoPopup, self).__init__(**kwargs)
        self.guic = GuiController(self)
        pass

    def set_fields(self, cryptod, **kwargs):
        """Set the value of widget fields."""
        try:
            self.file.text = kwargs['file']
            self.algorithm.text = cryptod['algorithm']
            self.mode.text = cryptod['mode']
            self.keysize.text = str(cryptod['keysize'])
            self.pbkdf.text = cryptod['pbkdf']
            self.iterations.text = str(cryptod['iterations'])
        except KeyError:
            self.algorithm.text = ''
            self.mode.text = ''
            self.keysize.text = ''
            self.keyderive.text = ''
            self.iterations.text = ''


class EditTagPopup(Popup):
    """
    GUI element. Tag management popup. Tag can be added, deleted and renamed.
    When renamed: all item list entry tag is replaced with the renamed one.
    When deleted: all items with the deleted tag are cleared."""
    # Widget hooks
    tag = ObjectProperty(None)

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
        self.tag.text = value
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
        tag = self.tag.text

        if tag == _(TAGS):
            message(tag, _('Action failed because: %s is already used.') %
                    (tag), 'w')
            return False
        # Delete = tag is ''
        if self.mode == -1 and self.value:
            tag = ''
        # Add a new tag
        elif self.mode == 1 and self.value == '':
            if model.contains(items=app.items,
                              value=tag, key='tag', casefold=True):
                message(tag,
                        ('Action failed because: %s is already used.') % (tag),
                       'w')
                return False
        # Rename a tag
        elif self.mode == 0:  # and self.value:
            pass
        else:
            return False

        app.root.get_screen(EDIT).tag.text = tag
        #
        for item in model.iterator(items=app.items, key='tag', value=self.value):
            item_old = item.copy()
            item['tag'] = tag
            app.add_history(new=item, old=item_old, action='update')
        return self.cmd_cancel(None)


class EnterScreen(Screen):
    """GUI element. App enter screen."""
    recentfiles = ObjectProperty(None)

    def __init__(self, *args, **kwargs):
        super(EnterScreen, self).__init__(**kwargs)
        self.app = None

    def on_enter(self):
        """Load recent files."""
        self.app = App.get_running_app()
        self.recentfiles.values = self.app.get_recent_files()

    def cmd_recent(self):
        """Choose a recent file and call login screen."""
        if self.recentfiles.text == 'Recent files':
            return False
        file = self.recentfiles.text
        if file and file in self.app.files:
            self.recentfiles.text = 'Recent files'
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
        self.recentfiles.values = self.app.get_recent_files()
        return True

    def cmd_exit(self):
        """Exit the app doing nothing. """
        self.app.stop()
        # sys.exit()
        return True


class ListScreen(Screen):
    """GUI element. Main screen with the list of user accounts."""
    # Widget hooks
    tag = ObjectProperty(None)
    search = ObjectProperty(None)
    expiring = ObjectProperty(None)
    account_list = ObjectProperty(None)

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
        if self.tag.disabled:
            self.tag.disabled = False
            self.search.disabled = False
        tags = self.build_tags()
        self.tag.values = tags
        self.app.root.get_screen(EDIT).tag.values = tags

        if not self.tag.text:
            self.tag.text = self.tag.values[0]
        elif self.tag.text != self.tag.values[0]:
            self.cmd_tag_selected()
        elif self.search.text:
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
            if not self.tag.disabled:
                self.tag.disabled = True
                self.search.disabled = True
            pwd_warn = float(self.app.config.getdefault(
                SkipKeyApp.SETTINGS, SkipKeyApp.PWDWARN, 7))
            pwd_lifetime = float(self.app.config.getdefault(
                SkipKeyApp.SETTINGS, SkipKeyApp.PWDLIFETIME, 6)) * 30.45
            data = []
            for i in self.app.items:
                try:
                    if model.time_left(i, pwd_lifetime) <= pwd_warn:
                        data.append(i)
                except Exception:
                    continue
            
            self.account_list.clear()

            for item in data:
                id = item.get('object_id', None)
                if id:
                    self.account_list.add_from_cache(id).refresh_view_attrs(item)
                else:
                    row = AccountAdapter()
                    row.refresh_view_attrs(item)
                    item.setdefault('object_id', self.account_list.add(row))

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
        tags = [TAGS, ]
        if self.app.items:
            t = list(set(i['tag'] for i in self.app.items))
            t.sort(key=str.lower)
            tags = tags + t

        return tags

    def _fill_items(self, items):
        """
        Internal. Fill the item list.

        Every item is an account.
        """
        self.account_list.clear()

        for item in items:
            id = item.get('object_id', None)
            if id:
                self.account_list.add_from_cache(id).refresh_view_attrs(item)
            else:
                row = AccountAdapter()
                row.refresh_view_attrs(item)
                item.setdefault('object_id', self.account_list.add(row))

        self.counter()

    def counter(self):
        """Return the number of displayed item accounts over the total item."""
        # self.ids['_lab_counter'].text = f'{len(self.account_list.children)} / {len(self.app.items)}'
        self.ids['_lab_account'].text = ('%s: %d') % (_('Personal accounts'), len(self.app.items))
        self.ids['_lab_counter'].text = f'{len(self.account_list.children)}'

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
        # app = App.get_running_app()
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
        if self.search.text:
            self.search.text = ''

        if after:
            if self.tag.text == TAGS:
                self._fill_items(self.app.items)
            else:
                sublst = model.select(
                    items=self.app.items, value=self.tag.text, key='tag')
                # sublst.sort(key=lambda x: str.lower(x['name']))
                self._fill_items(sublst)
            self.counter()
            return True
        else:
            Clock.schedule_once(
                lambda dt: self.cmd_tag_selected(after=True), 0.1)

    def clear_search(self):
        """Clear the search text field."""
        if len(self.search.text) > 0:
            self.search.text = ''
        self._fill_items(self.app.items)

    def cmd_search(self, after=False, at_least=1):
        """
        Search items from the field input text.

        For performance reasons it's better search for sublist.
        """
        if after:
            data = self.account_list.children
            if len(self.find.sublist) != len(data):
                self._fill_items(self.find.sublist)
                self.counter()
        else:
            # Start search from at least two characters
            if len(self.search.text) > at_least:
                # Search text: add characters -> search on sublist
                if self.find.pattern and str(self.search.text).casefold().startswith(str(self.find.pattern).casefold()):
                    sublist = model.search(
                        items=self.find.sublist, text=self.search.text)
                    # sublist.sort(key=lambda x: str.lower(x['name']))
                    self.find = ListScreen.Find(self.search.text, sublist)
                else:
                    sublist = model.search(
                        items=self.app.items, text=self.search.text)
                    self.find = ListScreen.Find(self.search.text, sublist)
            else:
                self.find = ListScreen.Find(
                    self.search.text, self.app.items)

            Clock.schedule_once(lambda dt: self.cmd_search(after=True), 0.1)
        return True

    def cmd_add(self):
        """Add a new item account. Call 'EditScreen'."""
        # Apply configuration
        app = App.get_running_app()
        config = self.app.config
        item = model.new_item()
        item['length'] = str(config.getdefault(
            SkipKeyApp.SETTINGS, SkipKeyApp.PWDLEN, 10))
        item['auto'] = str(config.getdefault(
            SkipKeyApp.PWDAUTO, SkipKeyApp.PWDLEN, True))

        self.manager.get_screen(EDIT).set_view_attrs(item=item, is_new=True)
        self.manager.transition.direction = 'left'
        self.manager.current = EDIT
        return True

    def cmd_back(self, after=False):
        """Return to login: stop the running mode and return
        to login screen. Warns the user that everything is cleared and
        data are going to be lost."""
        app = App.get_running_app()
        if after:
            self.account_list.clear()
            # self.account_list.layout_manager.clear_selection()
            self.tag.text = ''
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


class EditScreen(FocusBehavior, Screen):
    """GUI element. Account editing screen."""
    aname = ObjectProperty(None)
    tag = ObjectProperty(None)
    url = ObjectProperty(None)
    login = ObjectProperty(None)
    email = ObjectProperty(None)
    description = ObjectProperty(None)
    color = ObjectProperty(None)
    created = ObjectProperty(None)
    changed = ObjectProperty(None)
    secret_0 = ObjectProperty(None)
    secret_1 = ObjectProperty(None)
    secret_2 = ObjectProperty(None)


    def __init__(self, **kwargs):
        super(EditScreen, self).__init__(**kwargs)
        # Item currently edit
        self.item = None
        self.guic = GuiController(self)
        self.is_new = False

    def set_view_attrs(self, item, is_new):
        """Initialise screen fields from a dictionary."""
        self.item = item
        self.is_new = is_new

        self.aname.text = item['name']
        self.login.text = item['login']
        self.url.text = item['url']
        self.email.text = item['email']
        self.description.text = item['description']
        self.tag.text = item['tag']
        self.color.text = item['color']
        self.created.text = item['created']
        self.changed.text = item['changed']
        self.history = item['history']
        self.secret_0.set_view_attrs(item.get('secrets', [{}, {}, {}])[0])
        self.secret_1.set_view_attrs(item.get('secrets', [{}, {}, {}])[1])
        self.secret_2.set_view_attrs(item.get('secrets', [{}, {}, {}])[2])


    def get_view_attrs(self):
        """Returns screen fields from a dictionary."""
        app = App.get_running_app()
        item = model.new_item()
        item.update({
            'name': self.aname.text,
            'login': self.login.text,
            'url': self.url.text,
            'email': self.email.text,
            'description': self.description.text,
            'tag': '' if self.tag.text == TAGS else self.tag.text,
            'color': self.color.text,
            'created': self.created.text,
            'changed': self.changed.text,
            'history': self.history
        })
        secrets = [
            self.secret_0.get_view_attrs(),
            self.secret_1.get_view_attrs(),
            self.secret_2.get_view_attrs(),
        ]
        item['secrets'] = secrets
        return item


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
        item = self.get_view_attrs()

        if not self.item_check(item):
            return False
        # If the item is a new one from the add check name is not in items
        if self.is_new and model.contains(items=app.items, value=item['name'], key='name'):
            message(title=_('Duplicate key'), text=_(
                '"%s" exists. Choose another name') % (item['name']), type='e')
            return False
        try:
            # Clock.schedule_once(lambda dt: app.save_item(item=item), 0)
            app.save_item(item=item)
            self.manager.transition.direction = 'right'
            self.manager.current = LIST
        except Exception as e:
            message(_('Save item'), _('Exception: %s') % (str(*e.args)), 'e')
        return True

    def item_check(self, item):
        """Check mandatory fields before saving the account item."""
        log = []
        # Check for changes
        if model.is_equal(item, self.item):
            message(_('Info'), _('No changes.'), 'i')
            return False
        # Check for password
        if all(s['password'] == '' for s in item['secrets']):
            log.append(_('No password defined'))
        # Check for key
        if item['name'] == '':
            log.append(_('Name is mandatory'))
        # Check for email
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

class MappingList(SelectableList):
    def __init__(self, *args, **kwargs):
        super(MappingList, self).__init__(**kwargs)

class ImportScreen(Screen):
    """
    GUI element. Screen enabling the import of a '.csv' password file
    into the current one."""
    # mapping = ObjectProperty(None)

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
            'tag': 'tag',
            'description': 'description',
            'created': 'created',
            'changed': 'changed',
            'password_0': 'password_0',
            'password_1': '',
            'password_2': '',
        }

        self.mapping_list = self.ids['_mapping_list']

    def on_enter(self, **kwargs):
        """Load a template for mapping the column headers of the input
        file to the headers of the current file."""
        super(ImportScreen, self).on_enter(**kwargs)
        if not self.initialized:
            for k, v in self.mapping.items():
                # item = ItemComposite(items={'target': k})
                item = ItemComposite(height=ui.field_y, size_hint=(1, None))
                item.add('target', Label(text=k))
                item.add('source', TextInput(text=v))
                self.mapping_list.add(item)
            self.initialized = True

    def cmd_back(self):
        """Go back to the list screen without doing anything."""
        app = App.get_running_app()
        app.root.transition.direction = 'right'
        app.root.current = LIST

    def cmd_import(self):
        """Import the '.csv' into current file. Once the mapping is applied,
        new accounts are formed and appended to the current list.
        New records are normalized by adding calculated values in place of
        missing information. Nevertheless errors may occurs."""
        app = App.get_running_app()
        mapping = {i.items['target'].text: i.items['source'].text for i in self.mapping_list.children}

        try:
            items_ = app.import_csv(file=self.file, mapping=mapping)
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
    actions = ObjectProperty(None)
    changed_item_list = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(ChangesScreen, self).__init__(**kwargs)
        self.app = App.get_running_app()
        self.guic = GuiController(self)

    def _fill_fields(self, history):
        """
        Fetch changes from the app history.

        -----------
        Parameters

        - history: list of changes. 
        """
        # Doesn't work with deleted records
        self.changed_item_list.clear()

        try:
            old = model.state_object(
                history[self.actions.values.index(self.actions.text)])
        except Exception:  # No changes
            return

        try:  # No records found it was deleted
            new = self.app.items[model.index_of(
                items=self.app.items, key='name', value=old['name'])]
        except Exception:
            new = old
        # Fill the table of changed values
        for key, value in old.items():
            if key == 'secrets':
                for i in range(0, len(value)):
                    old_pwd = old['secrets'][i]['password']
                    new_pwd = new['secrets'][i]['password']
                    label = new['secrets'][i]['label']
                    if old_pwd != new_pwd:
                        old_pwd = '********'
                        new_pwd = '*********'
                    elif old_pwd == new_pwd == '':
                        continue
                    else:
                        old_pwd = new_pwd = '********'
                    view = ChangeView(key=key, label=label+':', new=new_pwd, old=old_pwd)
                    self.changed_item_list.add(view)
            else:
                view = ChangeView(key=key, label=SkipKeyApp.LABELS.get(key, key)+':', new=new[key], old=value)
                if key in SkipKeyApp.LABELS:
                    self.changed_item_list.add(view)


    def on_enter(self):
        """Screen initialization."""
        if len(self.app.history) > 0:
            self.actions.values = ['{: <10s} - {: <10s} - {:s}'.format(
                m['name'], m['action'], m['timestamp'].isoformat(sep=' ', timespec='seconds')) for m in self.app.history]
            self.actions.text = self.actions.values[0]
            self._fill_fields(self.app.history)
        else:
            self.actions.values = [_('No changes'), ]
            self.actions.text = self.actions.values[0]

    def cmd_back(self):
        """Return to list, discard all changes."""
        self.manager.transition.direction = 'right'
        self.manager.current = LIST
        return True

    def cmd_undo(self, *args):
        """Set the original item and discard the last changed one,
        deletes it from history. Undo of Undo is, at present, not supported."""
        try:
            pos = self.actions.values.index(self.actions.text)
            if pos < len(self.app.history):
                state = self.app.history.pop(pos)
                item = model.state_object(state)  # ['body']
                if state['action'] == model.SkipKey.APPEND:
                    self.app.delete_item(item, history=False)
                else:
                    self.app.save_item(item, history=False)  # no history
            else:
                pass  # Non changes in history
        except Exception as e:
            message(title=_('Undo'),
                    text=_('Revert action "%s" failed: %s') % (
                        self.actions.text, e.args[0]),
                    type='e')
        self.on_enter()

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
    password = ObjectProperty(None)
    strenght = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(LoginPanel, self).__init__(**kwargs)
        self.guic = GuiController(self)

    def cmd_text(self, text):
        """
        Callback for TextInput on_text event. 
        """
        self.strenght.set_strength(text)

    def changed(self):
        """
        Return if the pasword has been changed.
        """
        if self.password.text:
            return self.password.text != ''
        return False


class SeedPanel(BoxLayout):
    """
    GUI element. Panel for random seed input.

    It is used by LoginPopup, CipherPopup.
    """
    # Widget hooks
    seed = ObjectProperty(None)
    strenght = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(SeedPanel, self).__init__(**kwargs)
        self.guic = GuiController(self)

    def cmd_text(self, text):
        """
        Callback for TextInput on_text event.
        """
        self.strenght.set_strength(text)

    def changed(self):
        """
        Return True if the seed has been changed.
        """
        if self.seed.text:
            return self.seed.text != ''
        return False


class PercentProgressBar(BoxLayout):
    """
    Display a pecentage with a progress bar.

    -----------

    Parameters:
        percentage: the percentage.
    """
    id = StringProperty('')
    def __init__(self, **kwargs):
        super(PercentProgressBar, self).__init__(**kwargs)


class AccountAdapter(ItemComposite):
    def __init__(self, **kwargs):
        super(AccountAdapter, self).__init__(**kwargs)
        self.size_hint = (1, None)
        self.height = dp(50)
        parts = {
            'name': ItemPart(width=dp(180)),
            # 'login': ItemPart(width=dp(180)),
            'url': ItemPart(width=dp(200)),
            'tag': ItemPart(width=dp(100)),
            'elapsed': PercentProgressBar(width=dp(120)),
        }
        for key, widg in parts.items():
            self.add(key, widg)

        self.lifetime = float(App.get_running_app().config.getdefault(
            SkipKeyApp.SETTINGS, SkipKeyApp.PWDLIFETIME, 6)) * 30.45

    def refresh_view_attrs(self, item):
        ''' Catch and handle the view changes '''
        self.items['name'].text = item['name']
        # self.items['login'].text = item['login']
        self.items['url'].text = item['url']
        self.items['tag'].text = item['tag']
        elapsed = model.elapsed(item)
        elapsed = elapsed if elapsed < self.lifetime else self.lifetime
        elapsed = 100 * elapsed/self.lifetime
        self.items['elapsed'].ids.progressbar.value = elapsed


class AccountItemList(BubbleBehavior, SelectableList):
    """
    GUI element. Accounts list container.
    The list is managed in EditScreen.
    """

    def __init__(self, *args, **kwargs):
        super(AccountItemList, self).__init__(**kwargs)

        # Add the bubble menu
        self.add_bubble(ItemMenu())


class ChangeView(Selectable, BoxLayout):
    """
    Provides a comparison between an 'old' vs  a 'new' object,
    emphasizing changes of its content.

    -------------------
    Parameters:
    - label: label displayed in the item.
    - new: new content.
    - old: old content.
    """

    def __init__(self, **kwargs):
        super(ChangeView, self).__init__()
        self.ids.label.text = kwargs.get('label', '-')
        new = str(kwargs.get('new', '-'))
        old = str(kwargs.get('old', '-'))
        new = new if new else ' '
        old = old if old else ' '

        if new != old:
            new = '[b][color=FF0000]%s[/color][/b]' % (new)
            old = '[b][color=00FF00]%s[/color][/b]' % (old)

        self.ids.new.text = new
        self.ids.old.text = old


class ChangedItemList(SelectableList):
    """
    GUI element. Container of changed account items.
    The list is managed in ChangesScreen.
    """

    def __init__(self, *args, **kwargs):
        super(ChangedItemList, self).__init__(**kwargs)


class ItemMenu(Menu):
    """
    GUI element. Bubble context menu for a selected account item.

    -------------
        Menu options:

    - Get the account url.
    - Get the account user.
    - Get the account password.
    - Get the account login: 'user' [tab] 'password'.
    - Edit the account item: leave the screen and enter 'EditScreen'.
    """

    def __init__(self, **kwargs):
        super(ItemMenu, self).__init__(**kwargs)
        # Clear clipboard scheduled event
        self.evt_clipboard = None
        self.app = App.get_running_app()
        self.item = None

    def _set_widget(self, widg):
        Menu._set_widget(self, widg)
        index = model.index_of(items=self.app.items, value=self.name, key='name')
        if index != None:
            self.item = self.app.items[index]
            self._init_layout(self.ids.secret_0, 0)
            self._init_layout(self.ids.secret_1, 1)
            self._init_layout(self.ids.secret_2, 2)
            # self.ids.secret_0.text = self.item['secrets'][0].get('label', '')
            # self.ids.secret_0.disabled = self.item['secrets'][0].get('password', '') == ''
            # self.ids.secret_1.text = self.item['secrets'][1].get('label', '')
            # self.ids.secret_1.disabled = self.item['secrets'][1].get('password', '') == ''
            # self.ids.secret_2.text = self.item['secrets'][2].get('label', '')
            # self.ids.secret_2.disabled = self.item['secrets'][2].get('password', '') == ''
    
    def _init_layout(self, secret, index):
        secret.text = self.item['secrets'][index].get('label', '')
        disabled = self.item['secrets'][index].get('password', '') == ''
        secret.disabled = disabled
        if disabled:
            # secret.background_normal='data/transparent.png'
            secret.background_disabled_normal='data/transparent.png'


    @property
    def name(self):
        return self.widget.items['name'].text

    def cmd_url(self, *args):
        url = self.item['url']
        try:
            browser.open(url, new=0, autoraise=True)
        except Exception:
            self._publish(self.app, url)

        return True

    def cmd_user(self, *args):
        """
        Publish user.
        """
        user = self.item['login']
        self._publish(self.app, user)
        return True

    def cmd_password(self, *args):
        """
        Publish password.
        """
        # app = App.get_running_app()
        p = self._password(self.app, *args)
        self._publish(self.app, p)
        return True

    def cmd_login(self, *args):
        """
        Publish 'user TAB password' and dismiss bubble.
        """
        p = self._password(self.app, 0)
        login = ''.join((self.item["login"], '\t', p))
        self._publish(self.app, login)
        self.reset()
        return True

    def _password(self, app, *args):
        try:
            secret = self.item['secrets'][args[0]]
            if secret['auto'] == 'False':
                p = app.decrypt(secret['password'])
            else:
                p = app.show(secret)
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
        return True

    def cmd_edit(self, *args):
        """
        Edit the account item.
        Leave the screen and enter 'EditScreen'.
        """
        self.app.root.get_screen(EDIT).set_view_attrs(item=self.item, is_new=False)
        self.app.root.transition.direction = 'left'
        self.app.root.current = EDIT
        self.reset()
        return True

    def reset(self):
        # Free the selection to enable re-selection
        self.widg = None
        self.item = None
        self.parent.remove_widget(self)

    def on_touch_down(self, touch):
        """
        Remove bubble when click outside it.
        """
        if not self.collide_point(touch.x, touch.y):
            self.reset()
        return super(ItemMenu, self).on_touch_down(touch)


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
        #'color': _('Color'),  # Basic colors as string
        'created': _('Created'),  # Date
        'changed': _('Changed'),  # Date
        'auto': _('Auto'),  # True, False=user
        'length': _('Length'),  # Integer
        'letters': _('Letters'),  # True / False
        'numbers': _('Numbers'),  # At least [0 length]
        'symbols': _('Symbols'),  # At least [0 length]
        # User encrypted password or salt Base64 encoded
        'password': _('Cipher Data'),
        #'history': ''  # Record history - not yet managed
    }

    timer = StringProperty('')
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
        self.icon = os.path.join(icons_dir, ICON)
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
        # with open(f'{path}\settings.json') as f:
        with open(os.path.join(path, 'settings.json')) as f:
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
        Event handler for the on_start event which is fired after
        initialization (after build() has been called) but before
        the application has started running."""
        # Init screens:
        return super().on_start()

    # App
    def on_pause(self):
        """
        Event handler called when Pause mode is requested. You should return
        True if your app can go into Pause mode, otherwise return False and
        your application will be stopped."""
        return super().on_pause()

    # App
    def on_resume(self):
        """
        Event handler called when your application is resuming from the
        Pause mode."""
        return super().on_resume()

    # App
    def on_stop(self):
        """
        Event handler for the on_stop event which is fired when the
        application has finished running (i.e. the window is about
        to be closed).
        """
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
            self.timer = hh_mm_ss(self.count_down)
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
    def delete_item(self, item, history=True):
        """
        Delete an item from the item list.
        """
        return super().delete_item(item, history)

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
    def generate(self, **kwargs):
        """
        Generate a password.
        """
        return super().generate(**kwargs)

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

    SkipKeyApp(search_fields=search_fields).run()
