"""
ItemList
========

The :class: `ItemList` implements a container for items, like a list.
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
from datetime import datetime, timedelta
import kivy
from kivy.app import App
from kivy.lang.builder import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.properties import ObjectProperty
from kivy.properties import StringProperty
from kivy.properties import DictProperty
from kivy.graphics import Color
from kivy.graphics import Line
from kivy.graphics import Rectangle
from kivy.graphics import InstructionGroup
from kivy.metrics import dp
kivy.require('1.11.0')  # Current kivy version


SINGLE = '0'
'''Only one cell is selected.'''
MULTI = '1'
'''The row is selected as long as one of its cells is.'''

Builder.load_file('kv/polyitemlist.kv')


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


# class ItemList(BoxLayout):
class ItemList(FloatLayout):
    """
    The widget works as a container for a list of items. Items can be added and removed.
    It supports an optional bubble-menu that can displayed over it by touching an item.

    Parameters:
    -----------
    - cols:
        a dictionary of field-name that must be displayed in the 'ItemComposite',
        default is None.
    - sel_mode:
        is selection mode: possible values are 'SINGLE' (one line at a time),
        or 'MULTI' (one or more lines at a time).
    """

    def __init__(self, cols=None, sel_mode=SINGLE, **kwargs):
        '''Mask is a dict key-width, if width is None or '' no width is set'''
        super(ItemList, self).__init__(**kwargs)
        self.sel_mode = sel_mode
        self.cols = cols if cols else {}
        self.bubble = None

        self.container = BoxLayout(orientation='vertical', size_hint_y=None)
        scroll_view = ScrollView()
        scroll_view.add_widget(self.container)
        self.add_widget(scroll_view)
        self.container.bind(minimum_height=self.container.setter('height'))

    @property
    def count(self):
        """
        Property:
        ---------
            the number of items.
        """
        return len(self.container.children)

    @property
    def items(self):
        """
        Property:
        ---------
            items list.
        """
        return self.container.children

    def add_bubble(self, bubble):
        """
        Add a bubble menu.
        Parameters:
        -----------
            bubble: the Bubble menu.
        """
        if self.bubble:
            self.remove_widget(self.bubble)
        self.bubble = bubble

    def add(self, item_class, **kwargs):
        """
        Add an item to the list.
        This method internally calls the _add method.
        Parameters
        ----------
        item_class: the 'Item' subclass to be instantiated.

        kwparams: named parameters to instantiate the 'item_class'.
        Returns: the the item_class's instance
        -------
        Boolean: True when added.
        """
        item = item_class(header=self, kwparams=kwargs)
        self._add(item)
        return item

    def _add(self, item_widget):
        '''Internal: add an item widget to the widget list.'''
        self.container.add_widget(item_widget)
        self.container.height += item_widget.height
        self.height = self.container.height
        return None

    def remove(self, item):
        '''Remove the item from the 'ItemList'.'''
        for i in self.items():
            if i.item == item:
                self._remove(i)
                return i
        return None

    def _remove(self, item_widget):
        '''Internal: remove the item widget from the widget list.'''
        self.container.remove_widget(item_widget)
        return None

    def clear(self):
        '''Remove all 'Items' from the 'ItemList'. '''
        self.container.clear_widgets()
        self.container.height = 0
        self.height = self.container.height
        return None

    def _select(self, item):
        '''Internal: select the item according to the selection mode.'''
        if self.sel_mode == MULTI:
            # Do nothing
            pass
        if self.sel_mode == SINGLE:
            for _item in [i for i in self.items if not i is item]:
                _item.selected = False
                selection(_item, _item.selected)
        # Call the bubble on the new selected item!
        if self.bubble:
            self.show_bubble(item)

    def show_bubble(self, item):
        '''Internal: shows the bubble menu over the touched item.'''
        self.remove_widget(self.bubble)
        self.bubble.item = item
        scroll = self.container.parent
        y_view = scroll.to_parent(item.x, item.y)
        if y_view[1] + self.bubble.height + item.height/2 < self.parent.height:
            y = list(map(sum, zip(y_view, (0, item.height/2))))
            self.bubble.arrow_pos = 'bottom_mid'
        else:
            y = list(
                map(sum, zip(y_view, (0, + item.height/2 - self.bubble.height))))
            self.bubble.arrow_pos = 'top_mid'

        self.bubble.pos = (0, y[1])
        self.add_widget(self.bubble)


class Item(GridLayout):
    """Item is the base class implementing an item for the 'ItemList'.
    kwparams parameters:
    ------------------------
    - 'sid':
        item reference in the CompositeItem
    - 'header':
        named parameter is the 'ItemList' reference.
    - 'kwparams':
        named parameter is the 'Item' initialization parameters dict.
    """
    sid = StringProperty('')
    header = ObjectProperty(None)
    kwparams = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(Item, self).__init__(**kwargs)
        self.rows = 1
        self.size_hint_y = None
        self.selected = False  # True/False

    def on_touch_down(self, touch):
        '''On touch down it emphasizes the item according to the solection mode.
        The touch event is consumed.'''
        if not (touch.is_double_tap or touch.is_mouse_scrolling):
            if self.collide_point(touch.x, touch.y):
                self._select()
                # Consume event
                return True
        # Bubble up event
        return super().on_touch_down(touch)

    def _select(self):
        '''Internal: select the item and propagates to the 'ItemList'.'''
        self.selected = not self.selected
        selection(self, self.selected)
        self.header._select(self)


class ItemComposite(Item):
    '''Item is a row made of adjacent cells, each one is a 'ItemPart' instance.
    has a key (see cells property)'''

    def __init__(self, **kwargs):
        super(ItemComposite, self).__init__(**kwargs)
        self.spacing = (dp(10), dp(10))
        self.height = dp(40)
        self._cells = {}
        if self.header.cols:
            self._fill_cols()
        else:
            self._fill()

    @property
    def cells(self):
        '''Cell widgets in this item as a dictionary (name - widgets) pair.'''
        return self._cells

    def _fill(self):
        """Internal: fill the composite with the 'kwparams' parameters."""
        for key, v in self.kwparams.items():
            cell = ItemPart(sid=key)
            cell.text = v
            self.add(cell)

    def _fill_cols(self):
        """Internal: fill the composite with the 'kwparams' parameters."""
        for key in self.header.cols:
            cell = ItemPart(sid=key)
            if key in self.kwparams:
                cell.text = self.kwparams[key]
                self.add(cell)
            else:
                pass

    def add(self, item_cell):
        """Add a subitem to the composite."""
        #item_cell.sid = item_cell.sid if item_cell.sid else id(item_cell)
        #sid = item_cell.sid if item_cell.sid else id(item_cell)
        sid = item_cell.sid if hasattr(
            item_cell, 'sid') and item_cell.sid else id(item_cell)
        # Set the width according to the cols
        if self.header.cols and sid in self.header.cols and self.header.cols[sid]:
            item_cell.width = float(self.header.cols[sid])
        # Adapt text to the available width
        if sid and self.header.cols:
            try:
                if isinstance(item_cell, Label):
                    item_cell.bind(texture_size=self._set_width)
            except Exception as err:
                pass
        self.add_widget(item_cell)
        self.width += item_cell.width
        self._cells[sid] = item_cell

    def _set_width(self, *args):
        """Internal: set the width according to the defined cols or
        adapt the width to the texture_size"""
        subitem = args[0]
        sid = subitem.sid
        texture_size = subitem.texture_size
        # Set the width according to the defined dictionary
        if sid in self.header.cols and self.header.cols[sid]:
            length = float(self.header.cols[sid])
            if texture_size[0] > length:
                subitem.text_size = length, subitem.height
            w = length
        # Adapt the width to the texture size
        else:
            w = subitem.texture_size[0]
        subitem.width = w


# class ItemPart(Label):
class ItemPart(Label):
    """
    Implements a part of a 'ItemComposite' object.
    kwparams named parameters:
    ------------------------
    - 'item':
        named parameter is the 'ItemComposite' reference.
    - 'sid':
        named parameter is the field key.
    """
    # item = ObjectProperty(None)
    sid = StringProperty('')

    def __init__(self, *args, **kwargs):
        super(ItemPart, self).__init__(**kwargs)
        self.selected = False
        self.size_hint_x = None
        self.padding_x = dp(2)

    def on_touch_down(self, touch):
        '''On touch down it emphasizes the item according to the solection mode.
        The touch event is consumed.'''
        if not (touch.is_double_tap or touch.is_mouse_scrolling):
            if self.collide_point(touch.x, touch.y):
                self._select()
                return True
        # Bubble up event
        return super().on_touch_down(touch)

    def _select(self):
        '''Internal: select the item and propagates to the 'ItemList'.'''
        self.selected = not self.selected
        selection(self, self.selected)




if __name__ == '__main__':
    import model
    items = []
    items.extend([
        model.new_item(strict=False, name='item 7', url='', login='',
                       email='tnnfnc@gmaiail.coop', description='This is the account description', tag='Free'),
        model.new_item(strict=False, name='item 2', url='', login='',
                       email='tnnfnc@gmaiail.coop', description='This is the account description', tag='Free'),
        model.new_item(strict=False, name='item 3', url='', login='',
                       email='tnnfnc@gmaiail.coop', description='This is the account ', tag='Web'),
        model.new_item(strict=False, name='item 5', url='', login='',
                       email='tnnfnc@gmaiail.coop', description='This is the account description', tag='Free'),
        model.new_item(strict=False, name='item 4', url='', login='',
                       email='tnnfnc@gmaiail.coop', description='This is  account description', tag='Web'),
        model.new_item(strict=False, name='item 6', url='', login='',
                       email='tnnfnc@gmaiail.coop', description='This is the account description', tag='Free'),
        model.new_item(strict=False, name='item 1', url='', login='',
                       email='tnnfnc@gmaiail.coop', description='This is the account description', tag='Gov'),
        model.new_item(strict=False, name='item 8', url='', login='', email='tnnfnc@gmaiail.coop', description='This is the account description', tag='Gov')]
    )
    items.extend([
        model.new_item(strict=False, name='item 7', url='www.googlex.coop', login='tnnfnc_user_',
                       email='tnnfnc@gmaiail.coop', description='This is the account description', tag='Free'),
        model.new_item(strict=False, name='item 2 - long', url='www.googlex.coop.COOP.NET.kfjrwoif \nkkk', login='tnnfnc_user_',
                       email='tnnfnc@gmaiail.coop', description='This is the account description', tag='Free'),
        model.new_item(strict=False, name='item 3', url='www.googlex.coop', login='tnnfnc__',
                       email='tnnfnc@gmaiail.coop', description='This is the account ', tag='Web'),
        model.new_item(strict=False, name='item 5', url='www.googlex.coop', login='tnnfnc_user_PIPPOLOlog',
                       email='tnnfnc@gmaiail.coop', description='This is the account description', tag='Free'),
        model.new_item(strict=False, name='item 4', url='www.googlex.coop', login='tnnfnc_user_',
                       email='tnnfnc@gmaiail.coop', description='This is  account description', tag='Web'),
        model.new_item(strict=False, name='item 6', url='www.googlex.coop', login='tnnfnc_user_',
                       email='tnnfnc@gmaiail.coop', description='This is the account description', tag='Free'),
        model.new_item(strict=False, name='item 1', url='www.googlex.coop', login='_user_',
                       email='tnnfnc@gmaiail.coop', description='This is the account description', tag='Gov'),
        model.new_item(strict=False, name='item 8', url='www.googlex.coop', login='tnnfnc_user_', email='tnnfnc@gmaiail.coop', description='This is the account description', tag='Gov')]
    )

    to_compare = {'password': 'secret',
                  'home': 'Boston',
                  'mother': 'Clara',
                  'father': 'Unknown',
                  'sister': 'Paula',
                  'brother': 'Jim',
                  'son': '',
                  }
    to_progress = [{'name': 'pippo', 'date': '2019-05-02 14:06:24'},
                   {'name': 'next empty', 'date': '2019-08-02 14:06:24'},
                   {'name': '', 'date': '2019-03-02 14:06:24'},
                   {'name': 'label', 'date': '2019-09-01 14:06:24'},
                   {'name': '', 'date': '2019-08-31 14:06:24'},
                   {'name': '', 'date': '2019-08-22 14:06:24'},
                   {'name': '', 'date': '2019-05-15 14:06:24'},
                   {'name': '', 'date': '2019-05-02 14:06:24'}]

    to_elapsed = [
        {'max': 90, 'elapsed': 190},
        {'max': 70, 'elapsed': 100},
        {'label': '', 'elapsed': 365},
        {'label': '', 'elapsed': 1000},
        {'max': 50, 'elapsed': 180},
        {'label': '', 'elapsed': 1},
        {'label': '', 'elapsed': 0},
        {'elapsed': 80}
    ]


    class TestingApp(App):

        def __init__(self, widget, **kwargs):
            super(TestingApp, self).__init__(**kwargs)
            self.widget = widget

        def build(self):
            # Items

            for item in items:
                w_item = self.widget.add(item_class=ItemComposite, **item)
                # Comparator
            
            return self.widget

    cell_widths = {'name': 100,
                   'url': 200,
                   'login': 150,
                   'elapsed': 100,
                   'warning': 260,
                   'email': 150,
                   'date': 400}

    widget = ItemList(sel_mode=SINGLE, cols=cell_widths)
    # widget = ItemList(sel_mode=MULTI, cols=cell_widths)

    TestingApp(widget=widget).run()
