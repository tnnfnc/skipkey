'''Crypto fachade...'''
import cryptography.hazmat.primitives.keywrap as keywrap
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
import os
import json
import gzip as gzip
import base64

# Translations


def _(x):
    return x


def init_symbols():
    """Return a tuple of symbols characters from exadecimal
    ranges [0x21-0x2f], [0x3a-0x40], [0x5b-0x5f]."""
    symbols = []
    # Symbols
    for hex in range(int('21', base=16), int('30', base=16)):
        symbols.append(chr(hex))
    for hex in range(int('3a', base=16), int('41', base=16)):
        symbols.append(chr(hex))
    for hex in range(int('5b', base=16), int('60', base=16)):
        symbols.append(chr(hex))
    return tuple(symbols)

# Digit
def init_numbers():
    """Return a tuple of numbers digit from exadecimal
    ranges [0x30-0x39]."""
    numbers = []
    for hex in range(int('30', base=16), int('3a', base=16)):
        numbers.append(chr(hex))
    return tuple(numbers)


# Upper
def init_letters():
    """Return a tuple of lowercase and uppercase letters
    from exadecimal ranges [0x41-0x5a], [0x61-0x7a]."""
    letters = []
    for hex in range(int('41', base=16), int('5b', base=16)):
        letters.append(chr(hex))
    # Lower
    for hex in range(int('61', base=16), int('7b', base=16)):
        letters.append(chr(hex))
    return tuple(letters)


def get_cryptografy_parameters(**kwargs):
    """Return a dictionary of default cryptographic parameters.

    Existing keys are updated from optional kwargs.

    --------
    """
    d = {'algorithm': 'AES',
         'mode': 'CBC',
         'keysize': 256,
         'pbkdf': 'PBKDF2HMAC',
         'hash': 'SHA256',
         'length': int(256/8),
         'iterations': 100,
         'salt': str(base64.b64encode(os.urandom(32)), encoding='utf-8')}
    if kwargs:
        for k in kwargs:
            d[k] = kwargs[k]
    return d


# def encrypt_by_key(cryptod, password, seed, items, key):
#     '''Encrypt in place the content of items witk the key specified'''
#     try:
#         local_cf = CipherFachade()
#         # key = local_cf.key_derivation_function(
#         #     cryptod).derive(password)
#         seed = local_cf.key_derivation_function(
#             cryptod).derive(seed)
#         for item in items:
#             r = local_cf.encrypt(item[key], cryptod, seed)
#             r = bytes(json.dumps(r), encoding='utf-8')
#             r = str(base64.b64encode(r), encoding='utf-8')
#             item[key] = r
#         return items
#     except Exception as e:
#         return None


def cipherdata(cryptopars, ciphervalue='', iv='', **kwargs):
    """
    Cryptographic envelop containing key derivation materials.

    Return a dictionary with the predefined keys.
    If ''**args'' is passed the new keys are added to the predefined.

    ----------
        Parameters
    strict : Default ''True'' only predefined keys are returned.

    **args : Key-value pairs for custom further infos

    -------
        Return
    a dictionary with the predefined keys.
    """
    d = dict(cryptopars)
    d['ciphervalue'] = ciphervalue
    d['iv'] = iv
    # Add further custom data
    if kwargs:
        for key in kwargs:
            d[key] = str(kwargs[key])
    return d


def cipher_algorithms():
    '''Advanced Encryption Standard is a block cipher standardized by NIST;
    it is fast and cryptographically strong. Camellia is a block cipher
    approved for use by CRYPTREC and ISO/IEC. It is considered to have
    comparable security and performance to AES but is not as widely studied
    or deployed.

    CAST5 (also known as CAST-128) is a block cipher approved for use in
    the Canadian government by the Communications Security Establishment.

    SEED is a block cipher developed by the Korea Information Security
    Agency (KISA).
    It is defined in RFC 4269 and is used broadly throughout South Korean
    industry.'''
    return {'AES': _('Advanced Encryption Standard'),
            'Camellia': _('Camellia is a block cipher approved for use by CRYPTREC and ISO/IEC.'),
            'CAST5': _('CAST5 (also known as CAST-128) is a block cipher approved for use in the Canadian government.'),
            'SEED': _('SEED is a block cipher developed by the Korea Information Security Agency (KISA).')
            }


def key_derivators():
    return {'PBKDF2HMAC': _('Password Based Key Derivation Function 2, is typically used for deriving a cryptographic key from a password.'),
            'HKDF': _('HMAC-based Extract-and-Expand Key Derivation Function, is suitable for deriving keys of a fixed size.'),
            }


SYMBOLS = init_symbols()
NUMBERS = init_numbers()
LETTERS = init_letters()


class PatternException(Exception):
    pass

class Schema():

    SEP = ','

    def __init__(self, schema):
        """[summary]

        Args:
            schema ([type]): [description]

        Raises:
            PatternException: [description]
        """
        if schema:
            if isinstance(schema, dict):
                self.auto = schema.get('auto', '')
                self.lenght = schema.get('lenght', '')
                self.letters = schema.get('letters', '')
                self.numbers = schema.get('numbers', '')
                self.symbols = schema.get('symbols', '')
                self.gliphs = schema.get('gliphs', '')
            elif isinstance(schema, list) or isinstance(schema, tuple):
                self.auto = schema[0]
                self.lenght = schema[1]
                self.letters = schema[2]
                self.numbers = schema[3]
                self.symbols = schema[4]
                self.gliphs = schema[5]
            elif isinstance(schema, str):
                self._pattern = schema
        else:
            self._pattern = 'True,0,True,0,0,""'

        if not self.check(self._pattern):
            raise PatternException(f'Schema not valid: {schema}')

    @staticmethod
    def check(pattern):
        if pattern:
            split = pattern.split(Schema.SEP)
            try:
                if str(split[0]) in ('True', 'False') and\
                    str(split[2]) in ('True', 'False') and\
                    int(split[1]) > -1 and int(split[3]) > -1 and\
                    int(split[4]) > -1 and isinstance(split[5], str):
                    return True
                return False
            except Exception:
                return False
        return False

    @property
    def auto(self):
        return self._pattern.split(self.SEP)[0]

    @property
    def lenght(self):
        return self._pattern.split(self.SEP)[1]

    @property
    def letters(self):
        return self._pattern.split(self.SEP)[2]

    @property
    def numbers(self):
        return self._pattern.split(self.SEP)[3]

    @property
    def symbols(self):
        return self._pattern.split(self.SEP)[4]

    @property
    def gliphs(self):
        return self._pattern.split(self.SEP)[5]

    @auto.setter
    def auto(self, value : bool):
        self._encode(value, 1)

    @lenght.setter
    def lenght(self, value : int):
        self._encode(value, 2)

    @letters.setter
    def letters(self, value : bool):
        self._encode(value, 3)

    @numbers.setter
    def numbers(self, value : int):
        self._encode(value, 4)

    @symbols.setter
    def symbols(self, value : int):
        self._encode(value, 5)

    @gliphs.setter
    def gliphs(self, value : str):
        self._encode(value, 6)

    def _encode(self, value, maxsplit):
        split = self._pattern.split(self.SEP, maxsplit)
        split[maxsplit - 1] = str(value)
        self._pattern = self.SEP.join(split)

    @property
    def schema(self):
        return self._pattern


class Pattern():
    """Define the pattern that a token must be compliant to.
    """

    def __init__(self, letters, numbers, symbols, length, *args, **kwargs):
        if letters is None or letters == '' or False:
            letters = 0
        else:
            letters = 1
        if numbers is None or numbers == '':
            numbers = 0
        if symbols is None or symbols == '':
            symbols = 0
        if length is None or symbols == '':
            length = 0
        # try:
        self.numbers = int(numbers)
        self.symbols = int(symbols)
        self.letters = int(letters)
        self._length = int(length)

        self._gliphs = []
        if self.letters > 0:
            self._gliphs.extend(LETTERS)
        if self.numbers > 0:
            self._gliphs.extend(NUMBERS)
        if self.symbols > 0:
            self._gliphs.extend(SYMBOLS)
        if self.numbers + self.letters + self.symbols == 0:
            raise ValueError(_('Inconsistent pattern of zeros gliphs'))

    @property
    def gliphs(self):
        """Return the list of allowed textual symbols."""
        return self._gliphs

    @property
    def length(self):
        """Lenght"""
        return self._length

    def check(self, text):
        """Check the text contains at least as many allowed
        textual symbols as set."""
        lt = s = n = 0
        result = False
        for g in text:
            if g in LETTERS and lt < self.letters:
                lt += 1
            if g in NUMBERS and n < self.numbers:
                n += 1
            if g in SYMBOLS and s < self.symbols:
                s += 1
            if n == self.numbers and s == self.symbols and lt == self.letters:
                result = True
                break
        return result

    def token(self, key):
        """Transform a bytes sequence to a token compliant to the pattern."""
        n = int(key.hex(), base=16)
        d = len(self.gliphs)
        p = []
        while True:
            p.append(self.gliphs[n % d])
            n = int(n/d)
            if n < d or len(p) == self.length:
                break
        return ''.join(p)


class KeyWrapper():
    ''' Wrap the secret key.
        Keep the wrapped secret and the wrapping key separated.'''

    def __init__(self):
        pass

    def wrap(self, secret):
        '''Wrap the key and save the further parameters'''
        _wrapkey = os.urandom(16)
        self._wrappedkey = keywrap.aes_key_wrap_with_padding(
            _wrapkey, secret, default_backend())
        return _wrapkey

    def unwrap(self, wrapkey):
        '''Return the secret key'''
        secret = keywrap.aes_key_unwrap_with_padding(
            wrapkey, self._wrappedkey, default_backend())
        return secret


class CipherFachade():

    def __init__(self, encoding='utf-8'):
        self.encoding = encoding
        self.backend = default_backend()

    @staticmethod
    def parse(obj):
        '''Parse an encrypted object to crypto-dictionary format'''
        data = json.loads(obj)
        cryptopars = get_cryptografy_parameters(**data)
        return cipherdata(cryptopars, **data)

    def _algorithm(self, secret, name='AES'):
        if not name:
            return algorithms.AES(secret)
        name = name.upper()
        if name == 'AES':
            return algorithms.AES(secret)
        if name == 'CAMELLIA':
            return algorithms.Camellia(secret)
        elif name == 'CAST5':
            return algorithms.CAST5(secret)
        elif name == 'SEED':
            return algorithms.SEED(secret)
        else:
            return algorithms.AES(secret)

    def encrypt(self, obj, cryptod, secret):
        '''Encrypt a python object to crypto-dictionary format'''
        # Items to json string
        try:
            # Compress content
            data = gzip.compress(
                bytes(json.dumps(obj), encoding=self.encoding))
            # Format content in a crypto-dictioray
            algorithm = self._algorithm(
                secret=secret, name=cryptod['algorithm'])
            iv = os.urandom(int(algorithm.block_size/8))
            cryptod['iv'] = str(base64.b64encode(iv), encoding=self.encoding)
            # Encrypt content
            cipher = Cipher(algorithm, modes.CBC(iv), backend=self.backend)
            encryptor = cipher.encryptor()
            # Pad
            padder = padding.PKCS7(cipher.algorithm.block_size).padder()
            data = padder.update(data) + padder.finalize()
            data = encryptor.update(data) + encryptor.finalize()
            # Base64 encoded
            data = base64.b64encode(data)
            cryptod['mode'] = modes.CBC.name
            cryptod['keysize'] = cipher.algorithm.key_size
            cryptod['ciphervalue'] = str(data, encoding=self.encoding)
            cipher = None
            return cryptod
        except ValueError as ve:
            raise ValueError('Encrypting failure!') from ve

    def decrypt(self, cryptod, secret):
        '''Decrypt the content from crypto-dictionary format
        to python plain object'''
        try:
            # From json to python crypto dict
            data = base64.b64decode(
                bytes(cryptod['ciphervalue'], encoding=self.encoding))
            # Decrypt
            iv = base64.b64decode(bytes(cryptod['iv'], encoding=self.encoding))
            algorithm = self._algorithm(
                secret=secret, name=cryptod['algorithm'])
            cipher = Cipher(algorithm, modes.CBC(iv), backend=self.backend)
            decryptor = cipher.decryptor()
            data = decryptor.update(data) + decryptor.finalize()
            # Unpad
            unpadder = padding.PKCS7(cipher.algorithm.block_size).unpadder()
            data = unpadder.update(data) + unpadder.finalize()
            # Unzip
            data = str(gzip.decompress(data), encoding=self.encoding)
            cipher = None
            # json string
        except ValueError as ve:
            raise ValueError('Decrypt failure!') from ve
        try:
            data = json.loads(data)
        except ValueError as ve:
            raise ValueError('JSON formatting failure!') from ve
        return data

    def key_derivation_function(self, cryptod, info=None):
        '''Return a KeyDerivationFunction from crypto-dictionary
        specifications.'''
        pbkdf = None
        try:
            if cryptod['pbkdf']:
                salt = base64.b64decode(
                    bytes(cryptod['salt'], encoding=self.encoding))
                length = int(cryptod['length'])
                iterations = int(cryptod['iterations'])
                if cryptod['pbkdf'].upper() == 'HKDF':
                    pbkdf = HKDF(
                        algorithm=hashes.SHA256(),
                        length=length,
                        salt=salt,
                        info=info,
                        backend=self.backend
                    )
                if cryptod['pbkdf'].upper() == 'PBKDF2HMAC':
                    pbkdf = PBKDF2HMAC(
                        algorithm=hashes.SHA256(),
                        length=length,
                        salt=salt,
                        iterations=iterations,
                        backend=self.backend
                    )
                return pbkdf
        except ValueError as ve:
            raise ValueError('Key derivation function failure!') from ve
        else:
            raise ValueError('Invalid argument!')

    def secret(self, key, iterations, pattern):
        '''Return a readable password generated from a secret
        key and a pattern.

        A password of n characters requires a length of (n - 1) bytes.

        Parameters:

            pattern is a Pattern object

        Return:

            password, salt
        '''

        pwd = ''
        while not pattern.check(pwd):
            salt = os.urandom(32)
            pbkdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=pattern.length - 1,
                salt=salt,
                iterations=iterations,
                backend=self.backend
            )
            pwd = pattern.token(pbkdf.derive(key))
            pbkdf = None
        return pwd, salt

    def password(self, key, salt, iterations, pattern):
        '''Return a password from a pattern'''
        pbkdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=pattern.length - 1,
            salt=salt,
            iterations=iterations,
            backend=self.backend
        )

        pwd = pattern.token(pbkdf.derive(key))
        return pwd


if __name__ is '__main__':
    '''Prepare a key'''
    cryptopars = get_cryptografy_parameters(
        algorithm='AES',
        mode='CBC',
        iv='',
        keysize=256,
        pbkdf='PBKDF2HMAC',
        hash='SHA256',
        length=int(256/8),
        iterations=100,
        salt=str(base64.b64encode(os.urandom(32)), encoding='utf-8'),
        ciphervalue='')

    cd = cipherdata(cryptopars,
                    iv='',
                    ciphervalue=''
                    )

    items = [a for a in range(0, 100)]

    cf = CipherFachade()
    pbkdf = cf.key_derivation_function(cd)
    sc = pbkdf.derive(b'my passphrase')
    pbkdf = cf.key_derivation_function(cd)
    print(
        f"Test key generation verifification: {pbkdf.verify(b'my passphrase', sc)==None}")

    '''Wrap and unwrap key is ok during a session'''
    kw = KeyWrapper()
    wrappingkey = kw.wrap(sc)
    print(kw.unwrap(wrappingkey))

    key = kw.unwrap(wrappingkey)
    print(f"Test key wrapping: {key==sc}")
    c = cf.encrypt(obj=items, cryptod=cd, secret=key)
    jc = json.dumps(c)
    cd1 = cf.parse(jc)
    # Recover key from crypto-dictionary
    pbkdf = cf.key_derivation_function(cd1)
    key1 = pbkdf.derive(b'my passphrase')
    d = cf.decrypt(cryptod=cd1, secret=key1)

    print(
        f'Encrypt - Decrypt test passed: {all([items[i] - d[i] for i in range(0, len(items))])==False}')

    print(cipher_algorithms())

    print(
        f"Pattern passed - right: {Pattern(1, 3, 5, 12).check('ABCDEFGHIjj,.-[]123')}")
    print(
        f"Pattern passed - more symbols: {Pattern(1, 3, 5, 12).check('ABCD2EFGHIjj,.-[]123')}")
    print(
        f"Pattern passed - more numbers: {Pattern(1, 3, 5, 12).check('ABCD2EFGHIjj,.-[!]123')}")
    print(
        f"Pattern passed - low numbers: {not Pattern(1, 3, 5, 12).check('ABCDEFGHIjj,.-[]13')}")
    print(
        f"Pattern passed - low symbols: {not Pattern(1, 3, 5, 12).check('ABCD2EFGHIjj,-[]123')}")

    b = b'\xa6\xadu09\xab\xc0\xcb[+\x04O\xc7\x9b\x19@0L#\x80\xc4\x8e=b\xbe\xea\xf9\xc3F\xb5\xc1\x12'

    for i in range(0, 4):
        for j in range(0, 5):
            (passwd, salt) = cf.secret(b, 1000, Pattern(5, i, j, 12))
            print(f'Password: {passwd}, Salt: {salt}')
            # Ckeck password
            passwd_ckh = cf.password(b, salt, 1000, Pattern(5, i, j, 12))
            print(f'The password check is: {passwd_ckh==passwd}')
