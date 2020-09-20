"""
SelectableItemList
========

The :class: `SelectableItemList` implements a container for widget_list, like a list.
The :class: `Item` is the basic item widget for the list: at present
there are these subclasses of `Item`:

    -:class: `ItemComposite` that provides an in-line `ItemPart` structure,
    -:class: `Comparison` that provides a comparison between an 'old' vs  a 'new'
        object, emphasizing changes of the tho contents,
    -:class: `ProgressItem` that provides a way to represent the
        new changed date with respect to a deadline date.


SkipKey: a help to password management
"""
# from progresslist import ProgressItem
# from datetime import datetime, timedelta
import kivy
from kivy.app import App
from kivy.lang.builder import Builder
from kivy.uix.boxlayout import BoxLayout
# from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.behaviors.compoundselection import CompoundSelectionBehavior
# from kivy.properties import ObjectProperty
# from kivy.properties import StringProperty
# from kivy.properties import DictProperty
from kivy.graphics import Color
# from kivy.graphics import Line
from kivy.graphics import Rectangle
from kivy.graphics import InstructionGroup
from kivy.metrics import dp
kivy.require('1.11.0')  # Current kivy version

Builder.load_string(
    """
<Item>:

<ItemPart>:
    size_hint: None, 1
    # padding_x: dp(2)
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
    """)


def selection(widget, select=False):
    """
    Emphasizes the widget adding a clear transparent background.
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


# class SelectableItemList(BoxLayout):
# class SelectableItemList(CompoundSelectionBehavior, BoxLayout):
class SelectableItemList(CompoundSelectionBehavior, BoxLayout):
    """
    The widget works as a container for a list of widget_list.
    """

    def __init__(self, **kwargs):
        '''Mask is a dict key-width, if width is None or '' no width is set'''
        super(SelectableItemList, self).__init__(**kwargs)
        # self.orientation='vertical'
        # self.size_hint_y=None
        self.container = BoxLayout(orientation='vertical', size_hint_y=None)
        self.container.bind(minimum_height=self.container.setter('height'))
        #
        scroll_view = ScrollView()
        scroll_view.add_widget(self.container)
        self.add_widget(scroll_view)

    @property
    def row_count(self):
        """
        Property:

        ---------
        Number of widget in the list.
        """
        return len(self.container.children)

    @property
    def widget_list(self):
        """
        Property:

        ---------
        List of widgets.
        """
        return self.container.children

    def add(self, item, **kwargs):
        """
        Add a widget to the list.

        ----------
        Parameters:

            item: the widget.

        -------
        Return:

            The number of list elements
        """
        item.selection_behavior = self
        self.container.add_widget(item)
        item.set_index(len(self.container.children) - 1)
        self.container.height += item.height
        self.height = self.container.height
        return len(self.container.children)

    def remove(self, item):
        '''Remove the item from the 'SelectableItemList'.'''
        return self.container.remove_widget(item)

    def clear(self):
        '''Remove all 'Items' from the 'SelectableItemList'. '''
        self.container.clear_widgets()
        self.container.height = 0
        self.height = self.container.height

    def select_node(self, node):
        selection(node, True)
        if hasattr(self, 'show_bubble'):
            self.show_bubble(node)
        return super(SelectableItemList, self).select_node(node)

    def deselect_node(self, node):
        selection(node, False)
        if hasattr(self, 'hide_bubble'):
            self.hide_bubble(node)
        return super(SelectableItemList, self).deselect_node(node)

    def on_selected_nodes(self, gird, nodes):
        print("Selected nodes = {0}".format(nodes))


class Item(GridLayout):
    """Item is the base class implementing an item
    for the 'SelectableItemList'.

    Extend this class for adding your widget to the
    Selectable Item List.

    --------------------

    Properties:

    - data: a dictionary of key - value pairs from
    kwargs or implemented in the subclasses.
    - index: the position of the item in the SelectableItemList
    """
    _list_index = None

    def __init__(self, **kwargs):
        super(Item, self).__init__(**kwargs)
        self.rows = 1
        self._selection_behavior = None
        self._data = kwargs

    @property
    def selection_behavior(self):
        return self._selection_behavior

    @selection_behavior.setter
    def selection_behavior(self, b):
        self._selection_behavior = b

    @property
    def data(self):
        """Return the item data dictionary.

        Item data must be implemented in your subclass."""
        return self._data

    @property
    def index(self):
        return self._list_index

    def set_index(self, index):
        """Set the position of the item in the SelectableItemList."""
        self._list_index = index

    def on_touch_down(self, touch):
        '''On touch down it emphasizes the item according
        to the solection mode.
        The touch event is consumed.'''
        if not (touch.is_double_tap or touch.is_mouse_scrolling):
            if self.collide_point(touch.x, touch.y):
                #self.selection_behavior.select_with_touch(self, touch)
                if self in self.selection_behavior.selected_nodes:
                    self.selection_behavior.deselect_node(self)
                else:
                    self.selection_behavior.select_with_touch(self, touch)
                # Consume event
                return True
        # Bubble up event
        return super().on_touch_down(touch)


class ItemComposite(Item):
    '''An item made of adjacent widget parts.

    ---------------------

    Parameters:

    - header: is a dictionary of key name and width values.
    The part width will have the desired width.
    - kwargs: key-value arguments will add key - ItemPart
    widget to the ItemComposite.

    has a key (see cells property)'''

    def __init__(self, header={}, **kwargs):
        super(ItemComposite, self).__init__()
        self.rows = 1
        self.spacing = (dp(10), dp(10))
        self.height = dp(40)
        self.header = header
        if self.header:
            self._fill_cols(kwargs)
        else:
            self._fill(kwargs)

    def _fill(self, kwargs):
        """Internal: fill the composite with the 'kwparams' parameters."""
        for key, value in kwargs.items():
            cell = ItemPart()
            cell.text = value
            self.add(key, cell)

    def _fill_cols(self, kwargs):
        """Internal: fill the composite with the 'kwparams' parameters."""
        for key in self.header:
            cell = ItemPart()
            if key in kwargs:
                cell.text = kwargs[key]
                self.add(key, cell)
            else:
                pass

    def add(self, key, part):
        """Add a widget to the composite. 

        ----------------
        The widget will be added also to the dictionary
        data with the corresponding key. Existing keys are overwritten.
        """
        if self.header:
            part.width = float(self.header.get(key, None))
            # Adapt text to the available width
        # Add to _data when called
        self._data[key] = part
        self.add_widget(part)
        self.width += part.width


class ItemPart(Label):
    """
    Default widget, part of a 'ItemComposite' object.

    ---------------
    It extends Label.
    """

    def __init__(self, *args, **kwargs):
        super(ItemPart, self).__init__(**kwargs)
        self.size_hint_x = None
        self.padding_x = dp(4)

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
    import model
    from bubblemenu import BubbleDecorator, BubbleMenu

    cols = {'name': 100,
            'url': 200,
            'login': 150,
            }

    class SelectableBubbleList(BubbleDecorator, SelectableItemList):
        def __init__(self, **kwargs):
            super(SelectableBubbleList, self).__init__(**kwargs)

    class MyLabel(Item, Label):
        def __init__(self, **kwargs):
            Item.__init__(self)

    class TestingApp(App):

        def __init__(self, widget, **kwargs):
            super(TestingApp, self).__init__(**kwargs)
            self.widget = widget

        def build(self):
            # Items
            data = [
                {'name': 'Abracadabra', 'url': 'www.googlere.com',
                    'login': 'UsernamePippo'},
                {'name': 'Abracadabra', 'url': 'www.googlere.com',
                    'login': 'UsernamePippo'},
                {'name': 'Abracadabra', 'url': 'www.googlere.com',
                    'login': 'UsernamePippo'},
                {'name': 'Abracadabra', 'url': 'www.googlere.com',
                    'login': 'UsernamePippo'},
                {'name': 'Abracadabra', 'url': 'www.googlere.com',
                    'login': 'UsernamePippo'},
                {'name': 'Abracadabra', 'url': 'www.googlere.com',
                    'login': 'UsernamePippo'},
                {'name': 'Abracadabra', 'url': 'www.googlere.com',
                    'login': 'UsernamePippo'},
                {'name': 'Abracadabra', 'url': 'www.googlere.com',
                    'login': 'UsernamePippo'},
                {'name': 'Abracadabra', 'url': 'www.googlere.comwww.googlere.com',
                    'login': 'UsernamePippo'},
                {'name': 'Abracadabra', 'url': 'www.googlere.com',
                    'login': 'UsernamePippo'},
                {'name': 'Abracadabra', 'url': 'www.googlere.com',
                    'login': 'UsernamePippo'},
            ]

            for item in data:
                widg = ItemComposite(**item)
                w_item = self.widget.add(ItemComposite(header=cols, **item))
                self.widget.add(MyLabel(**item))
                # Comparator

            return self.widget

    # widget = SelectableItemList()
    widget = SelectableBubbleList()
    widget.add_bubble(BubbleMenu(size_hint=(
        None, None), size=(dp(300), dp(60))))

    TestingApp(widget=widget).run()
