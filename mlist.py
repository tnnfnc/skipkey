"""
SelectableList
========

The :class: `SelectableList` implements a container a list of widget.
The :class: `Item` is the basic item widget for the list.

    -:class: `ItemComposite` provides an in-line `ItemPart` structure,
"""
import kivy
from kivy.app import App
from kivy.lang.builder import Builder
from kivy.properties import DictProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.behaviors.compoundselection import CompoundSelectionBehavior
from kivy.graphics import Color
from kivy.graphics import Rectangle
from kivy.graphics import InstructionGroup
from kivy.metrics import dp
# Current kivy version
kivy.require('1.11.0')  

Builder.load_string(
"""
<SelectableList>:
    orientation: 'vertical'
    # spacing: (dp(10), dp(10))
    size_hint_y: None
    height: self.minimum_height


<ItemComposite>:
    # Horizontal spacing between parts
    spacing: dp(10)
    # height as decided

# Inherits from Label
<ItemPart>:
    size_hint: None, 1
    # Adapt size to text
    halign: 'left'
    valign: 'center'
    text_size: self.size
    canvas:
        Color:
            rgb: 0.5, 0.5, 0.5, 1
        Line:
            points: self.x, self.y, self.x + self.width, self.y
            width: 1.2

<OneTextLine>:
    size_hint: None, None
    halign: 'left'
    valign: 'top'
    # Adapt size to text
    size: self.texture_size    
""")

def selection(widget, select=False):
    """Emphasizes the widget adding a clear transparent background.

    Args:
        widget (Widget): the widget to apply selection to
        select (bool, optional): Apply selection. Defaults to False.
    """
    group = len(widget.canvas.get_group('sel')) > 0
    if not group:
        sel = InstructionGroup(group='sel')
        sel.add(Color(1, 1, 1, 0.3))
        sel.add(Rectangle(pos=widget.pos, size=widget.size))
    with widget.canvas:
        if select and not group:
            widget.canvas.add(sel)
        elif not select and group:
            widget.canvas.remove_group('sel')
        else:
            pass  # Nothing to do here!

class WidgetCache():
    def __init__(self):
        self.cache = {}

    def set(self, widget):
        """[summary]

        Args:
            widget ([type]): [description]

        Returns:
            [type]: [description]
        """
        key = id(widget)
        if key in self.cache:
            pass
        else:
            self.cache[key] = widget
        return key

    def get(self, key):
        """[summary]

        Args:
            key ([type]): [description]

        Returns:
            [type]: [description]
        """
        return self.cache.get(key, None)

class SelectableList(CompoundSelectionBehavior, BoxLayout):
    """
    The widget works as a container for a list of widget_list.
    """

    def __init__(self, **kwargs):
        '''Mask is a dict key-width, if width is None or '' no width is set'''
        super(SelectableList, self).__init__(**kwargs)
        self.cache = WidgetCache()


    @property
    def widgets(self):
        """
        Property:

        ---------
        List of widgets.
        """
        return self.children

    def add(self, item):
        """Add items to the list. Return a cache id.

        Args:
            item ([type]): [description]

        Returns:
            [type]: [description]
        """
        self.height += item.height
        item.selection_behavior = self
        item.index = (len(self.children) - 1)
        self.add_widget(item)
        return self.cache.set(item)

    def add_from_cache(self, id):
        item = self.cache.get(id)
        if item:
            self.add(item)
        return item

    def remove(self, item):
        '''Remove the item from the 'SelectableList'.'''
        return self.remove_widget(item)

    def clear(self):
        '''Remove all 'Items' from the 'SelectableList'. '''
        self.height = 0
        return self.clear_widgets()

    def select_node(self, node):
        selection(node, True)
        if hasattr(self, 'show_bubble'):
            self.show_bubble(node)
        return super(SelectableList, self).select_node(node)

    def deselect_node(self, node):
        selection(node, False)
        if hasattr(self, 'hide_bubble'):
            self.hide_bubble(node)
        return super(SelectableList, self).deselect_node(node)


class Selectable():
    """Selectable is the base class implementing a selectable item
    for the 'SelectableList'.

    Extend this class for adding your widget to the
    Selectable Item List.

    --------------------

    Properties:

    - data: a dictionary of key - value pairs from
    kwargs or implemented in the subclasses.
    - index: the position of the item in the SelectableList
    """
    _list_index = None

    def __init__(self, **kwargs):
        super(Selectable, self).__init__(**kwargs)
        self._selection_behavior = None
        self.rows = 1

    @property
    def selection_behavior(self):
        return self._selection_behavior

    @selection_behavior.setter
    def selection_behavior(self, b):
        self._selection_behavior = b

    @property
    def index(self):
        return self._list_index

    @index.setter
    def index(self, index):
        """Set the position of the item in the SelectableList."""
        self._list_index = index

    def on_touch_down(self, touch):
        '''On touch down it emphasizes the item according
        to the solection mode.
        The touch event is consumed.'''
        if not (touch.is_double_tap or touch.is_mouse_scrolling):
            if self.collide_point(touch.x, touch.y):
                if self in self.selection_behavior.selected_nodes:
                    self.selection_behavior.deselect_node(self)
                else:
                    self.selection_behavior.select_with_touch(self, touch)
                # Consume event
                return True
        # Bubble up event
        return super().on_touch_down(touch)

    def refresh_view_attrs(self, items):
        """Refresh the values displayed by this widget.

        Overwrite this method in your subclass.

        Args:
            items (dict): key-value pairs with new values.
        """
        return self

class OneTextLine(Label, Selectable):
    def __init__(self, **kwargs):
        super(OneTextLine, self).__init__(**kwargs)


class ItemComposite(Selectable, GridLayout):
    '''An item made of adjacent widget parts.

    ---------------------

    Parameters:

    - widths: is a dictionary of key name and width values.
    The part width will have the desired width.
    - items: key-value arguments will add key - ItemPart
    widget to the ItemComposite.

    has a key (see cells property)'''

    items = DictProperty()
    widths = DictProperty()

    def __init__(self, **kwargs):
        super(ItemComposite, self).__init__(**kwargs)
        self.rows = 1
        if self.items:
            self._compose()

    def _compose(self):
        """(internal) Compose the items into the widget.
        """
        for key, value in self.items.items():
            part = ItemPart()
            part.text = value
            self.add(key, part)

    def add(self, key, item):
        """Add a widget to the composite. 

        ----------------
        The widget will be added also to the dictionary
        data with the corresponding key. Existing keys are overwritten.
        """
        if self.widths:
            w = float(self.widths.get(key, -1))
            if w > 0:
                item.width = w
        # self._data[key] = part
        self.items[key] = item
        self.add_widget(item)
        self.width += item.width


class ItemPart(Label):
    """
    Default widget, part of a 'ItemComposite' object.

    ---------------
    It extends Label.
    """

    def __init__(self, *args, **kwargs):
        super(ItemPart, self).__init__(**kwargs)
        self.size_hint_x = None

    def on_touch_down(self, touch):
        '''On touch down it emphasizes the item according
        to the solection mode.
        The touch event is consumed.'''
        if not (touch.is_double_tap or touch.is_mouse_scrolling):
            if self.collide_point(touch.x, touch.y):
                return True
        # Bubble up event
        return super().on_touch_down(touch)


if __name__ == '__main__':
    pass
    


