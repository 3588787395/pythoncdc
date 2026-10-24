# Source Generated with Decompyle++ (Python version)
# File: encrypt.pyc (Python 3.11)

import codecs
from binascii import b2a_hex, a2b_hex
class AESEncrypt(object):
    def __init__(self, length=16):
        self._length = length
    def encrypt(self, data, key, iv):
        """
        使用AES对代码进行加密

        Args:
            data:  明文，需要注意的是：如果明文data的长度不是密钥长度的倍数【加密文本text必须为密钥长度的倍数！】，那就补足为密钥长度的倍数
            key :  密钥key 长度必须为16（AES-128）、24（AES-192）、或32（AES-256）Bytes 长度.
            iv  ： 初始向量,长度必须为16Byte
        Returns:
            加密后的代码
        """
        from Crypto.Cipher import AES
        cryptor = AES.new(key, AES.MODE_CBC, iv)
        data = data.encode('utf-8')
        count = len(data)
        add = self._length - count % self._length
        data = data + b'\x00' * add
        context = cryptor.encrypt(data)
        return b2a_hex(context).decode('ASCII')
    def decrypt(self, data, key, iv):
        """
        对已经用AES加密的代码进行解密

        Args:
            data:  密文
            key :  密钥key 长度必须为16（AES-128）、24（AES-192）、或32（AES-256）Bytes 长度.
            iv  ： 初始向量，必须与加密的初始向量相同
        Returns:
            解密后的代码
        """
        from Crypto.Cipher import AES
        cryptor = AES.new(key, AES.MODE_CBC, iv)
        plain_text = cryptor.decrypt(a2b_hex(data))
        result_text = plain_text.rstrip(b'\x00')
        return result_text.decode('utf-8')
class DESEncrypt(object):
    def __init__(self, length=32):
        self._length = length
    def encrypt(self, data, key, iv):
        """
        使用DES对代码进行加密

        Args:
            data:  明文，需要注意的是：如果明文data的长度不是密钥长度的倍数【加密文本text必须为密钥长度的倍数！】，那就补足为密钥长度的倍数
            key :  密钥key 长度必须为8Bytes 长度.
            iv  ： 初始向量,长度必须为8Byte
        Returns:
            加密后的代码
        """
        from Crypto.Cipher import DES
        cryptor = DES.new(key, DES.MODE_CBC, iv)
        data = data.encode('utf-8')
        count = len(data)
        add = self._length - count % self._length
        data = data + b'\x00' * add
        context = cryptor.encrypt(data)
        return b2a_hex(context).decode('ASCII')
    def decrypt(self, data, key, iv):
        """
        对已经用DES加密的代码进行解密

        Args:
            data: 密文
            key : 密钥key 长度必须为8Bytes 长度.
            iv  ：初始向量，必须与加密的初始向量相同
        Returns:
            解密后的代码
        """
        from Crypto.Cipher import DES
        cryptor = DES.new(key, DES.MODE_CBC, iv)
        context = cryptor.decrypt(a2b_hex(data))
        result_text = context.rstrip(b'\x00')
        return result_text.decode('utf-8')
