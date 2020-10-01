from skipkey import SkipKeyApp

search_fields = ('name',
                 'tag',
                 'description',
                 'login',
                 'url',
                 'email')

item_template = {
    'name': '',  # new name
    'url': '',  # Check valid url
    'login': '',  # Any string
    'email': '',  # @-mail
    'description': '',  # Any string
    'tag': '',  # Any string
    'color': '',  # Basic colors as string
    'created': '',  # Date
    'changed': '',  # Date
    'auto': '',  # True, False=user
    'length': '',  # Integer
    'letters': '',  # True / False
    'numbers': '',  # At least [0 length]
    'symbols': '',  # At least [0 length]
    'password': '',  # User encrypted password or salt Base64 encoded
    'history': ''  # Record history - not yet managed
}

SkipKeyApp(search_fields=search_fields, item_template=item_template).run()