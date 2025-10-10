# coding: utf-8
# | Python AES
# +--------------------------------------------------------------------

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64, sys
import public


class aescrypt_py3():
    def __init__(self,key,model = 'ECB',iv = None,encode_='utf-8'):
        self.encode_ = encode_
        self.model =  {'ECB':AES.MODE_ECB,'CBC':AES.MODE_CBC}[model]
        self.key = self.add_16(key)
        if model == 'ECB':
            self.aes = AES.new(self.key,self.model)
        elif model == 'CBC':
            self.aes = AES.new(self.key, self.model, iv)

    def add_16(self,par):
        par = par.encode(self.encode_)
        while len(par) % 16 != 0:
            par += b'\x00'
        return par

    def aesencrypt(self,text):
        text = self.add_16(text)
        self.encrypt_text = self.aes.encrypt(text)
        return base64.encodebytes(self.encrypt_text).decode().strip().replace("\n","")

    def aesdecrypt(self,text):
        text = base64.decodebytes(text.encode(self.encode_))
        self.decrypt_text = self.aes.decrypt(text)
        return self.decrypt_text.decode(self.encode_).strip('\0')

    # base64 编码
    def encode_base64(self, data):
        str2 = (data).strip()
        if sys.version_info[0] == 2:
            return base64.b64encode(str2)
        else:
            return str(base64.b64encode(str2.encode('utf-8')))

    # base64 解码
    def decode_base64(self, data):
        import base64
        str2 = (data).strip()
        if sys.version_info[0] == 2:
            return base64.b64decode(str2)
        else:
            return str(base64.b64decode(str2))

class aescrypt_py2():
    def __init__(self,key,model = 'ECB',iv = None,encode_='utf-8'):
        self.encode_ = encode_
        self.model =  {'ECB':AES.MODE_ECB,'CBC':AES.MODE_CBC}[model]
        self.key = self.add_16(key)
        if model == 'ECB':
            self.aes = AES.new(self.key,self.model)
        elif model == 'CBC':
            self.aes = AES.new(self.key,self.model,iv)

    def add_16(self,par):
        par = par.encode(self.encode_)
        while len(par) % 16 != 0:
            par += b'\x00'
        return par
    def aesencrypt(self,text):
        text = self.add_16(text)
        self.encrypt_text = self.aes.encrypt(text)
        return base64.b64encode(self.encrypt_text).decode().strip().replace("\n","")

    def aesdecrypt(self,text):
        text = base64.b64decode(text.encode(self.encode_))
        self.decrypt_text = self.aes.decrypt(text)
        return self.decrypt_text.decode(self.encode_).strip('\0')

        ##############   base64    #############
    # base64 编码
    def encode_base64(self, data):
        str2 = (data).strip()
        if sys.version_info[0] == 2:
            return base64.b64encode(str2)
        else:
            return str(base64.b64encode(str2.encode('utf-8')))

    # base64 解码
    def decode_base64(self, data):
        import base64
        str2 = (data).strip()
        if sys.version_info[0] == 2:
            return base64.b64decode(str2)
        else:
            return str(base64.b64decode(str2))


class AesCryptPy3(object):
    def __init__(self, key, model='ECB', iv=None, char_set='utf8'):
        self.char_set = char_set
        self.model = model
        self.key = self.add_16(key)
        self.iv = None if iv is None else self.add_16(iv)

    def add_16(self, par):
        if not isinstance(par, bytes):
            par = par.encode(self.char_set)
        while len(par) % 16 != 0:
            par += b'\0'
        return par

    @property
    def aes(self):
        if self.model == 'ECB':
            return AES.new(self.key, AES.MODE_ECB)
        elif self.model == 'CBC':
            return AES.new(self.key, AES.MODE_CBC, self.iv)
        raise ValueError("不支持的加密方式")

    def aes_encrypt(self, text: str):
        text = pad(text.encode(self.char_set), 16)
        encrypt_text = self.aes.encrypt(text)
        return base64.b64encode(encrypt_text).decode()

    def aes_decrypt(self, text: str):
        text = base64.decodebytes(text.encode(self.char_set))
        decrypt_text = self.aes.decrypt(text)
        decrypt_text = unpad(decrypt_text, 16)
        return decrypt_text.decode(self.char_set).strip('\0')

    # base64 编码
    @staticmethod
    def encode_base64(data: str):
        str2 = data.strip()
        if sys.version_info[0] == 2:
            return base64.b64encode(str2)
        else:
            return str(base64.b64encode(str2.encode('utf-8')))

    # base64 解码
    @staticmethod
    def decode_base64(data: str):
        import base64
        str2 = data.strip()
        if sys.version_info[0] == 2:
            return base64.b64decode(str2)
        else:
            return str(base64.b64decode(str2).decode('utf-8'))
