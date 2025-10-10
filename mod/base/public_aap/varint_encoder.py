import struct


# varint编码 -> bytes
def _varint_encode(num):
    res = b''

    while num > 127:
        res += struct.pack('B', 0x80 | (num & 0x7f))
        num >>= 7

    res += struct.pack('B', num)

    return res


# varint解码 -> num, length
def _varint_decode(bs):
    res = 0
    n = 0
    for shift in range(0, 64, 7):
        if n > len(bs) - 1:
            break

        res |= (bs[n] & 0x7f) << shift
        if (bs[n] & 0x80) == 0:
            break

        n += 1

    return res, n + 1
