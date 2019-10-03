# -*- coding: utf-8 -*-
"""
Created on Sat Jul 20 15:35:21 2019

@author: Franco
"""
import csv
import re
from datetime import datetime

def new_item(strict=True, **args):
    """
    Item builder.
    Return a dictionary with the predefined keys and ''empty'' values.
    If ''**args'' is passed the new keys are added to the predefined.
        Parameters
    ----------
    strict : Default ''True'' only predefined keys are returned.

    **args : Key-value pairs.

        Return a dictionary with the predefined keys.
    -------
    type :
        Raises
    ------
    Exception
    See Also
    --------

    Examples
    --------
    >>>

    """
    template = {
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
    if strict:
        for key in args:
            if key in template:
                template[key] = str(args[key])
    else:
        for key in args:
            template[key] = str(args[key])

    return template

def search_items(items, text, fields=('name', 'tag', 'description', 'login', 'url', 'email')):
    """
    Find a text in the items list.
    Find a text in the items list, the match is lower case.
        Parameters
    ----------
    items : the list.

    text : the text.

        Returns the list of items where the text was found.
    -------
    type :
        Raises
    ------
    Exception
    See Also
    --------

    Examples
    --------
    >>>

    """
    f_list = []
    if text == '' or None:
        return items
    text = str(text).lower()
    for i, x in enumerate(items):
        if text in ' '.join(str(v) for k, v in x.items() if k in fields).lower():
            f_list.append(i)
    return [items[x] for x in f_list if f_list]


def in_items(items, value, key, casefold=False):
    """
    Return if a value is found in a key.
        Parameters
    ----------
    items : the list.

    value : the value.

    key : the key.

        Return if a value is found for the specified key in the list.
    """
    if casefold:
        value = str(value).casefold().strip()
        return value in [str(i[key]).casefold().strip() for i in items]
    return value in [i[key] for i in items]


def index_of(items, value, key):
    """
    Return the index of the list where a value is found for the specified key.
        Parameters
    ----------
    items : the list.

    value : the value.

    key : the key.

        Return the list index where the value is found for the specified key,
    otherwise -1 is returned.
    """
    try:
        return [i[key] for i in items].index(value)
    except ValueError:
        return -1


def filter_items(items, value, key):
    """
    Search the list for a value in the given key.
    FThe match is lower case.
        Parameters
    ----------
    items : the list.

    value : the value.

    key : the key.

        Returns the list of items where the value was found in the given key.
    """
    l = [i for i in items if str(i[key]).lower() == str(value).lower()]

    return l


def replace_items(items, key, old, new):
    """
    Replace in the list of items the old value with a the new one.
    The match is lower case.
        Parameters
    ----------
    items : the list.

    new : the new value.

    old : the old value.

    key : the key.

    """
    for i in items:
        if str(i[key]).lower() == str(old).lower():
            i[key] = new
    return items


def item_iterator(items, key, value):
    """
    Return the item from the list where the value was found in the key.
    The match is lower case.
        Parameters
    ----------
    items : the list.

    value : the value.

    key : the key.

    """
    for i in items:
        if str(i[key]).lower() == str(value).lower():
            yield i

# History


def memento(item, key='name', action='', **kvargs):
    '''Return a memento item: a dictionary: name, timestamp, action and a
    body containing the item serialized into a json string.'''
    try:
        h = {'name': item['name'],
            'timestamp': datetime.now(),
             'action': action,
             'body': item}
            #  'body': json.dumps(item)}
        for k, v in kvargs.items():
            h[k] = v
    except KeyError:
        h = None
    return h

mapping = {
    'Access': 'name',
    'url': 'url',
    'User Name': 'login',
    'Contact e-mail': 'email',
    'Description': 'description',
    'Category': 'tag',
    'Created on': 'created',
    'Password': 'password'}
#      'color': ''
#     'changed': '',
#     'auto': '',
#     'length': '',
#     'letters': '',
#     'numbers': '',
#     'symbols': '',
#     'history': ''
# }


def import_csv(file, delimiter='\t', lineterminator='\r\n', mapping=None):
    items = []
    with open(file, newline='') as csvfile:
        reader = csv.DictReader(
            csvfile, delimiter='\t', lineterminator=lineterminator, quoting=csv.QUOTE_NONE)
        if mapping:
            for row in reader:
                d = {mapping[k]: row[k] for k in mapping.keys()}
                items.append(d)
        else:
            for row in reader:
                d = {k: row[k] for k in row.keys()}
                items.append(d)
    return items


def export_csv(file, items, fieldnames=[], delimiter='\t', lineterminator='\r\n'):
    if len(items) > 0:
        fieldnames = items[0].keys()
    with open(file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, delimiter=delimiter, lineterminator=lineterminator,
                                quoting=csv.QUOTE_MINIMAL, fieldnames=fieldnames, escapechar=None)
        writer.writeheader()
        log = []
        for item in items:
            try:
                writer.writerow(item)
            except Exception as e:
                log.append('Error:{} at {}'.format(e.args, item))
                raise

    return True


def normalize(item):
    if item['email'] == '' and re.search(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", item['login']):
        item['email'] = item['login']
    if item['login'] == '' and item['email']:
        item['login'] = item['email']
    if item['url'] == '':
        item['url'] = item['name']


def set_fields(widget, fields={}):
    """Construct: widget.ids.id
        if the label has id _lab_name the fileld name must be name.
        """
    for key, wid in widget.ids.items():
        if key.startswith('_lab_'): #label
#            wid.text = _(wid.text)
            pass
        elif key.startswith('_inp_'): #inputfield
            wid.text = fields[key[5:]]
            pass
        elif key.startswith('_out_'): #outputfield
            wid.text = fields[key[5:]]
            pass
        elif key.startswith('_btn_'): #button
            pass
        elif key.startswith('_swi_'): #switch
            pass
        elif key.startswith('_spi_'): #spinner
            pass
        elif key.startswith('_wid_'): #widget
            pass
        elif key.startswith('_scr_'): #scroll
            pass
        elif key.startswith('_prb_'): #progress bar
            pass
        else:
            pass



if __name__ == '__main__':
    items = []
    items.extend([
        new_item(name='item 7', tag='Free'),
        new_item(name='item 2', tag='Free'),
        new_item(name='item 3', tag='Web'),
        new_item(name='item 5', tag='Free'),
        new_item(name='item 4', tag='Web'),
        new_item(name='item 6', tag='Free'),
        new_item(name='item 1', tag='Gov'),
        new_item(name='item 8', tag='Gov')]
    )

    print(f'\n --------> search items: \n {search_items(items, "ree")}')

    print(f"\n --------> in items: \n {in_items(items, 'item 6', 'name')}")

    print(f"\n --------> in items casefold: \n {in_items(items, 'itEm 6', 'name', casefold=True)}")

    print(f"\n --------> in items casefold: \n {in_items(items, 'itEm 6', 'name')}")

    print(
        f"\n --------> index of items: \n {index_of(items, 'item 6', 'name')}")

    print(f"\n --------> filter items: \n {filter_items(items, 'Gov', 'tag')}")

    print(
        f"\n --------> replace_items: \n {replace_items(items, 'tag', 'Gov', 'Replaced(Gov)')}")

    for i in item_iterator(items, 'tag', 'Replaced(Gov)'):
        i['tag'] = 'Replaced(Replaced(Gov))'

    print(f"\n --------> item_iterator : \n {items}")

    items.sort(key=lambda k: k['name'])
    print(f"sorted items: \n {items}")
    h = []
    for i in items:
        h[0:0] = [memento(i, father='Franco', mother='Maria',
                          city='Mezzocorona')]

    print(f"Amplified history: ")
    for i in h:
        print(i)

    # print(f"Mementos by key: ")
    # l = mementos_by_key(h)
    # for i in l.keys():
    #     print(f'{i}: {l[i]}')

    # print(f"Parse memento: ")
    # for i in l:
    #     print(f'{parse_memento_by_key(l[i])}')

    file = ''
    path = ''
    if file:
        f = f'{path}{file}'
        items = import_csv(f)
        items = import_csv(f, mapping=mapping)
        print(items)
