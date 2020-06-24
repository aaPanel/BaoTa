# coding: utf-8
# | Python AES
# +--------------------------------------------------------------------

from Crypto.Cipher import AES
import base64,sys
class aescrypt_py3():
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


