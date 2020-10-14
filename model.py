# -*- coding: utf-8 -*-
"""
Created on Sat Jul 20 15:35:21 2019

@author: Franco
"""
import threading
import cipherfachade
import base64
import json
import csv
import re
from datetime import datetime, timedelta



export_fieldnames =  [
    'name',
    'url',
    'login',
    'email',
    'description',
    'tag',
    'color',
    'created',
    'changed',
    'password_0',
    'password_1',
    'password_2',
    'history'
]

# json_item_tmp = json.dumps(item_template)

def new_item(strict=True):
    """Item builder.
    Return a dictionary from the provided template.

    Item keys are updated from **args key-value pairs.

    ----------
        Parameters

    **args : Key-value pairs.

    ----------
        Return

        Return a dictionary with the predefined keys.
    """
    secret = {
    'label': '',
    'auto': 'True',
    'length': '',
    'letters': '',
    'symbols': '',
    'numbers': '',
    'password': ''}

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
        'secrets': [dict(secret), dict(secret), dict(secret)],  # List of secrets
        'history': ''  # Record history - not yet managed
    }
    return dict(item_template)
    # if template:
    #     item = json.loads(template)
    # else:
    #     item = {}
    # return item

def copy(item):
    """Deep copy

    Args:
        item (dict): source data

    Returns:
        dict: a data deep copy
    """
    acopy = new_item()
    secrets = acopy['secrets']
    acopy.update(item)
    for i, secret in enumerate(item['secrets']):
        secrets[i].update(secret)
    acopy['secrets'] = secrets
    return acopy

def time_left(item, lifetime):
    """Return the password validity time left from today, assuming a lifetime.
    
    If the password is still valid it returns a positive number, else it returns
    the negative number of days from its expiration.
    """
    today = datetime.now()
    try:
        changed = None
        if 'changed' in item:
            changed = datetime.fromisoformat(item['changed'])
        elif 'created' in item:
            changed = datetime.fromisoformat(item['created'])
        else:
            return 0
        expire_date = changed + timedelta(days=lifetime)
        return (expire_date - today).days
    except Exception:
        pass
    return 0


def elapsed(item):
    """Return elapsed days since password was set."""
    today = datetime.now()
    try:
        changed = None
        if 'changed' in item:
            changed = datetime.fromisoformat(item['changed'])
        elif 'created' in item:
            changed = datetime.fromisoformat(item['created'])
        else:
            return 0
        return (today - changed).days
    except Exception:
        return 0


def add_index(key_list):
    '''Add a index text field to the item for the textual search.'''
    def f(item):
        item['index'] = ' '.join([str(item[k]).lower() for k in key_list])
        return item
    return f


def purge(item):
    """Return a new item purged of the internal data.

    The purge also performs a deep copy of the item.

    Args:
        item (dict): account item.

    Returns:
        dict: account item.
    """
    try:
        item = copy(item)
        del item['index']
        del item['object_id']
        
    except KeyError:
        pass
    return item

def is_equal(a, b):
    """Return a = b.

    Args:

    - a (dict): access data
    - b (dict): access data

    Returns:

    bool: True if a = b
    """
    isequal = True
    for k in a:
        if isinstance(a[k], list):
            for i in range(0, len(a[k])):
                if not is_equal(a[k][i], b[k][i]):
                    isequal = False
                    break
        elif a[k] != b[k]:
            isequal = False
            break
    return isequal


def password_changed(a, b):
    """Return true when al least one password of a is different from b.

    Args:

    - a (dict): access data
    - b (dict): access data

    Returns:

    bool: true when al least one password of a is different from b.
    """
    for i in range(0, len(a['secrets'])):
        if a['secrets'][i]['password'] != b['secrets'][i]['password']:
            return True
    return False

def search(items, text):
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


def state_object(state):
    '''Return a memento item: a dictionary:
    '''
    return state['body']


def import_csv(file, delimiter='\t', lineterminator='\r\n', mapping=None):
    items = []
    with open(file, newline='') as csvfile:
        reader = csv.DictReader(
            csvfile, delimiter='\t', 
            lineterminator=lineterminator, 
            strict=True, 
            # quoting=csv.QUOTE_NONE,
            #
            quotechar='',
            quoting=csv.QUOTE_NONE,
            doublequote=False,
            escapechar=None)
        if mapping:
            for row in reader:
                d = {}
                for k in mapping.keys():
                    if mapping[k]:
                        d[k] = row[mapping[k]]
                items.append(d)
        else:
            for row in reader:
                d = {k: row[k] for k in row.keys()}
                items.append(d)
    return items


def export_csv(file, items, fieldnames=[], delimiter='\t', lineterminator='\r\n'):
    if len(fieldnames) == 0 and len(items) > 0:
        raise Exception('field names are not specified')
    with open(file, 'w', newline='') as csvfile:
        # writer = csv.DictWriter(csvfile, delimiter=delimiter, lineterminator=lineterminator,
        #                         quoting=csv.QUOTE_MINIMAL, fieldnames=fieldnames, escapechar=None)
        writer = csv.DictWriter(csvfile, 
                                delimiter=delimiter, 
                                fieldnames=fieldnames,
                                quotechar='',
                                quoting=csv.QUOTE_NONE,
                                doublequote=False,
                                escapechar='`')
        writer.writeheader()
        log = []
        for item in items:
            try:
                writer.writerow(item)
            except Exception as e:
                log.append('Error:{} at {}'.format(e.args, item))
                raise

    return log

def check_date(date):
    """Check a date against the format:
    YYYY\<sep\>MM\<sep\>DD and hh\<sep\>mm\<sep\>ss where \<sep\> can
    be any character.

    Args:
        date (str): String containing a date.

    Returns:
        str: a date string in isoformat 'YYYY-MM-DD hh:mm:ss'
    """
    pattern = r'(\d{4}.\d{2}.\d{2})+\D*(\d{2}.\d{2}.\d{2})*'
    match = re.search(pattern, date)
    rdate = date
    try:
        if match.group() and match.group(1):
            ymd = match.group(1)
            rdate = ymd[0:4] + '-' + ymd[5:7] + '-' + ymd[8:10]
            if match.group(2):
                hms = match.group(2)
                rdate = rdate + ' ' + hms[0:2] + ':' + hms[3:5] + ':' + hms[6:8]
            else:
                rdate = rdate + ' ' + '08:00:00'
        else: 
            rdate = datetime.now().isoformat(sep=' ', timespec='seconds')
    except Exception:
        rdate = datetime.now().isoformat(sep=' ', timespec='seconds')
    return rdate


def normalize(item):
    if item['email'] == '' and re.search(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", item['login']):
        item['email'] = item['login']
    if item['login'] == '' and item['email']:
        item['login'] = item['email']
    if item['url'] == '':
        item['url'] = item['name']
    # Check and repair date: 'created', 'changed'
    item['created'] = check_date(item.get('created', ''))
    item['changed'] = check_date(item.get('changed', ''))
    return True



class SkipKey():
    """
    SkipKey Application Logic. 
    """
    DELETE = 'delete'
    UPDATE = 'update'
    APPEND = 'append'

    def __init__(self, search_fields, **kwargs):
        # Data model - interface
        self.items = []
        # Mementos Data model - interface
        self.history = []
        # Current file - interface
        self.file = None
        # Secret key wrapper - interface
        self.keywrapper = None
        # Session key - interface
        self.session_key = None
        # Sectret seed wrapper - interface
        self.seedwrapper = None
        # Session seed - interface
        self.session_seed = None
        # Cipher / Decipher - interface
        self.cipher_fachade = None
        # Crypto parameters - interface
        self.cryptod = None
        # Search in the content of keys
        self.search_fields = search_fields

       # interface

    def open(self, file, passwd, seed):
        """
        Open the file and prepare the records. Raises excepions."""
        # try:
        with open(file, mode='r') as f:
            cryptod = json.load(f)
        if self.secure(cryptod=cryptod, passwd=passwd, seed=seed):
            self.file = file
            self.items = self.cipher_fachade.decrypt(
                cryptod,
                self.keywrapper.unwrap(self.session_key)
            )
            self.items.sort(key=lambda x: str.lower(x['name']))
            #
            list(map(add_index(self.search_fields), self.items))
            return True
        else:
            raise ValueError('Security initialization trouble')
        return False

    # interface

    def delete_item(self, item, history=True):
        """
        Delete an item from the item list.
        """
        index = index_of(self.items, item['name'], 'name')
        if index == None:  # Delete
            raise ValueError('Item "%s" not found' % (item['name']))
        else:
            old = self.items.pop(index)
            if history:
                self.add_history(new=None, old=old, action=SkipKey.DELETE)
            self.items.sort(key=lambda k: str(k['name']).lower())
        return True

    # interface
    def save_item(self, item, history=True):
        """
        Add a new item or update an existing one.

        The item identifier is its name, so it is not possible to have
        more than one item with the same name.
        The changed date is updated only if password was changed.
        """
        add_index(self.search_fields)(item)
        index = index_of(self.items, item['name'], 'name')
        if index == None: # Append
            item['created'] = check_date(item.get('created', ''))
            item['changed'] = check_date(item.get('changed', ''))
            # if item['created'] == '':
            #     item['created'] = datetime.now().isoformat(
            #         sep=' ', timespec='seconds')
            # if item['changed'] == '':
            #     item['changed'] = datetime.now().isoformat(
            #         sep=' ', timespec='seconds')
            self.items.append(item)
            if history:
                self.add_history(new=None, old=item, action=SkipKey.APPEND)
        else: # Update
            if history:
                old = self.items[index]
                self.add_history(new=item, old=old, action=SkipKey.UPDATE)
            # Update the changed only if password was changed
            # if self.items[index]['password'] != item['password']:
            if password_changed(self.items[index], item):
                item['changed'] = datetime.now().isoformat(
                    sep=' ', timespec='seconds')
            self.items[index] = item
        self.items.sort(key=lambda k: str(k['name']).lower())
        return True

    # interface
    def add_history(self, new, old, action=''):
        """
        History Data model: for the present the history is a back up of
        the data model.
        {'name': item_name, 'changed': timestamp, 'item': item_json_dump}
        """
        if new != old:
            self.history.append(state(item=old, action=action))

    # interface
    def encrypt(self, text):
        """
        Encrypt a password using the security algorithm and seed.
            Parameters
        ----------
            text : text to encrypt

            Returns
        ----------
            cipher text as base64 encoded utf-8 string
        -------
        type :
            Raises Exceptions
        ------
        Exception
        """
        # Get the seed:
        # try:
        key = self.seedwrapper.unwrap(self.session_seed)
        cryptod = self.cipher_fachade.encrypt(text, self.cryptod, key)
        # encoding='utf-8'
        r = bytes(json.dumps(cryptod), encoding='utf-8')
        r = str(base64.b64encode(r), encoding='utf-8')
        return r

    # interface
    def decrypt(self, text):
        """
        Decrypt a text using the security algorithm and seed.
            Parameters
        ----------
            text : text to encrypt

            Returns
        ----------
            plain object
        -------
        Exceptions :
            Raises Exceptions at decryption failure.
        """
        # Get the seed:
        # try:
        cryptod = json.loads(str(base64.b64decode(text), encoding='utf-8'))
        key = self.seedwrapper.unwrap(self.session_seed)
        t = self.cipher_fachade.decrypt(cryptod, key)
        return t
        # except Exception as e:
        #     message(_('Decipher'), *e.args, 'e')

    # interface
    def generate(self, **kwargs):
        """
        Generate a password.
        Generate a password and update the strenght.
            Parameters
        ----------
         length : password length.

         letters : letters are allowed: True/False.

         numbers : a number, numbers allowed at least.

         symbols : a number, symbols allowed at least.

            Returns
        ---------
          password

          seed

        ------
        Exception
        """

        try:
            length =  kwargs.get('length', 0)
            letters = kwargs.get('letters', 0)
            numbers = kwargs.get('numbers', 0)
            symbols = kwargs.get('symbols', 0)
            if letters or numbers or symbols and length:
                pattern = cipherfachade.Pattern(
                    letters=letters,
                    numbers=numbers,
                    symbols=symbols,
                    length=length
                )
                seed = self.seedwrapper.unwrap(self.session_seed)
                pwd, salt = self.cipher_fachade.secret(
                    seed, self.cryptod['iterations'], pattern)
                # seed, ITERATIONS, pattern)
                return pwd, salt
            else:
                raise ValueError('The password preferences are missing')
        except Exception as e:
            raise ValueError(e)

    # interface
    def show(self, secret):
        """
        Show a generated password and its strenght.

            Parameters

            secret : the secret.

        ----------

            Returns

        - password

        -------
        
        Exception :
            Raises Exceptions
        """
        length =  secret.get('length', 0)
        letters = secret.get('letters', 0)
        numbers = secret.get('numbers', 0)
        symbols = secret.get('symbols', 0)

        pattern = cipherfachade.Pattern(
            letters=letters,
            numbers=numbers,
            symbols=symbols,
            length=length
        )
        seed = self.seedwrapper.unwrap(self.session_seed)
        salt = base64.b64decode(secret['password'])
        p = self.cipher_fachade.password(
            seed, salt, self.cryptod['iterations'], pattern)
        return p

    # interface
    def secure(self, cryptod, passwd, seed):
        """
        Turn the security on (call once)."""
        # try:
        self.cipher_fachade = cipherfachade.CipherFachade()
        self.keywrapper = cipherfachade.KeyWrapper()
        self.seedwrapper = cipherfachade.KeyWrapper()
        # Wrapping secret key
        key = self.cipher_fachade.key_derivation_function(
            cryptod).derive(passwd)
        self.session_key = self.keywrapper.wrap(key)
        # Wrapping secret seed
        seed = self.cipher_fachade.key_derivation_function(
            cryptod).derive(seed)
        self.session_seed = self.seedwrapper.wrap(seed)
        # security settings
        self.cryptod = cryptod
        return True

    # interface
    def unsecure(self):
        """Turn the security off."""
        self.cipher_fachade = None
        self.session_key = None
        self.session_seed = None
        self.keywrapper = None
        self.seedwrapper = None
        self.cryptod = None
        return True

    # interface
    def initialize(self):
        """Initializes app context"""
        self.unsecure()
        # Data model
        self.items = []
        # Current file
        self.file = None
        # Mementos Data model
        self.history = []
        # Keeps recent files
        self.files
        return True

    # interface
    def save(self, file, force=False):
        """
        Save items into a file.

        The file is saved if any changes was made, otherwise return
        without saving. If the optional parameter force is True, then
        the file is saved even if no changes were made.
        The file is always encrypted.
        Parameters
        ----------
        - file :
        the file path.
        - force :
        force the saving.

        Returns
        -------
        True :
        if the file was saved, otherwise returns False.
        """
        if file and self.session_key and (len(self.history) > 0 or force):
            # try:
            items = list(map(purge, self.items))
            data = self.cipher_fachade.encrypt(
                items,
                cryptod=self.cryptod,
                secret=self.keywrapper.unwrap(self.session_key)
            )
            with open(file, mode='w') as f:
                json.dump(data, f)
            return True
        # Nothing to save
        return False

    # interface
    def copy(self, file, cryptod, passwd, seed, thread=False):
        """
        Save items into a file.
        The file is encrypted.
            Parameters
        ----------
        file : the file path.

        cryptod : the cryprographic stuff for generating the secret key.

            Returns
        -------
        type :
            Raises
        ------
        Exception
        """
        if not thread:
            kwargs = {'file': file, 'cryptod': cryptod,
                      'passwd': passwd, 'seed': seed, 'thread': True}
            copy_thread = threading.Thread(target=self.copy, kwargs=kwargs)
            copy_thread.start()
            return True

        # Before copying all password must be encrypted
        # with the new key, and all generated ones must be
        # converted in user typed
        # Should be done in another thread
        items_copy = list(map(purge, self.items[0:]))
        # try:
        # Get the seed:
        try:
            local_cf = cipherfachade.CipherFachade()
            key = local_cf.key_derivation_function(
                cryptod).derive(passwd)
            seed = local_cf.key_derivation_function(
                cryptod).derive(seed)
            pwd = ''
            for item in items_copy:
                for secret in item['secrets']:
                    if secret['auto'] == 'True':
                        pwd = self.show(secret)
                        secret['auto'] = 'False'
                        secret['length'] = ''
                        secret['letters'] = ''
                        secret['numbers'] = ''
                        secret['symbols'] = ''
                    elif secret['auto'] == 'False':
                        pwd = self.decrypt(secret['password'])
                    r = local_cf.encrypt(pwd, cryptod, seed)
                    r = bytes(json.dumps(r), encoding='utf-8')
                    r = str(base64.b64encode(r), encoding='utf-8')
                    secret['password'] = r
            #
            data = local_cf.encrypt(
                items_copy, cryptod=cryptod, secret=key)
            local_cf = None
            with open(file, mode='w') as f:
                json.dump(data, f)
        except Exception as e:
            raise Exception(e)
        return True

    # interface
    def export(self, file):
        items_csv = []
        for i in self.items[:]:
            item = purge(i)
            for i, secret in enumerate(item['secrets']):
                if secret.get('password', '') == '':
                    continue
                if secret['auto'] == 'True':
                    secret['password'] = self.show(secret)
                elif secret['auto'] == 'False':
                    secret['password'] = self.decrypt(secret['password'])
                item[f'password_{i}'] = secret['password']

            del item['secrets']
            item['description'] = item['description'].replace('\r', '').replace('\n', ' ').replace('\t', '    ')
            items_csv.append(item)
        #
        
        log = export_csv(file=file, items=items_csv, 
                         fieldnames=export_fieldnames, 
                         delimiter='\t', lineterminator='\r\n')
        return log


    # interface
    def import_csv(self, file, mapping):
        """Import the '.csv' into current file. Once the mapping is applied,
        new accounts are formed and appended to the current list.
        New records are normalized by adding calculated values in place of
        missing information. Nevertheless errors may occurs."""
        try:
            items = import_csv(file=file, delimiter='\t', mapping=mapping)
            # Add default keys
            items_ = []
            for item in items:
                ritem = new_item()
                ritem.update(item)
                for i, secret in enumerate(ritem['secrets']):
                    if item.get(f'password_{i}', '') != '':
                        secret['label'] =  mapping.get(f'password_{i}', 'password')
                        secret['password'] = self.encrypt(item[f'password_{i}'])
                        secret['auto'] = 'False'
                        del ritem[f'password_{i}']
                normalize(ritem)
                items_.append(ritem)
        except Exception:
            raise
        return items_