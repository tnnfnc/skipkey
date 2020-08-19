# from kivy.uix.boxlayout import BoxLayout
"""
The library implements a simple layout controller for customize
the appearance of the app. A background image can be added to layout top
containers and widgets and their color can be modified.
##USAGE
For activating the customization, add this line to the __init__ method of
the widget class you like to change, reference the new GuiController object
into yours for preventing garbaging:
def __init__(self, **kwargs):
        self.guic = GuiController(self)
"""
from kivy.graphics import Rectangle
from kivy.graphics import Color
import kivy

GUI_ACTIVE = True
LAYT_BACKGROUND_SRC = ''#"data/background.png"
LAYT_BACKGROUND_CLR = (0, 0.9, 0.0, 0.8)
WIDG_BACKGROUND_SRC = ''#"data/background.png"
WIDG_BACKGROUND_CLR = None#(0, 0, 0, 0.8)


class GuiController():

    def __init__(self, root, **kwargs):
        super(GuiController, self).__init__(**kwargs)
        if GUI_ACTIVE and hasattr(root, 'walk'):
            iterator = root.walk(restrict=False, loopback=False)
            for w in iterator:
                if not hasattr(w, 'gui_manager'):
                    if isinstance(w, kivy.uix.boxlayout.BoxLayout):
                        print(w.__class__)
                        LayoutDelegate(w)
                    elif isinstance(w, kivy.uix.widget.Widget):
                        print(w.__class__)
                        WidgetDelegate(w)


class GuiDelegate():

    def __init__(self, layout, **kwargs):
        super(GuiDelegate, self).__init__(**kwargs)
        if not hasattr(layout, 'gui_manager'):
            setattr(layout, 'gui_manager', self)
            self.layout = layout
            self.rect = None
            self.do_layout()

    def do_layout(self):
        pass

    def update_gui(self, *args):
        """listen to size and position changes"""
        pass


class LayoutDelegate(GuiDelegate):

    def do_layout(self):
        ly = self.layout
        with ly.canvas.before:
            if LAYT_BACKGROUND_CLR:
                Color(LAYT_BACKGROUND_CLR)
            if LAYT_BACKGROUND_SRC:
                self.rect = Rectangle(
                    source=LAYT_BACKGROUND_SRC, size=ly.size, pos=ly.pos)
        if LAYT_BACKGROUND_SRC:
            ly.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        """listen to size and position changes"""
        self.rect.pos = self.layout.pos
        self.rect.size = self.layout.size


class WidgetDelegate(GuiDelegate):

    def do_layout(self):
        ly = self.layout
        with ly.canvas.before:
            if WIDG_BACKGROUND_CLR:
                Color(WIDG_BACKGROUND_CLR)
            if WIDG_BACKGROUND_SRC:
                self.rect = Rectangle(
                    source=WIDG_BACKGROUND_SRC, size=ly.size, pos=ly.pos)
        if WIDG_BACKGROUND_SRC:
            ly.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        """listen to size and position changes"""
        self.rect.pos = self.layout.pos
        self.rect.size = self.layout.size
