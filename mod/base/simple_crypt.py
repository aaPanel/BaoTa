#!/usr/bin/env python3
"""
最终版本：标准APR1算法实现的crypt.crypt()替代函数
基于 https://github.com/Tblue/pyapr1/blob/master/apr1.py
"""

import hashlib
import os


def to64(data, n_out):
    """APR1标准的base64编码"""
    chars = "./0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    out = ""
    for i in range(n_out):
        out += chars[data & 0x3f]
        data >>= 6
    return out


def mkint(data, *indexes):
    """从字节数组的指定索引创建整数"""
    r = 0
    for i, idx in enumerate(indexes):
        r |= data[idx] << 8 * (len(indexes) - i - 1)
    return r


def hash_apr1(salt, password):
    """标准APR1哈希算法"""
    sb = bytes(salt, "ascii")
    pb = bytes(password, "iso-8859-1")
    ph = hashlib.md5()

    ph.update(pb)
    ph.update(b"$apr1$")
    ph.update(sb)

    sandwich = hashlib.md5(pb + sb + pb).digest()
    ndig, nrem = divmod(len(pb), ph.digest_size)
    for n in ndig * [ph.digest_size] + [nrem]:
        ph.update(sandwich[:n])

    i = len(pb)
    while i:
        if i & 1:
            ph.update(b'\x00')
        else:
            ph.update(pb[:1])
        i >>= 1

    final = ph.digest()

    for i in range(1000):
        maelstrom = hashlib.md5()

        if i & 1:
            maelstrom.update(pb)
        else:
            maelstrom.update(final)

        if i % 3:
            maelstrom.update(sb)

        if i % 7:
            maelstrom.update(pb)

        if i & 1:
            maelstrom.update(final)
        else:
            maelstrom.update(pb)

        final = maelstrom.digest()

    pw_ascii = (to64(mkint(final, 0, 6, 12), 4) +
                to64(mkint(final, 1, 7, 13), 4) +
                to64(mkint(final, 2, 8, 14), 4) +
                to64(mkint(final, 3, 9, 15), 4) +
                to64(mkint(final, 4, 10, 5), 4) +
                to64(mkint(final, 11), 2))

    return f"$apr1${salt}${pw_ascii}"


def generate_salt():
    """生成随机盐值"""
    random_bytes = os.urandom(6)
    return to64(mkint(random_bytes, *range(6)), 8)


def crypt(password, salt=None):
    """
    直接替代 crypt.crypt(password, salt)
    生成nginx完全兼容的APR1密码哈希

    Args:
        password (str): 要加密的密码
        salt (str, optional): 盐值，如果为None则自动生成

    Returns:
        str: APR1格式的密码哈希，如 $apr1$salt$hash

    用法：
        原来: import crypt; hashed = crypt.crypt(password, salt)
        替换: from final_crypt import crypt; hashed = crypt(password, salt)
    """
    if salt is None:
        salt = generate_salt()
    elif salt.startswith('$apr1$'):
        parts = salt.split('$')
        if len(parts) >= 3:
            salt = parts[2]
        else:
            salt = generate_salt()

    return hash_apr1(salt, password)