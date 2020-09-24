
from kivy.uix.dropdown import DropDown

class DropDownMenu(DropDown):
    menu_items = []
    def __init__(self, *args, **kwargs):
        super(DropDownMenu, self).__init__(**kwargs)

    def add_widget(self, widget, index=0, canvas=None):
        self.menu_items.append(widget)
        return DropDown.add_widget(self, widget, index, canvas)