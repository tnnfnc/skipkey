import os
import re
import kivy
import base64
from kivy.properties import ObjectProperty
from kivy.lang.builder import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from uicontroller import GuiController
from kivy.clock import Clock
from kivy.app import App

import commons

commons.import_kivy_rule((
    os.path.join('kv', 'userpanel.kv'),
    os.path.join('kv', 'autopanel.kv'),
    os.path.join('kv', 'passwordpanel.kv'),
    os.path.join('kv', 'password.kv'),
    os.path.join('kv', 'passwordpopup.kv'),
    os.path.join('kv', 'passwordstrenght.kv')
))
# Translation pacify lynt
_ = commons._
message = commons.message


def new_attrs():
    """Data dictionary managed by views.

    Returns:

    - dict: a dictionary of all data from the views.
    """
    return dict({
        'label': '',
        'auto': 'True',
        'length': '',
        'letters': '',
        'symbols': '',
        'numbers': '',
        'password': ''})


def strength(password):
    """Calculate the strenght of a password.

    Args:

        password (string): password

    Returns:

        integer: the password strength
    """
    p = password
    l = len(password)
    n = 0
    if len(p) > 8:
        n += 1
    if len(re.findall('[A-Z]', p)) > round(len(p)*0.35):
        n += 1
    if len(re.findall('[a-z]', p)) > round(len(p)*0.35):
        n += 1
    if len(re.findall('[\d]', p)) > round(len(p)*0.15):
        n += 1
    if len(re.findall('[\W]', p)) > round(len(p)*0.20):
        n += 1
    requirements = n
    # Sum the repeated any type of characters
    n = 0
    r = dict([(c, 0) for c in p])
    for c in p:
        r[c] += 1
    repeated = sum(r.values()) - len(r)

    # Sequentials
    n = 0
    for i in range(1, len(p)):
        d = ord(p[i - 1]) - ord(p[i])
        if d == 1 or d == -1:
            n += 1
    sequentials = n
    # Symbols or numbers not in the first or last position
    # Minimum 8 characters in length Contains 3/4 of the following items:
    # Uppercase Letters - Lowercase Letters - Numbers - Symbols
    good = 4 * len(re.findall('[a-zA-Z]', p)) +\
        2 * (l - len(re.findall('[A-Z]', p))) +\
        2 * (l - len(re.findall('[a-z]', p))) +\
        4 * len(re.findall('\d', p)) +\
        6 * len(re.findall('\W', p)) +\
        2 * len(re.findall('[\d|\W]', p[1:-1])) +\
        2 * requirements

    bad = len(re.findall('[a-zA-Z]', p)) +\
        len(re.findall('\d', p)) +\
        repeated +\
        2 * len(re.findall('[A-Z]{2,}', p)) +\
        2 * len(re.findall('[a-z]{2,}', p)) +\
        2 * len(re.findall('\d{2,}', p)) +\
        3 * sequentials
    return int(good - bad)


def requirements(text):
    r = dict(letters=round(len(text)*52/89),
             numbers=round(len(text)*10/89),
             symbols=round(len(text)*27/89))
    return r


class PasswordStrenght(BoxLayout):
    """
    GUI element. Password strength gauge.
    """
    # Widget hooks
    strenght = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(PasswordStrenght, self).__init__(**kwargs)

    def set_strength(self, text):
        """
        Set the password strenght value.

        It evaluates the password strength.
        """
        value = strength(text)
        self.strenght.value = value

        RGB = [
            '{0:02X}'.format(int(255 if value < 55 else 255 -
                                 value*255/100 if value < 100 else 200)),
            '{0:02X}'.format(int(value*255/100 if value <
                                 50 else 255 if value < 100 else 0)),
            '{0:02X}'.format(int(255 if value > 100 else 0))
        ]

        text = _('Strenght') + ' {:.2%}'.format(self.strenght.value/100)
        self.ids._lab_strenght.text = f"[color={''.join(RGB)}]{text}[/color]"


class Password(GridLayout):
    def __init__(self, **kwargs):
        super(Password, self).__init__(**kwargs)
        self.guic = GuiController(self)
        self.attrs = {}
        self.default_label = ''

    def set_view_attrs(self, attrs):
        """Update the view attributes.

        Args:
            attrs (dict): view attributes.
        """
        self.attrs = attrs
        text = attrs.get('label', '')
        text = text if text != '' else _('Create password')
        self.ids.password.text = text

    def get_view_attrs(self):
        """Get view attributes.

        Get user input from the popup.

        Returns:

            dict: view data.
        """
        return self.attrs

    def cmd_change_pwd(self):
        # Keep an instance of PasswordPopup with
        # current editing values
        self.popup = PasswordPopup()
        self.popup.title = _('Edit Password')  # + ': ' + self.attrs['name']
        if self.default_label and self.attrs['label'] == '':
            self.attrs['label'] = self.default_label
        self.popup.set_view_attrs(self.attrs)
        self.popup.call_back = self.set_view_attrs
        self.popup.open()

    def cmd_delete_pwd(self):
        """Delete the password.
        """
        self.update = False
        self.attrs = new_attrs()
        self.ids.password.text = _('Create password')

    def on_call_back(self, *args):
        """Update internal password view attrs.
        """
        popup_attrs = args[0].attrs
        self.attrs.update(popup_attrs)
        self.ids.password.text = popup_attrs['label']


class UserPanel(BoxLayout):
    """
    GUI element. Panel for changing password.
    It is used by LoginPopup, CipherPopup.
    """
    # Widget hooks
    password = ObjectProperty(None)
    confirm = ObjectProperty(None)
    strenght = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(UserPanel, self).__init__(**kwargs)
        self.guic = GuiController(self)

    def cmd_text(self, text):
        """
        Callback for TextInput on_text event.
        """
        self.strenght.set_strength(text)

    def set_view_attrs(self, attrs):
        """
        Update the view fields. 
        """

        try:
            password = attrs.get('password', '')
            if password:
                self.password.text = App.get_running_app().decrypt(password)
            else:
                self.password.text = password
            self.confirm.text = self.password.text
        except Exception:
            self.confirm.text = self.password.text = ''

    def get_view_attrs(self):
        """Return user input from the active tab.

        Returns:

        - dict: a dictionary from user input.
        """
        try:
            rvalue = new_attrs()
            app = App.get_running_app()
            rvalue.update({'auto': 'False',
                           'password': app.encrypt(self.password.text)})
            return rvalue
        except Exception as e:
            message(title=_('Password Error'), text=e.args[0], type='e')
            return {}

    def changed(self):
        """
        Return True if the pasword has been changed.
        """
        if self.password.text and self.confirm.text:
            return self.password.text != '' and self.password.text == self.confirm.text
        return False


class AutoPanel(BoxLayout):
    """
    GUI element. Panel for generating the password.

    It is used in EditScreen.
    """
    # Widget hooks
    length = ObjectProperty(None)
    letters = ObjectProperty(None)
    symbols = ObjectProperty(None)
    numbers = ObjectProperty(None)
    strenght = ObjectProperty(None)
    password = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(AutoPanel, self).__init__(**kwargs)
        self.salt = None
        self.guic = GuiController(self)

    # def set_strength(self, text):
    #     self.strenght.set_strength(text)

    def cmd_text(self, text):
        """
        Callback for TextInput on_text event.
        """
        self.strenght.set_strength(text)

    def set_view_attrs(self, attrs):
        """
        Initialize the input fields from currently edited account item.
        """
        self.length.text = attrs['length']
        self.symbols.text = attrs['symbols']
        self.numbers.text = attrs['numbers']
        self.letters.active = attrs['letters'] == 'True'
        # self.strenght.set_strength('')
        # In the case of password failure or initial
        try:
            self.password.text = App.get_running_app().regenerate(attrs)
            self.salt = attrs.get('password', '')
        except Exception:
            app = App.get_running_app()
            length = str(app.config.getdefault(
                app.SETTINGS, app.PWDLEN, 10))
            self.length.text = length
            self.password.text = ''
            self.salt = None

    def get_view_attrs(self):
        """Return user input from the active tab.

        Returns:

        - dict: a dictionary from user input.
        """
        rvalue = new_attrs()
        rvalue.update({
            'auto': 'True',
            'length': self.length.text,
            'letters': str(self.letters.active),
            'symbols': self.symbols.text,
            'numbers': self.numbers.text,
            'password': self.salt if self.salt else ''})
        return rvalue

    def changed(self):
        """
        Return True if the pasword has been changed.
        """
        if self.password.text:
            return self.password.text != ''
        return False

    def cmd_generate(self):
        app = App.get_running_app()
        try:
            pwd, salt = app.generate(**self.get_view_attrs())
            self.password.text = pwd
            # self.strenght.set_strength(pwd)
            # The salt matter!
            self.salt = str(base64.b64encode(salt), encoding='utf-8')
        except ValueError as e:
            message(_('Password'), *e.args, 'e')


class PasswordPanel(BoxLayout):
    """
    GUI element. Panel for user login.
    """
    # Widget hooks
    autopanel = ObjectProperty(None)
    userpanel = ObjectProperty(None)
    tabs = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(PasswordPanel, self).__init__(**kwargs)
        # self.guic = GuiController(self)

    def set_view_attrs(self, attrs):
        '''Update panels'''
        # Refresh
        self.autopanel.set_view_attrs(new_attrs())
        self.userpanel.set_view_attrs(new_attrs())
        self.ids.label.text = attrs.get('label', '')
        # Update views
        n_attrs = new_attrs()
        n_attrs.update(attrs)
        if n_attrs['auto'] == 'True':
            self.autopanel.set_view_attrs(n_attrs)
            tab = self.tabs.tab_list[1]
        else:
            self.userpanel.set_view_attrs(n_attrs)
            tab = self.tabs.tab_list[0]

        Clock.schedule_once(
            lambda dt: self.tabs.switch_to(tab, do_scroll=False), 0)

    def get_view_attrs(self):
        """Return user input from the active tab.

        Returns:

        - dict: a dictionary from user input.
        """
        rvalue = new_attrs()
        # 0 UserPanel, 1 AutoPanel
        # Auto panel active
        if self.tabs.current_tab is self.tabs.tab_list[1] and self.autopanel.changed():
            rvalue.update(self.autopanel.get_view_attrs())
        # User panel active
        elif self.tabs.current_tab is self.tabs.tab_list[0] and self.userpanel.changed():
            rvalue.update(self.userpanel.get_view_attrs())
        rvalue.update({'label': self.ids.label.text})
        return rvalue

    def changed(self):
        """
        Return if the pasword has been changed.
        """
        return self.userpanel.changed() or self.autopanel.changed()


class PasswordPopup(Popup):

    passwordpanel = ObjectProperty(None)

    def __init__(self, *args, **kwargs):
        super(PasswordPopup, self).__init__(**kwargs)
        self.attrs = {}

    def set_view_attrs(self, attrs):
        self.attrs = attrs
        self.passwordpanel.set_view_attrs(self.attrs)

    def get_view_attrs(self):
        """Return the user input.

        Returns:
            dict: view data
        """
        return self.attrs

    def cmd_save(self):
        """Save the password
        """
        if self.passwordpanel.changed():
            rvalue = new_attrs()
            rvalue.update(self.passwordpanel.get_view_attrs())
            if rvalue['label'] == '':
                message(_('Password label'), _(
                    'A password label is required'), 'e')
                return
            self.attrs = rvalue
            # Update the text of the caller
            if self.call_back:
                self.call_back(rvalue)
            self.dismiss()

    def cmd_cancel(self):
        """Cancel without saving.
        """
        self.dismiss()
