"""SkipKey: a help to password management"""
import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.lang.builder import Builder
from kivy.properties import ObjectProperty
from kivy.properties import DictProperty
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Line
from kivy.metrics import dp

kivy.require('1.11.0')  # Current kivy version

Builder.load_file('data/kv/fields.kv')


class FieldsWidget(BoxLayout):

    def __init__(self, **kwargs):
        super(FieldsWidget, self).__init__(**kwargs)
        self._fields = {}
        self.container = BoxLayout(orientation='vertical', size_hint_y=None)
        scroll_view = ScrollView()
        scroll_view.add_widget(self.container)
        self.add_widget(scroll_view)
        self.container.bind(minimum_height=self.container.setter('height'))

    def add(self, key, field, **kwargs):
        f = field(comparable=kwargs)
        self.container.add_widget(f)
        self._fields[key] = f
        return self

    @property
    def fields(self):
        return self._fields

    def clear(self):
        '''Remove items from the list'''
        self.container.clear_widgets()
        self._fields = {}
        return self

class FieldCompare(BoxLayout):

    label = ObjectProperty(None)
    value = ObjectProperty(None)
    change = ObjectProperty(None)
    comparable = DictProperty(None)

    def __init__(self, **kwargs):
        super(FieldCompare, self).__init__(**kwargs)
        self.compare()

    def compare(self, *args):
        name = last = former = ''
        if 'name' in self.comparable:
            name = self.comparable['name']
        if 'last' in self.comparable:
            last = self.comparable['last']
        if 'former' in self.comparable:
            former = self.comparable['former']

        name = name if name else ' - '
        last = last if last else ' - '
        former = former if former else ' - '
        if last != former:
            self.value.markup = True
            self.change.markup = True
            last = '[color=ff3333]%s[/color]' % (last)
            former = '[color=33FF33]%s[/color]' % (former)
        else:
            self.value.markup = False
            self.change.markup = False

        self.label.text = name
        self.value.text = last
        self.change.text = former


# class FieldCompare2(BoxLayout):

#     # pr_label = ObjectProperty(None)
#     # pr_value = ObjectProperty(None)
#     # pr_change = ObjectProperty(None)
#     comparable = DictProperty(None)

#     def __init__(self, **kwargs):
#         super(FieldCompare2, self).__init__(**kwargs)
#         self.add_widget(self.label)
#         self.add_widget(self.value)
#         self.add_widget(self.change)
#         with self.canvas:
#             self.line=Line(points=(self.x, self.y, self.x + self.width, self.y),
#                  width=2, joint='miter')


#     def redraw(self, *args):
#         # Line(points=(self.x, self.y, self.x + self.width, self.y), width=2, joint='miter')
#         with self.canvas:
#             self.line(points=(self.x, self.y, self.x + self.width, self.y),
#                  width=0.8, joint='miter')

#     def resize_label(self, *args):
#         '''Resize the labels text_size'''
#         s = (self.width - self.label.width)/2, None
#         self.value.text_size = s
#         self.change.text_size = s
#         self.value.size = self.value.texture_size
#         self.change.size = self.change.texture_size

#     def set_height(self, *args):
#         self.height = max(self.value.height, self.change.height)

#     def on_comparable(self, *args):
#         self.orientation = 'horizontal'
#         self.size_hint_y = None
#         self.label = Label(size_hint_x=None, width=dp(120), halign='left', valign='center')
#         self.value = Label()
#         self.change = Label()
#         self.bind(width=self.resize_label)
#         self.value.bind(height=self.set_height)
#         self.change.bind(height=self.set_height)
#         self.label.bind(size=self.label.setter('text_size'))
#         self.bind(pos=self.redraw, size=self.redraw)

#         name = last = former = ''
#         if 'name' in self.comparable:
#             name = self.comparable['name']
#         if 'last' in self.comparable:
#             last = self.comparable['last']
#         if 'former' in self.comparable:
#             former = self.comparable['former']

#         name = name if name else ' - '
#         last = last if last else ' - '
#         former = former if former else ' - '
#         if last != former:
#             self.value.markup = True
#             self.change.markup = True
#             last = '[color=ff3333]%s[/color]' % (last)
#             former = '[color=33FF33]%s[/color]' % (former)
#         else:
#             self.value.markup = False
#             self.change.markup = False

#         self.label.text = name
#         self.value.text = last
#         self.change.text = former



if __name__ == '__main__':

    fields = {'password': 'secret',
              'home': 'Boston',
              'mother': 'Clara',
              'father': 'Unknown',
              'sister': 'Paula',
              'brother': 'Jim',
              'son': '',
              }

    class TestingApp(App):

        def __init__(self, widget, **kwargs):
            super(TestingApp, self).__init__(**kwargs)
            self.widget = widget

        def build(self):
            for k, v in fields.items():
                self.widget.add(field=FieldCompare, key=k, name=k,
                                last=v*8, former='old_%s' % (v)*18)
            return self.widget

    widget = FieldsWidget()
    TestingApp(widget=widget).run()
