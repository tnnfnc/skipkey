from kivy.lang.builder import Builder
from kivy.properties import StringProperty
from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup
from kivy import utils

from localize import translate
import os

# Commons 
current_dir = os.path.dirname(os.path.realpath(__file__))
icons_dir = os.path.join(current_dir, 'data', 'icons')
locale_dir = os.path.join(current_dir, 'locale')
kivy_dir = os.path.join(current_dir, 'kv')
_ = translate(domain='skipkey', localedir=locale_dir, languages=['it'])

def import_kivy_rule(files):
    """Import a kivy rule file only if it was not already imported.
        Check for full file name.
    Args:
        files (iterable): kivy rule files
    """
    if Builder:
        if isinstance(files, str):
            files = (files,)
        for file in files:
            if os.path.basename(file) in (os.path.os.path.basename(f) for f in Builder.files):
                continue
            Builder.load_file(file)

import_kivy_rule('commons.kv')
import_kivy_rule(os.path.join('kv', 'dynamic.kv'))
import_kivy_rule(os.path.join('kv', 'messagepopup.kv'))
import_kivy_rule(os.path.join('kv', 'decisionpopup.kv'))

class MessagePopup(Popup):
    # Widget hooks
    message = ObjectProperty(None)
    image = ObjectProperty(None)

    def __init__(self, *args, **kwargs):
        super(MessagePopup, self).__init__(**kwargs)

    def show(self, title='', text='', type='i'):
        text = utils.escape_markup(f'{text}')
        color = []
        if type == 'e':
            _color = [1,0,0,1]
            text = ''.join(('[color=ff0000]', text, '[/color]'))
            self.image.source = os.path.join('data', 'icons', 'info_error.png')
        elif type == 'w':
            _color = [1,1,0,1]
            text = ''.join(('[color=ffff00]', text, '[/color]'))
            self.image.source = os.path.join('data', 'icons', 'info_warning.png')
        elif type == 'i':
            _color = [0,1,0,1]
            text = ''.join(('[color=00ff00]', text, '[/color]'))
            self.image.source = os.path.join('data', 'icons', 'info_ok.png')
        else:
            pass

        self.title = title
        self.title_color = _color
        self.message.text = text
        self.open()


class DecisionPopup(Popup):
    # Widget hooks
    message = ObjectProperty(None)
    fn_ok = ObjectProperty(None)
    fn_canc = ObjectProperty(None)
    ok_kwargs = ObjectProperty(None)
    canc_kwargs = ObjectProperty(None)

    def __init__(self, title='', text='', *args, **kwargs):
        super(DecisionPopup, self).__init__(**kwargs)
        self.message.text = text
        self.title = title

    def show(self, title, text, fn_ok=None, fn_canc=None,
             ok_kwargs={}, canc_kwargs={}, **kwargs):
        self.title = title
        self.message.text = ''.join(
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


message = MessagePopup().show

decision = DecisionPopup().show