import os
import sys
import re
import time
import base64
import json
import gettext # in log 4
import json
import gzip as gzip
import threading
import csv
from datetime import datetime
from datetime import timedelta
# passed!

import kivy
from kivy import utils
from kivy.clock import Clock
from kivy.app import App
from kivy.lang import Builder
from kivy.lang.builder import Builder
from kivy.core.clipboard import Clipboard
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivy.properties import ObjectProperty
from kivy.properties import BooleanProperty
from kivy.uix.spinner import Spinner
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from kivy.uix.bubble import BubbleButton
from kivy.uix.screenmanager import Screen
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.behaviors import FocusBehavior
# passed!

#
from kivy.uix.behaviors.focus import FocusBehavior
from kivy.uix.behaviors.compoundselection import CompoundSelectionBehavior
# passed!

# Must reimplement without RecycleList and relative classes:
# But anyway you can import with no harm, but do not use them
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
# passed!

from kivy.graphics import Color
from kivy.graphics import Rectangle
from kivy.graphics import InstructionGroup
from kivy.graphics.instructions import InstructionGroup
# passed!

# import webbrowser as browser # not passed!
# not supported at all
# Must find another strategy for calling browser in Android
# and also in other OSs (Linux, Windows)

import cryptography 
import cryptography.hazmat.primitives.keywrap as keywrap
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
# passed!

import threading # passed!
from threading import Thread
from threading import Timer

# from pynput import keyboard
# from pynput import mouse

from mlist import SelectableList, ItemComposite
from bubblemenu import BubbleMenu, Menu, BubbleBehavior


Builder.load_file('commons.kv')
# passed!
# Import of local modules from import directive in .kv
# files works only if module is in the app dir!!
Builder.load_file(os.path.join('kv', 'dynamic.kv'))
#Popups
Builder.load_file(os.path.join('kv', 'loginpopup.kv'))
Builder.load_file(os.path.join('kv', 'cipherpopup.kv'))
Builder.load_file(os.path.join('kv', 'edittagpopup.kv'))
Builder.load_file(os.path.join('kv', 'infopopup.kv'))
Builder.load_file(os.path.join('kv', 'messagepopup.kv'))
Builder.load_file(os.path.join('kv', 'decisionpopup.kv'))
#Panels building blocks
Builder.load_file(os.path.join('kv', 'loginpanel.kv'))
Builder.load_file(os.path.join('kv', 'userpanel.kv'))
Builder.load_file(os.path.join('kv', 'seedpanel.kv'))
Builder.load_file(os.path.join('kv', 'autopanel.kv'))
Builder.load_file(os.path.join('kv', 'itemactionbubble.kv'))
#Widgets
Builder.load_file(os.path.join('kv', 'passwordstrenght.kv'))
Builder.load_file(os.path.join('kv', 'tagspinner.kv'))
Builder.load_file(os.path.join('kv', 'percentprogressbar.kv'))
Builder.load_file(os.path.join('kv', 'changeview.kv'))
#Screens
Builder.load_file(os.path.join('kv', 'enterscreen.kv'))
Builder.load_file(os.path.join('kv', 'listscreenm.kv'))#<-----
Builder.load_file(os.path.join('kv', 'editscreen.kv'))
Builder.load_file(os.path.join('kv', 'importscreen.kv'))
Builder.load_file(os.path.join('kv', 'changesscreen.kv'))
# passed!

# Screen Names
ENTER = 'Enter'
LIST = 'List'
EDIT = 'Edit'
CHANGES = 'changes'
IMPORT = 'import'

# App
ICON = 'skip.png'
TAGS = ('...')

def f(x):
    return x

import builtins
builtins.__dict__['_'] = f

class EnterScreen(Screen):
    pr_recentfiles = ObjectProperty(None)


class ListScreen(Screen):
    # Widget hooks
    pr_tag = ObjectProperty(None)
    pr_search = ObjectProperty(None)
    pr_expiring = ObjectProperty(None)
    account_list = ObjectProperty(None)


class EditScreen(FocusBehavior, Screen):
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


class ImportScreen(Screen):
    pass


class ChangesScreen(Screen):
    pr_actions = ObjectProperty(None)
    pr_changed_item_list_wid = ObjectProperty(None)


class TagSpinner(Spinner):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class AccountItemList(BubbleBehavior, SelectableList):
    def __init__(self, *args, **kwargs):
        super(AccountItemList, self).__init__(**kwargs)


class AutoPanel(BoxLayout):
    pr_length = ObjectProperty(None)
    pr_letters = ObjectProperty(None)
    pr_symbols = ObjectProperty(None)
    pr_numbers = ObjectProperty(None)
    pr_strenght = ObjectProperty(None)
    pr_password = ObjectProperty(None)



class PasswordStrenght(BoxLayout):
    pr_strenght = ObjectProperty(None)


class UserPanel(BoxLayout):
    pr_password = ObjectProperty(None)
    pr_confirm = ObjectProperty(None)
    pr_strenght = ObjectProperty(None)



class ChangedItemList(SelectableList):
    def __init__(self, *args, **kwargs):
        super(ChangedItemList, self).__init__(**kwargs)

class MappingList(SelectableList):
    def __init__(self, *args, **kwargs):
        super(MappingList, self).__init__(**kwargs)

from kivy.uix.dropdown import DropDown

class DropDownMenu(DropDown):
    def __init__(self, *args, **kwargs):
        super(DropDownMenu, self).__init__(**kwargs)
    



class TestApp(App):
    pr_timer = 'Now'
    def build(self):
        sm = ScreenManager()
        self.root = sm
        sm.add_widget(ImportScreen(name=IMPORT)) # passed!
        sm.add_widget(ChangesScreen(name=CHANGES)) # passed!
        sm.add_widget(EditScreen(name=EDIT)) # passed!
        sm.add_widget(EnterScreen(name=ENTER)) # passed!
        sm.add_widget(ListScreen(name=LIST)) # Not passed! Refactor it!

        # Must reimplement without RecycleList and relative classes
        # log 6
        return sm


TestApp().run()