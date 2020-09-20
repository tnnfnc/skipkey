"""File manager"""
import kivy
from kivy.lang.builder import Builder
from kivy.uix.popup import Popup
from kivy.properties import ObjectProperty
from kivy import utils
import os

kivy.require('1.11.0')  # Current kivy version


Builder.load_file(os.path.join('kv', 'filemanager.kv'))


class OpenFilePopup(Popup):
    # Widget hooks
    filechooser = ObjectProperty(None)

    def __init__(self, *args, **kwargs):
        super(OpenFilePopup, self).__init__(**kwargs)
        self.home = os.getcwd()
        self.filechooser.path = self.home
        self.filechooser.filters = [self.is_valid, ]

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

    def cmd_save(self, path, selection):
        '''To be implemented in the extending subclass.'''
        self.dismiss()

    # def save(self, file):
    #     '''To be implemented in the extending subclass.'''
    #     self.dismiss()

    def cmd_cancel(self):
        '''To be implemented in the extending subclass.'''
        self.dismiss()
