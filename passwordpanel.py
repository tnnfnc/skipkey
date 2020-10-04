import os
import kivy
import base64
from kivy.properties import ObjectProperty
from kivy.lang.builder import Builder
from kivy.uix.boxlayout import BoxLayout
from uicontroller import GuiController
from kivy.app import App
import password

import commons

commons.import_kivy_rule(os.path.join('kv', 'userpanel.kv'))
commons.import_kivy_rule(os.path.join('kv', 'autopanel.kv'))
commons.import_kivy_rule(os.path.join('kv', 'passwordpanel.kv'))
# Translation pacify lynt
_ = commons._
message = commons.message

def password_attrs():
    return dict({
        'label': '',
        'auto': 'False',
        'length': '',
        'letters': '',
        'symbols': '',
        'numbers': '',
        'password': ''})

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
        value = password.strength(text)
        self.strenght.value = value

        RGB = [
            '{0:02X}'.format(int(255 if value < 55 else 255 - value*255/100 if value < 100 else 200)),
            '{0:02X}'.format(int(value*255/100 if value < 50 else 255 if value < 100 else 0)),
            '{0:02X}'.format(int(255 if value > 100 else 0))
        ]

        text = _('Strenght') + ' {:.2%}'.format(self.strenght.value/100)
        self.ids._lab_strenght.text = f"[color={''.join(RGB)}]{text}[/color]"


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

    def set_view_attrs(self, item):
        """
        Update the view fields. 
        """
        
        try: 
            password = item.get('password', '')
            if password: 
                self.password.text = App.get_running_app().decrypt(password)
            else:
                self.password.text = password
            self.confirm.text = self.password.text
        except Exception:
            self.confirm.text = self.password.text = ''
        
    def get_view_attrs(self):
        """Return user input from the view.

        Returns:

            dict: {'password': encrypted_password}
        """
        try:
            rvalue = password_attrs()
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
        
    def set_view_attrs(self, item):
        """
        Initialize the input fields from currently edited account item.
        """
        self.length.text = item['length']
        self.symbols.text = item['symbols']
        self.numbers.text = item['numbers']
        self.letters.active = item['letters'] == 'True'
        # self.strenght.set_strength('')
        # In the case of password failure or initial
        try:
            self.password.text = App.get_running_app().show(item)
            self.salt = item.get('password', '')
        except Exception:
            self.password.text =  ''
            self.salt = None

    def get_view_attrs(self):
        """Return user input from the view.

        Returns:

        dict with keys: 'length', 'letters', 'symbols', 'numbers', 'password'
        """
        rvalue = password_attrs()
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

    def __init__(self, **kwargs):
        super(PasswordPanel, self).__init__(**kwargs)
        self.guic = GuiController(self)

    def set_view_attrs(self, item):
        '''Update panels'''
        tabs = self.ids.tabs
        # Refresh 
        self.autopanel.set_view_attrs(password_attrs())
        self.userpanel.set_view_attrs(password_attrs())
        # Update views
        if item['auto'] == 'True':
            self.autopanel.set_view_attrs(item)
            tab = tabs.tab_list[1]
        else:
            self.userpanel.set_view_attrs(item)
            tab = tabs.tab_list[0]
        tabs.switch_to(tab, do_scroll=False)

    def get_view_attrs(self):
        """Return user input from the active tab.

        Returns:
        
        - When Auto tab is active returns a dict with keys:
        'length', 'letters', 'symbols', 'numbers', 'password'
        
        - When Auto tab is active returns a dict with key: 'password'

        - Otherwise returns an empty dict.
        """
        # 0 UserPanel, 1 AutoPanel
        tabs = self.ids.tabs
        rvalue = {'label': self.ids.label.text}
        # Auto panel active
        if tabs.current_tab is tabs.tab_list[1] and self.autopanel.changed():
            rvalue.update(self.autopanel.get_view_attrs())
        # User panel active
        elif tabs.current_tab is tabs.tab_list[0] and self.userpanel.changed():
            rvalue.update(self.userpanel.get_view_attrs())
        return rvalue

    def changed(self):
        """
        Return if the pasword has been changed.
        """
        return self.userpanel.changed() or self.autopanel.changed()

if __name__ == '__main__':

    from kivy.app import App

    class TestApp(App):
        timer = 'Now'
        def build(self):
            self.view = PasswordPanel()
            return self.view

    app = TestApp()
    app.run()
    print(app.view.get_view_attrs())

