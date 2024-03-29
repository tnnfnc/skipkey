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


RANDOM_BYTES = 32


def _(x):
    """Translation mask
    """
    return x


def init_symbols():
    """Return a tuple of symbols:
    ! # $ % & ( ) , + * - = . : ; ? @ [ ] ^ _
    """
    # '"', no
    # "'", no
    # '/', no
    # '<', no
    # '>', no
    # '\', no
    #  "`", maybe
    #  '~', maybe
    return ('!', '#', '$', '%', '&', '(', ')', ',', '+', '*', '-',
            '=', '.', ':', ';', '?', '@', '[', ']', '^', '_')

# Digit


def init_numbers():
    """Return a tuple of numbers digit from exadecimal
    ranges [0x30-0x39]."""
    return ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9')


# Upper
def init_letters():
    """Return a tuple of lowercase and uppercase letters
    from exadecimal ranges [0x41-0x5a], [0x61-0x7a]."""
    return ('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i',
            'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r',
            's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
            'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I',
            'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R',
            'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z')


SYMBOLS = init_symbols()
NUMBERS = init_numbers()
LETTERS = init_letters()


def init_crypto_args(**kwargs):
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
         'salt': str(base64.b64encode(os.urandom(RANDOM_BYTES)), encoding='utf-8')}
    return {**d, **kwargs}


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


class PatternException(Exception):
    pass


class Schema():
    """[summary]

    Raises:
        PatternException: [description]

    Returns:
        [type]: [description]
    """
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
    def auto(self, value: bool):
        self._encode(value, 1)

    @lenght.setter
    def lenght(self, value: int):
        self._encode(value, 2)

    @letters.setter
    def letters(self, value: bool):
        self._encode(value, 3)

    @numbers.setter
    def numbers(self, value: int):
        self._encode(value, 4)

    @symbols.setter
    def symbols(self, value: int):
        self._encode(value, 5)

    @gliphs.setter
    def gliphs(self, value: str):
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
        self.numbers = self._convert(numbers)
        self.symbols = self._convert(symbols)
        self.letters = self._convert(letters)
        self._length = self._convert(length)

        self._gliphs = []
        if self.letters > 0:
            self._gliphs.extend(LETTERS)
        if self.numbers > 0:
            self._gliphs.extend(NUMBERS)
        if self.symbols > 0:
            self._gliphs.extend(SYMBOLS)
        if self.numbers + self.letters + self.symbols == 0:
            raise ValueError(_('Inconsistent pattern of zeros gliphs'))

    def _convert(self, s):
        if s == None or s == '' or str(s) == 'False':
            s = 0
        elif str(s) == 'True':
            s = 1
        return int(s)

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
        if len(key) < 1:
            raise PatternException(_('Password length must be at least 2'))

        n = int(key.hex(), base=16)
        d = len(self.gliphs)
        p = []

        p.append(self.gliphs[n % d])
        while len(p) < self.length:
            n = int(n/d) if int(n/d) > 0 else n
            if n < d:
                p.append(self.gliphs[n])
                break
            else:
                p.append(self.gliphs[n % d])

        if len(p) != self.length:
            raise PatternException()

        # while True:
        #     p.append(self.gliphs[n % d])
        #     n = int(n/d)
        #     if n < d or len(p) == self.length:
        #         break
        return ''.join(p)


class KeyWrapper():
    ''' Wrap the secret key.
        Keep the wrapped secret and the wrapping key separated.'''

    def wrap(self, secret):
        '''Wrap the key and save the further parameters'''
        # _wrapkey = os.urandom(16)
        _wrapkey = os.urandom(RANDOM_BYTES)
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
        """Parse a JSON string containing an encrypted content to a dictionary format.

        Args:
            obj (str): JSON string containing an encrypted content.
        Returns:
            dict: a dictionary containing an encrypted content.
        """
        data = json.loads(obj)
        cryptopars = init_crypto_args(**data)
        return cryptopars
        # return cipherdata(cryptopars, **data)

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
        """Encrypt a python object to a dictionary format.

        Args:
            obj (Object): the content to be encrypted.
            cryptod (dict): criptographic arguments.
            secret (bytes): secret key.

        Raises:
            ValueError: generic encryption error.

        Returns:
            dict: encrypted content dictionary.
        """
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
        """Decrypt the content from a dictionary format to a JSON string.

        Args:
            cryptod (dict): encrypted content
            secret (bytes array): secret key

        Raises:
            ValueError: Generic decryption error.

        Returns:
            str: a JSON string.
        """
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
        '''Return a string password generated from a secret
        key and a pattern.

        A password of n characters requires a length of (n - 1) bytes.

        Parameters:

            pattern is a Pattern object

        Return:

            password, salt
        '''

        pwd = ''
        while not pattern.check(pwd):
            salt = os.urandom(RANDOM_BYTES)
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


if __name__ == '__main__':
    '''Prepare a key'''
    cryptopars = init_crypto_args(
        algorithm='AES',
        mode='CBC',
        iv='',
        keysize=256,
        pbkdf='PBKDF2HMAC',
        hash='SHA256',
        length=int(256/8),
        iterations=100,
        salt=str(base64.b64encode(os.urandom(RANDOM_BYTES)), encoding='utf-8'),
        ciphervalue='')

    items = [a for a in range(0, 100)]

    cf = CipherFachade()
    pbkdf = cf.key_derivation_function(cryptopars)
    sc = pbkdf.derive(b'my passphrase')
    pbkdf = cf.key_derivation_function(cryptopars)
    print(
        f"Test key generation verifification: {pbkdf.verify(b'my passphrase', sc)==None}")

    '''Wrap and unwrap key is ok during a session'''
    kw = KeyWrapper()
    wrappingkey = kw.wrap(sc)
    print(kw.unwrap(wrappingkey))

    key = kw.unwrap(wrappingkey)
    print(f"Test key wrapping: {key==sc}")
    c = cf.encrypt(obj=items, cryptod=cryptopars, secret=key)
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
