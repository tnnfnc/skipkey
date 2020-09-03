from kivy.uix.bubble import Bubble
from kivy.uix.floatlayout import FloatLayout
from kivy.metrics import dp



class BubbleDecorator(FloatLayout):
    """Add a context menu with a Bubble widget"""

    def __init__(self, **kwargs):
        super(BubbleDecorator, self).__init__(**kwargs)
        self.bubble = None
        self.touch_pos = None

    def add_bubble(self, bubble):
        """Add a bubble menu.

        -----------
            Parameters:
                bubble: the Bubble menu.
        """
        if self.bubble:
            self.remove_widget(self.bubble)
        self.bubble = bubble

    def show_bubble(self, widg):
        '''Shows the bubble menu over the touched widget.'''
        if self.bubble:
            self.remove_widget(self.bubble)
            self.bubble.set_widget(widg)
            if self.touch_pos:
                if self.touch_pos[1] + self.bubble.height + widg.height/2 < self.height:
                    pos_y = self.touch_pos[1]
                    self.bubble.arrow_pos = 'bottom_mid'
                else:
                    pos_y = self.touch_pos[1] - self.bubble.height
                    self.bubble.arrow_pos = 'top_mid'
                self.bubble.pos = (self.bubble.width/2, pos_y)
                self.add_widget(self.bubble)

    def hide_bubble(self, widg):
        '''Remove the bubble menu over the touched widget.'''
        if self.bubble:
            self.remove_widget(self.bubble)
            self.bubble.widg = widg

    def on_touch_down(self, touch):
        '''On touch down it gets the touch position.'''
        if not (touch.is_double_tap or touch.is_mouse_scrolling):
            if self.collide_point(touch.x, touch.y):
                self.touch_pos = touch.pos
            else: 
                # Focus outside the decorator: anything to close?
                pass
        return super().on_touch_down(touch)


class BubbleMenu(Bubble):
    """
    GUI element. Bubble context menu displayed over the current widget.
    Extend it implementing the menu actions.
    """

    def __init__(self, **kwargs):
        super(BubbleMenu, self).__init__(**kwargs)
        self.widget = None
        self.border = (2, 2, 2, 1)
        #self.background_color = (1, 0, 0, .5)  # 50% translucent red
        #self.background_image = 'data/full.png'
        # arrow_image = 'path/to/arrow/image'

    def set_widget(self, widg):
        """Set the local context widget"""
        self.widget = widg

    def close_bubble(self, *args):
        """Remove this menu widget from its parent."""
        self.parent.remove_widget(self)