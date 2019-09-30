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

Builder.load_file('kv/comparator.kv')


class Comparator(BoxLayout):

    def __init__(self, **kwargs):
        super(Comparator, self).__init__(**kwargs)
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

class Comparison(BoxLayout):

    pr_label = ObjectProperty(None)
    pr_last = ObjectProperty(None)
    pr_former = ObjectProperty(None)
    comparable = DictProperty(None)

    def __init__(self, **kwargs):
        super(Comparison, self).__init__(**kwargs)
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
                self.widget.add(field=Comparison, key=k, name=k,
                                last=v*8, former='old_%s' % (v)*18)
            return self.widget

    widget = Comparator()
    TestingApp(widget=widget).run()