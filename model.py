# -*- coding: utf-8 -*-
"""
Created on Sat Jul 20 15:35:21 2019

@author: Franco
"""
import csv
import re
from datetime import datetime
from appconstants import item_template, index


def new_item(strict=True, template=item_template, **args):
    """Item builder.
    Return a dictionary with the predefined keys and ''empty'' values.
    If ''**args'' is passed the new keys are added to the predefined.
        Parameters
    ----------
    strict : Default ''True'' only predefined keys are returned.

    **args : Key-value pairs.

        Return a dictionary with the predefined keys.
    """
    item = dict(template)
    if strict:
        for key in args:
            if key in template:
                item[key] = str(args[key])
    else:
        for key in args:
            if 'index' in item:
                raise KeyError('index is a reserved name!')
            else:
                item[key] = str(args[key])
    item = add_index(item)
    return item


def add_index(item, key_list=index):
    '''Add a index text field to the item for the textual search.'''
    item['index'] = ' '.join([str(item[k]).lower() for k in key_list])
    return item


def delete_index(item):
    '''Delete from the item the index entry.'''
    try:
        item = dict(item)
        del item['index']
    except KeyError:
        pass
    return item


def search(items, text, fields=index):
    """
    Find a text in the items list.
    Find a text in the items list, the match is lower case.
        Parameters
    ----------
    items : the list.

    text : the text.

        Returns the list of items where the text was found.
    -------
    """
    if text == '' or None:
        return items
    text = text.lower()
    return [item for item in items if text in item['index']]


def contains(items, value, key, casefold=False):
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
    otherwise None is returned.
    """
    try:
        return [i[key] for i in items].index(value)
    except ValueError:
        return None


def select(items, value, key):
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
    return [i for i in items if str(i[key]).lower() == str(value).lower()]


def iterator(items, key, value):
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


def state(item, key='name', action='', **kvargs):
    '''Return a memento item: a dictionary: 
    - name: the item key
    - timestamp: date and time 
    - action: the user action
    - body: the python object.'''
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
    # Check and repair date: 'created', 'changed'
    d = item['created'].split('/')
    try:
        item['created'] = '{:0>2s}-{:0>2s}-{:0>2s} 08:00:00'.format(
            d[0], d[1], d[2])
    except Exception:
        item['created'] = datetime.now().isoformat(sep=' ', timespec='seconds')
    try:
        item['changed'] = '{:0>2s}-{:0>2s}-{:0>2s} 08:00:00'.format(
            d[0], d[1], d[2])
    except Exception:
        item['changed'] = datetime.now().isoformat(sep=' ', timespec='seconds')

# def replace_items(items, key, old, new):
#     """
#     Replace in the list of items the old value with a the new one.
#     The match is lower case.
#         Parameters
#     ----------
#     items : the list.

#     new : the new value.

#     old : the old value.

#     key : the key.

#     """
#     for i in items:
#         if str(i[key]).lower() == str(old).lower():
#             i[key] = new
#     return items

# def set_fields(widget, fields={}):
#     """Construct: widget.ids.id
#         if the label has id _lab_name the fileld name must be name.
#         """
#     for key, wid in widget.ids.items():
#         if key.startswith('_lab_'):  # label
#             #            wid.text = _(wid.text)
#             pass
#         elif key.startswith('_inp_'):  # inputfield
#             wid.text = fields[key[5:]]
#             pass
#         elif key.startswith('_out_'):  # outputfield
#             wid.text = fields[key[5:]]
#             pass
#         elif key.startswith('_btn_'):  # button
#             pass
#         elif key.startswith('_swi_'):  # switch
#             pass
#         elif key.startswith('_spi_'):  # spinner
#             pass
#         elif key.startswith('_wid_'):  # widget
#             pass
#         elif key.startswith('_scr_'):  # scroll
#             pass
#         elif key.startswith('_prb_'):  # progress bar
#             pass
#         else:
#             pass


if __name__ == '__main__':
    pass
