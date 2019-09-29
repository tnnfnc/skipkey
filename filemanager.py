"""SkipKey: file manager"""
import kivy
from kivy.lang.builder import Builder
from kivy.uix.popup import Popup
from kivy.properties import ObjectProperty
import os

kivy.require('1.11.0')  # Current kivy version

Builder.load_file('filemanager.kv')

class OpenFilePopup(Popup):
    # Widget hooks
    filechooser = ObjectProperty(None)

    def __init__(self, *args, **kwargs):
        super(OpenFilePopup, self).__init__(**kwargs)
        self.filechooser.rootpath = os.getcwd()
        self.filechooser.filters = [self.is_valid]
        self.filechooser.dirselect = False

    def cmd_load(self, path, selection):
        '''Call login to decipher file'''
        return False

    def cmd_cancel(self):
        self.dismiss()

    def is_valid(self, folder, file):
        return True

    def cmd_parentdir(self, button, state):
        # Enables going parent dir
        if state == 'down':
            button.text = os.getcwd()
            self.filechooser.rootpath = None
        else:
            button.text = _('..\\')
            self.filechooser.rootpath = os.getcwd()

class SaveFilePopup(Popup):
    # Widget hooks
    filechooser = ObjectProperty(None)

    def __init__(self, *args, **kwargs):
        super(SaveFilePopup, self).__init__(**kwargs)
        self.filechooser.rootpath = os.getcwd()
        # self.filechooser.filters = [self.is_valid]
        self.filechooser.dirselect = False

    def cmd_save(self, path, selection):
        if selection:
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
        pass

    def cmd_cancel(self):
        self.dismiss()

    def cmd_parentdir(self, button, state):
        # Enables going parent dir
        if state == 'down':
            button.text = os.getcwd()
            self.filechooser.rootpath = None
        else:
            button.text = _('..\\')
            self.filechooser.rootpath = os.getcwd()