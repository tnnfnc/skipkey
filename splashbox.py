from kivy.app import App
from kivy.lang.builder import Builder
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
import blinker

Builder.load_string(
    """
<ProgressWheel>:
    icon: self.animated_icon

    canvas:
        Rectangle:
            source: self.icon
            pos: self.x + self.height * 0.1, self.y + self.height * 0.1
            size: self.height * 0.8, self.height * 0.8
  
""")


class ProgressWheel(BoxLayout):

    animated_icon = StringProperty('')

    def __init__(self, **kwargs):
        super(ProgressWheel, self).__init__(**kwargs)
        self.animation = blinker.AnimatedIcon(
            owner=self, attr_name='animated_icon')

    def set_sequential_images(self, images):
        self.animation.set_attr_values(images)

    def startAnimation(self, frame):
        self.animation.start(frame)

    def stopAnimation(self):
        self.animation.reset()




if __name__ == '__main__':

    class TestApp(App):

        animated_icon = StringProperty('')

        def __init__(self, **kwargs):
            super(TestApp, self).__init__(**kwargs)

        def build(self):
            self.title = 'Splash'
            wheel = ProgressWheel()
            wheel.set_sequential_images(['data/icons/progress_1.png', 'data/icons/progress_2.png',
                                         'data/icons/progress_3.png', 'data/icons/progress_4.png', 'data/icons/progress_5.png'])
            wheel.startAnimation(0.07)
            return wheel

    TestApp().run()
