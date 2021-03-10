
from kivy.uix.dropdown import DropDown
from kivy.properties import ObjectProperty


class DropDownMenu(DropDown):
    """Extends DropDown class.

    Args:
        DropDown ([type]): [description]

    Returns:
        [type]: [description]
    """
    menu_items = ObjectProperty([])

    def __init__(self, *args, **kwargs):
        super(DropDownMenu, self).__init__(**kwargs)

    def add_widget(self, widget, index=0, canvas=None):
        """Add widget to the menu items list.
        """
        self.menu_items.append(widget)
        return DropDown.add_widget(self, widget, index, canvas)
