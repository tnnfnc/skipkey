"""File manager"""
import kivy
from kivy.lang.builder import Builder
from kivy.uix.popup import Popup
from kivy.properties import ObjectProperty
from kivy import utils
import os

kivy.require('1.11.0')  # Current kivy version


message_popup = None
decision_popup = None


def message(title, text, type='i'):
    global message_popup
    if not message_popup:
        message_popup = MessagePopup()

    text = utils.escape_markup(f'{text}')
    if type == 'e':
        text = ''.join(('[b][color=ff0000]', text, '[/color][/b]'))
        message_popup.pr_image.source = 'data/icons/bug.png'
    elif type == 'w':
        text = ''.join(('[b][color=ffff00]', text, '[/color][/b]'))
        message_popup.pr_image.source = 'data/icons/pen.png'
    elif type == 'i':
        text = ''.join(('[b][color=00ff00]', text, '[/color][/b]'))
        message_popup.pr_image.source = 'data/icons/ok.png'
    else:
        pass

    message_popup.title = title
    message_popup.pr_message.text = text
    message_popup.open()


def decision(title, text, fn_ok=None, fn_canc=None, ok_kwargs=None, canc_kwargs=None, **kwargs):
    global decision_popup
    if not decision_popup:
        decision_popup = DecisionPopup()

    text = ''.join(('[b]', utils.escape_markup(text), '[/b]'))
    decision_popup.title = title
    decision_popup.pr_message.text = text
    decision_popup.fn_ok = fn_ok
    decision_popup.fn_canc = fn_canc
    decision_popup.ok_kwargs = ok_kwargs
    decision_popup.canc_kwargs = canc_kwargs

    decision_popup.open()


Builder.load_file('kv/filemanager.kv')


class OpenFilePopup(Popup):
    # Widget hooks
    filechooser = ObjectProperty(None)

    def __init__(self, *args, **kwargs):
        super(OpenFilePopup, self).__init__(**kwargs)
        #self.filechooser.rootpath = os.getcwd()
        self.home = os.getcwd()
        self.filechooser.path = self.home
        self.filechooser.filters = [self.is_valid, ]
        # self.filechooser.dirselect = False

    def cmd_load(self, path, selection):
        '''To be implemented in the extending subclass.'''
        self.dismiss()

    def cmd_cancel(self):
        '''To be implemented in the extending subclass.'''
        self.dismiss()

    def is_valid(self, folder, file):
        '''To be implemented in the extending subclass.'''
        return True
        self.dismiss()


class SaveFilePopup(Popup):
    # Widget hooks
    filechooser = ObjectProperty(None)

    def __init__(self, *args, **kwargs):
        super(SaveFilePopup, self).__init__(**kwargs)
        self.home = os.getcwd()
        self.filechooser.path = self.home
        # self.filechooser.filters = [self.is_valid]
        # self.filechooser.dirselect = False
        # self.mode = SAVE  # or NEW

    def cmd_save(self, path, selection):
        '''To be implemented in the extending subclass.'''
        self.dismiss()

    def do_save(self, file):
        '''To be implemented in the extending subclass.'''
        self.dismiss()

    def cmd_cancel(self):
        '''To be implemented in the extending subclass.'''
        self.dismiss()


class MessagePopup(Popup):
    # Widget hooks
    pr_message = ObjectProperty(None)
    pr_image = ObjectProperty(None)

    def __init__(self, *args, **kwargs):
        super(MessagePopup, self).__init__(**kwargs)


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

    def cmd_ok(self, app):
        if self.fn_ok:
            try:
                self.fn_ok(**self.ok_kwargs)
                return True
            except Exception:
                return False
        return True

    def cmd_cancel(self, app):
        if self.fn_canc:
            try:
                self.fn_canc(**self.canc_kwargs)
                return False
            except Exception:
                return False
        return False
