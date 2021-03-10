from skipkey import SkipKeyApp

search_fields = ('name',
                 'tag',
                 'description',
                 'login',
                 'url',
                 'email')

SkipKeyApp(search_fields=search_fields).run()
