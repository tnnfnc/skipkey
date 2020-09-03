from kivy.factory import Factory
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.label import Label
from kivy.properties import BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color
from kivy.graphics import Line
from kivy.graphics import Rectangle


Builder.load_file('kv/recycleview.kv')


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


class ItemController(RecycleView):
    """MVC Controller"""

    def __init__(self, **kwargs):
        super(ItemController, self).__init__(**kwargs)
        # self.viewclass = 'ItemAdapter'


class ItemAdapter(RecycleDataViewBehavior, GridLayout):
    """MVC Viev adapter.

    --------------
    Extends this class and implement refresh_view_attrs(self, rv, index, data) for
    updating data from the model.
    """
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def __init__(self, **kwargs):
        super(ItemAdapter, self).__init__(**kwargs)
        self.rows = 1
        self.index = -1

    def refresh_view_attrs(self, rv, index, data):
        ''' Catch and handle the view changes '''
        return super().refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        '''On touch down it emphasizes the item according to the selection mode.
        The touch event is consumed.

        Send the event to the SelectionManager, that calls deselect_node() 
        on selected nodes and select_node() on node under selection.'''
        if not (touch.is_double_tap or touch.is_mouse_scrolling):
            if self.collide_point(touch.x, touch.y):
                # Send the event to the SelectionManager, it calls deselect_node()
                # on selected and select_node() on new selected node
                if self.selected:
                    self.parent.deselect_node(self)
                else:
                    self.parent.select_with_touch(self, touch)
                return True
        # Bubble up event
        return super().on_touch_down(touch)

    def apply_selection(self, index, rv, is_selected):
        ''' Respond to the selection of items in the view. 

        Called at changes of layout, scrolling, changing the data model'''
        if is_selected:
            pass
        else:
            pass


class SubItem(Label):
    """Part of ItemAdapter"""

    def __init__(self, *args, **kwargs):
        super(SubItem, self).__init__(**kwargs)


class SelectableRecycleBoxLayout(FocusBehavior, LayoutSelectionBehavior,
                                 RecycleBoxLayout):
    ''' Adds selection and focus behaviour to the view. '''

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_selected_nodes(self, gird, nodes):
        pass
    
    def select_node(self, node):
        node.selected = True
        selection(node, select=node.selected)
        if hasattr(self.parent.parent, 'show_bubble'):
            self.parent.parent.show_bubble(node)
        return super(SelectableRecycleBoxLayout, self).select_node(node)

    def deselect_node(self, node):
        node.selected = False
        selection(node, select=node.selected)
        if hasattr(self.parent.parent, 'hide_bubble'):
            self.parent.parent.hide_bubble(node)
        super(SelectableRecycleBoxLayout, self).deselect_node(node)


