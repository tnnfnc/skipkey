"""
ItemList
========

The :class: `ItemList` implements a container for items, like a list.
The :class: `Item` is the basic item widget for the list: at present
there are these subclasses of `Item`:

    -:class: `ItemComposite` that provides an in-line `SubItem` structure,
    -:class: `Comparison` that provides a comparison between an 'old' vs  a 'new' 
        object, emphasizing changes of the tho contents,
    -:class: `ProgressItem` that provides a way to represent the
        last changed date with respect to a deadline date.


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
    It supports an optional bubble-menu that can be activate by touching the item and
    displayed over it.

    Parameters:
    -----------
    - mask: 
        a dictionary of field-name that must be displayed in the 'ItemComposite',
        default is None.
    - sel_mode: 
        is selection mode: possible values are 'SINGLE' (one line at a time),
        or 'MULTI' (one or more lines at a time).
    """

    def __init__(self, mask=None, sel_mode=SINGLE, **kwargs):
        '''Mask is a dict key-width, if width is None or '' no width is set'''
        super(ItemList, self).__init__(**kwargs)
        self.sel_mode = sel_mode
        self.mask = mask
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

        kwargs: named parameters to instantiate the 'item_class'.
        Returns:
        -------
        Boolean: True when added.
        """
        item = item_class(header=self, kwargs=kwargs)
        self._add(item)
        return True

    def _add(self, item_widget):
        '''Internal: add an item widget to the widget list.'''
        self.container.add_widget(item_widget)
        self.container.height += item_widget.height
        self.height = self.container.height
        return True

    def remove(self, item):
        '''Remove the item from the 'ItemList'.'''
        for i in self.items():
            if i.item == item:
                self._remove(i)
        return True

    def _remove(self, item_widget):
        '''Internal: remove the item widget from the widget list.'''
        self.container.remove_widget(item_widget)
        return True

    def clear(self):
        '''Remove all 'Items' from the 'ItemList'. '''
        self.container.clear_widgets()
        self.container.height = 0
        self.height = self.container.height
        return True

    def _select(self, item):
        '''Internal: select the item according to the selection mode.'''
        if self.sel_mode == MULTI:
            # Do nothing
            pass
        if self.sel_mode == SINGLE:
            for _item in [i for i in self.items if not i is item]:
                _item.selected = False
                selection(_item, _item.selected)
        # print(item.kwargs)
        # Call the bubble on the last selected item!
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
    kwargs parameters:
    ------------------------
    - 'header':
        named parameter is the 'ItemList' reference.
    - 'kwargs':
        named parameter is the 'Item' initialization parameters dict.
    """
    header = ObjectProperty(None)
    kwargs = ObjectProperty(None)

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
    '''Item is a row made of adjacent cells, each one is a 'SubItem' instance.
    has a key (see cells property)'''

    def __init__(self, **kwargs):
        super(ItemComposite, self).__init__(**kwargs)
        self.spacing = (dp(10), dp(10))
        self.height = dp(40)
        self._cells = {}
        if self.header.mask:
            self._fill_mask()
        else:
            self._fill()

    @property
    def cells(self):
        '''Cell widgets in this item as a dictionary (name - widgets) pair.'''
        return self._cells

    def _fill(self):
        """Internal: fill the composite with the 'kwargs' parameters."""
        for k, v in self.kwargs.items():
            cell = SubItem(item=self, sid=k)
            cell.text = v
            self._add(cell)
            self._cells[k] = cell

    def _fill_mask(self):
        """Internal: fill the composite with the 'kwargs' parameters."""
        for key in self.header.mask:
            cell = SubItem(item=self, sid=key)
            if key in self.kwargs:
                cell.text = self.kwargs[key]
                self._add(cell)
                self._cells[key] = cell
            else:
                pass

    def _add(self, item_cell):
        """Internal: add a subitem to the composite."""
        self.add_widget(item_cell)
        self.width += item_cell.width
        if self.header.mask:
            item_cell.bind(texture_size=self._set_width)

    def _set_width(self, *args):
        """Internal: set the width according to the defined mask."""
        # Set the width according to the defined dictionary
        subitem = args[0]
        if subitem.sid in self.header.mask and self.header.mask[subitem.sid]:
            w = float(self.header.mask[subitem.sid])
        else:
            w = subitem.texture_size[0]
        subitem.width = w


class SubItem(Label):
    """
    Implements a part of a 'ItemComposite' object.
    kwargs named parameters:
    ------------------------
    - 'item':
        named parameter is the 'ItemComposite' reference.
    - 'sid':
        named parameter is the field key.
    """
    item = ObjectProperty(None)
    sid = StringProperty('')

    def __init__(self, *args, **kwargs):
        super(SubItem, self).__init__(**kwargs)
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


class Comparison(Item):
    """
    Provides a comparison between an 'old' vs  a 'new' object, 
    emphasizing changes of its content.
    kwargs parameters:
    -------------------
    - 'name':
        named parameter is the label displayed in the item.
    - 'last':
        named parameter is the new content.
    - 'former':
        named parameter is the old content.
    """
    pr_label = ObjectProperty(None)
    pr_last = ObjectProperty(None)
    pr_former = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(Comparison, self).__init__(**kwargs)
        self.compare()

    def compare(self, *args):
        name = last = former = ''
        if 'name' in self.kwargs:
            name = self.kwargs['name']
        if 'last' in self.kwargs:
            last = self.kwargs['last']
        if 'former' in self.kwargs:
            former = self.kwargs['former']

        name = name if name else ' - '
        last = last if last else ' - '
        former = former if former else ' - '
        if last != former:
            self.pr_last.markup = True
            self.pr_former.markup = True
            last = '[color=ff3333]%s[/color]' % (last)
            former = '[color=33FF33]%s[/color]' % (former)
        else:
            self.pr_last.markup = False
            self.pr_former.markup = False

        self.pr_label.text = name
        self.pr_last.text = last
        self.pr_former.text = former


class ProgressItem(Item):
    """
    Provides a way to graphically represent the last changed date
    with respect to 'today' date. 
    It renders the passed date wuth a progress bar in a [-max, +max] range
    centered on today.
    Parameters:
    -----------
    kwargs named parameters: 
        'max' named parameters is the half date range in days.
        'name' named parameters is label displayed in the item.
        'date' named parameters is the date .

    """

    def __init__(self, max=100, **kwargs):
        super(ProgressItem, self).__init__(**kwargs)
        self.max = max
        if 'max' in self.kwargs:
            self.max = int(self.kwargs.pop('max'))
        self._build()

    def _build(self, *args):
        """Internal."""
        if 'date' in self.kwargs:
            self.date = self.kwargs['date']
        if 'name' in self.kwargs:
            self.name = self.kwargs['name']

        if isinstance(self.date, datetime):
            d = self.date
        else:
            d = datetime.fromisoformat(self.date)

        value = (datetime.now() - d - timedelta(days=self.max)).days
        value = int(value)
        if value < -self.max:
            value = - self.max
            number = '<%s' % (value)
        elif value > self.max:
            value = self.max
            number = '>%s' % (value)
        else:
            value = value
            number = '%s' % (value)

        self.ids['_prb_before'].max = self.max
        self.ids['_prb_after'].max = self.max
        self.ids['_lab_number'].text = number
        self.ids['_lab_label'].text = self.name
        if value < 0:
            self.ids['_prb_before'].value = self.ids['_prb_before'].max + \
                value
            self.ids['_prb_after'].value = 0
            pass
        if value > 0:
            self.ids['_prb_before'].value = self.ids['_prb_before'].max
            self.ids['_prb_after'].value = value
            pass
        else:
            self.ids['_prb_before'] = self.ids['_prb_before'].max
            self.ids['_prb_after'] = 0
            pass


if __name__ == '__main__':
    import model
    # import skipkey
    # 'name': '',  # new name
    # 'url': '',  # Check valid url
    # 'login': '',  # Any string
    # 'email': '',  # @-mail
    # 'description': '',  # Any string
    # 'tag': '',  # Any string
    # 'color': '',  # Basic colors as string
    # 'created': '',  # Date
    # 'changed': '',  # Date
    # 'auto': '',  # True, False=user
    # 'length': '',  # Integer
    # 'letters': '',  # True / False
    # 'numbers': '',  # At least [0 length]
    # 'symbols': '',  # At least [0 length]
    # 'password': '',  # User encrypted password or salt Base64 encoded
    # 'history': ''  # Record history - not yet managed
    items = []
    items.extend([
        model.new_item(name='item 7', url='www.googlex.coop', login='tnnfnc_user_',
                       email='tnnfnc@gmaiail.coop', description='This is the account description', tag='Free'),
        model.new_item(name='item 2', url='www.googlex.coop', login='tnnfnc_user_',
                       email='tnnfnc@gmaiail.coop', description='This is the account description', tag='Free'),
        model.new_item(name='item 3', url='www.googlex.coop', login='tnnfnc__',
                       email='tnnfnc@gmaiail.coop', description='This is the account ', tag='Web'),
        model.new_item(name='item 5', url='www.googlex.coop', login='tnnfnc_user_',
                       email='tnnfnc@gmaiail.coop', description='This is the account description', tag='Free'),
        model.new_item(name='item 4', url='www.googlex.coop', login='tnnfnc_user_',
                       email='tnnfnc@gmaiail.coop', description='This is  account description', tag='Web'),
        model.new_item(name='item 6', url='www.googlex.coop', login='tnnfnc_user_',
                       email='tnnfnc@gmaiail.coop', description='This is the account description', tag='Free'),
        model.new_item(name='item 1', url='www.googlex.coop', login='_user_',
                       email='tnnfnc@gmaiail.coop', description='This is the account description', tag='Gov'),
        model.new_item(name='item 8', url='www.googlex.coop', login='tnnfnc_user_', email='tnnfnc@gmaiail.coop', description='This is the account description', tag='Gov')]
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
                   {'name': 'pippo', 'date': '2019-08-02 14:06:24'},
                   {'name': 'pippo', 'date': '2019-03-02 14:06:24'},
                   {'name': 'pippo', 'date': '2019-09-01 14:06:24'},
                   {'name': 'pippo', 'date': '2019-08-31 14:06:24'},
                   {'name': 'pippo', 'date': '2019-08-22 14:06:24'},
                   {'name': 'pippo', 'date': '2019-05-15 14:06:24'},
                   {'name': 'pippo', 'date': '2019-05-02 14:06:24'}]

    class TestingApp(App):

        def __init__(self, widget, **kwargs):
            super(TestingApp, self).__init__(**kwargs)
            self.widget = widget

        def build(self):
            # Items
            for item in items:
                self.widget.add(item_class=ItemComposite, **item)
                self.widget.add(item_class=Item, **item)
            # Comparator
            for k, v in to_compare.items():
                self.widget.add(item_class=Comparison, key=k, name=k,
                                last=v*8, former='old_%s' % (v)*18)
            # To progress
            for k in to_progress:
                self.widget.add(item_class=ProgressItem, max='44',
                                name=k['name'], date=k['date'])

            return self.widget

    cell_widths = {'name': 100, 'url': 200,
                   'login': 150, 'email': None, 'description': ''}

    widget = ItemList(sel_mode=SINGLE, mask=cell_widths)
    # widget = ItemList(sel_mode=MULTI, mask=cell_widths)

    TestingApp(widget=widget).run()
