from kivy.uix.bubble import Bubble
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.metrics import dp
from recyclelist import *
from bubblemenu import *

manager = """
<Manager>:
	orientation: 'vertical'
	# size: dp(500), dp(800)
	BoxLayout:
		height: self.minimum_height
		size_hint: 1, None
		pos_hint: {'top': 1.0}
		Button:
			size_hint: 1, None
			text: 'Fill List'
			on_release: root.fill_list(*args)
		Button:
			size_hint: 1, None
			text: 'Empty List'
			on_release: root.delete_list(*args)
"""

Builder.load_string(manager)


class Row(ItemAdapter):

    def __init__(self, **kwargs):
        super(Row, self).__init__(**kwargs)
        self.data = {
            'name': SubItem(id='name', width=dp(180)),
            'login': SubItem(id='login', width=dp(180)),
            'url': SubItem(id='url', width=dp(200)),

        }
        for id in self.data:
            self.add_widget(self.data[id])

    def refresh_view_attrs(self, rv, index, data):
        ''' Catch and handle the view changes '''
        self.index = index
        self.data['name'].text = data['name']
        self.data['login'].text = data['login']
        self.data['url'].text = data['url']

        return super().refresh_view_attrs(rv, index, data)


class BubbleList(BubbleDecorator, BoxLayout):
    def __init__(self, **kwargs):
        super(BubbleList, self).__init__(**kwargs)
        self.add_widget(ItemController())
        
        # self.fill_list()

    def fill_list(self, *args):
        data = [{'name': f'{str(x)}',
                 'login': f'login - {str(x)}',
                 'url': f'www.domain_{str(x)}.com'*2,
                 'expire': f'{x}',
                 'old_value': 'Old value',
                 'new_value': 'New Value'}
                for x in range(20)]
        self.data_model.data.extend(data)


class Manager(BoxLayout):

    def __init__(self, **kwargs):
        super(Manager, self).__init__(**kwargs)

        self.container = BubbleDecorator()
        self.controller = ItemController()
        self.controller.viewclass = 'Row'
        self.container.add_widget(self.controller)
        self.add_widget(self.container)


    def fill_list(self, *args):
        data = [{'name': f'{str(x)}',
                 'login': f'login - {str(x)}',
                 'url': f'www.domain_{str(x)}.com'*2,
                 'expire': f'{x}',
                 'old_value': 'Old value',
                 'new_value': 'New Value'}
                for x in range(20)]
        self.controller.data_model.data.extend(data)

    def delete_list(self, *args):
        data = []
        # Clear selections
        self.controller.layout_manager.clear_selection()
        self.controller.data_model.data = data


class TestApp(App):
    def build(self):
        m = Manager()
        # m = BubbleList()
        bubble = BubbleMenu(size=(dp(300), dp(50)), size_hint=(None, None))
        m.container.add_bubble(bubble)
        return m


TestApp().run()
