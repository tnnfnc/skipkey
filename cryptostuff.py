'''Crypto stuff...'''
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


def _(text):
    return text

# def load_dll():
#     import os
#     import sys

#     options = {"build_exe": {}}
#     PYTHON_INSTALL_DIR = os.path.dirname(os.path.dirname(os.__file__))
#     if sys.platform == "win32":
#         options["build_exe"]['include_files'] = [
#             os.path.join(PYTHON_INSTALL_DIR, 'DLLs', 'libcrypto-1_1-x64.dll'),
#             os.path.join(PYTHON_INSTALL_DIR, 'DLLs', 'libssl-1_1-x64.dll'),
#      ]

# load_dll()


SYMBOLS = []
# Symbols
for hex in range(int('21', base=16), int('30', base=16)):
    SYMBOLS.append(chr(hex))
for hex in range(int('3a', base=16), int('41', base=16)):
    SYMBOLS.append(chr(hex))
for hex in range(int('5b', base=16), int('60', base=16)):
    SYMBOLS.append(chr(hex))
SYMBOLS = tuple(SYMBOLS)

# Digit
NUMBERS = []
for hex in range(int('30', base=16), int('3a', base=16)):
    NUMBERS.append(chr(hex))
NUMBERS = tuple(NUMBERS)


# Upper
LETTERS = []
for hex in range(int('41', base=16), int('5b', base=16)):
    LETTERS.append(chr(hex))
# Lower
for hex in range(int('61', base=16), int('7b', base=16)):
    LETTERS.append(chr(hex))
LETTERS = tuple(LETTERS)

default_cryptod = {'algorithm': 'AES',
                   'mode': 'CBC',
                   'keysize': 256,
                   'pbkdf': 'PBKDF2HMAC',
                   'hash': 'SHA256',
                   'length': int(256/8),
                   'iterations': 100,
                   'salt': str(base64.b64encode(os.urandom(32)), encoding='utf-8')}


def encrypt_by_key(cryptod, password, seed, items, key):
    '''Encrypt in place the content of items witk the key specified'''
    try:
        local_cf = CipherFachade()
        # key = local_cf.key_derivation_function(
        #     cryptod).derive(password)
        seed = local_cf.key_derivation_function(
            cryptod).derive(seed)
        for item in items:
            r = local_cf.encrypt(item[key], cryptod, seed)
            r = bytes(json.dumps(r), encoding='utf-8')
            r = str(base64.b64encode(r), encoding='utf-8')
            item[key] = r
        return items
    except Exception as e:
        return None


def cryptodict(strict=True, **args):
    """
    Cripto dicionary builder.
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
        'algorithm': '',  # algorithms=AES
        'mode': '',  # CBC fixed
        'iv': '',  # initialisation vector al long as cipher's block
        'keysize': '',  # cipher key size in bits
        'pbkdf': '',
        'hash': '',  # SHA256
        'length': '',  # length of the derived key, converted in bits must match keysize
        'iterations': '',
        'salt': '',  # 32 bytes for key derivation
        'ciphervalue': ''  # Base64 file encoded
    }
    if strict:
        for key in args:
            if key in template:
                template[key] = str(args[key])
    else:
        for key in args:
            template[key] = str(args[key])

    return template


def cipher_algorithms():
    '''Advanced Encryption Standard is a block cipher standardized by NIST;
    it is fast and cryptographically strong. Camellia is a block cipher
    approved for use by CRYPTREC and ISO/IEC. It is considered to have comparable
    security and performance to AES but is not as widely studied or deployed. CAST5
    (also known as CAST-128) is a block cipher approved for use in the Canadian
    government by the Communications Security Establishment. SEED is a block cipher
    developed by the Korea Information Security Agency (KISA). It is defined in RFC
    4269 and is used broadly throughout South Korean industry.'''
    return {'AES': _('Advanced Encryption Standard'),
            'Camellia': _('Camellia is a block cipher approved for use by CRYPTREC and ISO/IEC.'),
            'CAST5': _('CAST5 (also known as CAST-128) is a block cipher approved for use in the Canadian government.'),
            'SEED': _('SEED is a block cipher developed by the Korea Information Security Agency (KISA).')
            }


def key_derivators():
    return {'PBKDF2HMAC': _('Password Based Key Derivation Function 2, is typically used for deriving a cryptographic key from a password.'),
            'HKDF': _('HMAC-based Extract-and-Expand Key Derivation Function, is suitable for deriving keys of a fixed size.'),
            }


class Pattern():
    def __init__(self, lett, num, sym, length, *args, **kwargs):
        if lett is None or lett == '':
            lett = 0
        if num is None or num == '':
            num = 0
        if sym is None or sym == '':
            sym = 0
        if length is None or sym == '':
            length = 0
        # try:
        self.num = int(num)
        self.sym = int(sym)
        self.lett = int(lett)
        self._length = int(length)
        # except ValueError as ve:
        #     ('Accept integer only')

        self._gliphs = []
        if self.lett > 0:
            self._gliphs.extend(LETTERS)
        if self.num > 0:
            self._gliphs.extend(NUMBERS)
        if self.sym > 0:
            self._gliphs.extend(SYMBOLS)
        if self.num + self.lett + self.sym == 0:
            raise ValueError(_('Inconsistent pattern of zeros gliphs'))

    def check(self, text):
        l = s = n = 0
        result = False
        for g in text:
            if g in LETTERS and l < self.lett:
                l += 1
            if g in NUMBERS and n < self.num:
                n += 1
            if g in SYMBOLS and s < self.sym:
                s += 1
            if n == self.num and s == self.sym and l == self.lett:
                result = True
                break
        return result

    @property
    def gliphs(self):
        return self._gliphs

    @property
    def length(self):
        return self._length

    def token(self, key):
        # transorm key to number
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

    def secret(self, wrapkey):
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
        return cryptodict(**json.loads(obj))

    def algorithm(self, secret, name='AES'):
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
            algorithm = self.algorithm(
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
        '''Decrypt the content from crypto-dictionary format to python plain object'''
        try:
            # From json to python crypto dict
            data = base64.b64decode(
                bytes(cryptod['ciphervalue'], encoding=self.encoding))
            # Decrypt
            iv = base64.b64decode(bytes(cryptod['iv'], encoding=self.encoding))
            algorithm = self.algorithm(
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
        '''Return a KeyDerivationFunction from crypto-dictionary specifications.'''
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
        '''Return a readable password generated from a secret key and a pattern.
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
    cd = cryptodict(
        algorithm='AES',
        mode='CBC',
        iv='',
        keysize=256,
        pbkdf='PBKDF2HMAC',
        hash='SHA256',
        length=int(256/8),
        iterations=100,
        salt=str(base64.b64encode(os.urandom(32)), encoding='utf-8'),
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
    print(kw.secret(wrappingkey))

    key = kw.secret(wrappingkey)
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
    # h = b.hex()
    # i = int(b.hex(), base=16)
    # # j = int(b, base=8)
    # gliphs = list(LETTERS)
    # gliphs.extend(list(NUMBERS))
    # gliphs.extend(list(SYMBOLS))

    # pwd = token(gliphs, b, 12)
    # print(f"Key conversion passed - {len(pwd)}: {pwd}")

    for i in range(0, 4):
        for j in range(0, 5):
            (passwd, salt) = cf.secret(b, 1000, Pattern(5, i, j, 12))
            print(f'Password: {passwd}, Salt: {salt}')
            # Ckeck password
            passwd_ckh = cf.password(b, salt, 1000, Pattern(5, i, j, 12))
            print(f'The password check is: {passwd_ckh==passwd}')
