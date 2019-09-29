"""SkipKey: a help to password management"""
import kivy
from kivy.app import App
from kivy.lang.builder import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.properties import ObjectProperty
from kivy.properties import StringProperty
from kivy.graphics import Color
from kivy.graphics import Line
from kivy.graphics import Rectangle
from kivy.graphics import InstructionGroup
from kivy.metrics import dp
kivy.require('1.11.0')  # Current kivy version

SINGLE_SEL = '0' '''Only one cell is selected.'''
MULTI_SEL = '1' '''The row is selected as long as one of its cells is.'''

Builder.load_file('data/kv/itemlist.kv')


def selection(widget, select=False):
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


class ItemList(FloatLayout):
    '''List of items'''
    # The current selected row or False
    # selected = ObjectProperty(None)

    def __init__(self, mask=None, cell_widths={}, mode=SINGLE_SEL, **kwargs):
        super(ItemList, self).__init__(**kwargs)
        self.sel_mode = mode
        self.mask = mask
        self.cell_widths = cell_widths  # Cell widths as a dict key-width
        self.size_hint_y = None
        self.box = BoxLayout(orientation='vertical', size_hint_y=None)
        self.add_widget(self.box)
        self.bubble = None

    def add_bubble(self, bubble):
        if self.bubble:
            self.remove_widget(self.bubble)
        self.bubble = bubble

    def add(self, row):
        '''Add an item to the list.'''
        # scroll = ScrollView(do_scroll_x=True, do_scroll_y=False,
        #                     size_hint_y=None, height=item.height,
        #                     scroll_type = ['content', 'bars'])
        # scroll.add_widget(item)
        # self.box.add_widget(scroll)
        item = Item(item_list=self, item=row)
        self._add(item)
        return True

    def _add(self, item_widget):
        '''Add an item widget to the widget list.'''
        self.box.add_widget(item_widget)
        self.box.height += item_widget.height
        self.height = self.box.height
        return True

    def remove(self, row):
        '''Remove item from the list'''
        for i in self.items():
            if i.item == row:
                self._remove(i)
        return True

    def _remove(self, item_widget):
        '''Remove the item widget from the widget list'''
        self.box.remove_widget(item_widget)
        return True

    def clear(self):
        '''Remove items from the list'''
        self.box.clear_widgets()
        self.box.height = 0
        self.height = self.box.height
        return True

    def cmd_selected(self, item):
        s = list(i for i in self.items if not i == item)
        # Unselect other rows
        for i in s:  # item
            i.selected = False
            selection(i, False)
            for c in i.cells.values():  # cell
                c.selected = False
                selection(c, False)
        if self.bubble:
            self.bubble_menu(item)

    def bubble_menu(self, item):
        self.remove_widget(self.bubble)
        self.bubble.item = item
        # Calculate position
        if (item.y + self.bubble.height) > self.height:
            y = self.height - (self.bubble.height + item.height)
            self.bubble.arrow_pos = 'top_mid'
        else:
            y = item.y
            self.bubble.arrow_pos = 'bottom_mid'
#        self.bubble.pos = (self.bubble.width/2, y)
        self.bubble.pos = (0, y)
        self.add_widget(self.bubble)

    @property
    def count(self):
        return len(self.box.children)

    @property
    def items(self):
        return self.box.children


class Item(GridLayout):
    '''Item is a row made of adjacent cells, each one has a key (see cells property)'''
    item_list = ObjectProperty(None)
    item = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(Item, self).__init__(**kwargs)
        self.rows = 1
        self.size_hint_y = None
        self.spacing = (dp(10), dp(10))
        self.height = dp(40)
        self._cells = {}
        if self.item_list.mask:
            self._fill_mask()
        else:
            self._fill()

    @property
    def cells(self):
        '''Cell widgets in this item as a dictionary (name - widgets) pair.'''
        return self._cells

    def _fill(self):
        for k, v in self.item.items():
            cell = ItemCell(item_widget=self, cell_id=k)
            cell.text = v
            self.add_cell(cell)
            self._cells[k] = cell

    def _fill_mask(self):
        for key in self.item_list.mask:
            cell = ItemCell(item_widget=self, cell_id=key)
            if key in self.item:
                cell.text = self.item[key]
                self.add_cell(cell)
                self._cells[key] = cell
            else:
                pass

    def add_cell(self, item_cell):
        self.add_widget(item_cell)
        self.width += item_cell.width

    def select(self):
        '''The row is selected as long as one of its cells is.'''
        if self.item_list.sel_mode == MULTI_SEL:
            selected = False
            for c in self.cells.values():
                selection(c, c.selected)
                if c.selected:
                    selected = True
            selection(self, selected)
        if self.item_list.sel_mode == SINGLE_SEL:
            selected = False
            for c in self.cells.values():
                selection(c, c.selected)
                if c.selected:
                    selected = True
            selection(self, selected)
            self.item_list.cmd_selected(self)


class ItemCell(Label):

    item_widget = ObjectProperty(None)
    cell_id = StringProperty('')

    def __init__(self, *args, **kwargs):
        super(ItemCell, self).__init__(**kwargs)
        self.selected = False
        self.size_hint_x = None
        self.padding_x = dp(2)
        self.bind(texture_size=self._set_width)
        # with self.canvas:
        #     Color(1, 1, 1, 1)
        #     Line(points=(self.x, self.y, self.x + 200, self.y),
        #          width=1.0, joint='miter')

    def on_touch_down(self, touch):
        '''Exclude on_ref_press'''
        if not (touch.is_double_tap or touch.is_mouse_scrolling):
            if self.collide_point(touch.x, touch.y):
                self.select()
        # Bubble up event
        return super().on_touch_down(touch)

    def select(self):
        self.selected = not self.selected
        # Multiple selection
        # for c in self.item.cells.values():
        #     if c.selected and not c is self:
        #         c.selected = False
        # Single selection
        for c in self.item_widget.cells.values():
            if c.selected and not c is self:
                c.selected = False
        self.item_widget.select()

    def _set_width(self, *args):
        # Set the width according to the defined dictionary
        if self.cell_id in self.item_widget.item_list.cell_widths:
            w = self.item_widget.item_list.cell_widths[self.cell_id]
        else:
            w = self.texture_size[0]
        self.width = w

    # @property
    # def key(self):
    #     return self._key


if __name__ == '__main__':
    import model
    import skipkey
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

    class TestingApp(App):

        def __init__(self, widget, **kwargs):
            super(TestingApp, self).__init__(**kwargs)
            self.widget = widget

        def build(self):
            # As highlighted by the image above, show casing the Kivy App Life Cycle,
            # this is the function where you should initialize and return your Root Widget.
            # RETURN THE ROOT WIDGET
            for item in items:
                self.widget.add(item)
            return self.widget
    cell_widths = {'name': 100, 'url': 100, 'login': 100}
    b = skipkey.ItemActionBubble()
    widget = ItemList(mode=SINGLE_SEL, cell_widths=cell_widths)
    widget.add_bubble(b)
    TestingApp(widget=widget).run()
