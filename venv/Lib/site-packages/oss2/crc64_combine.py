import sys

#-----------------------------------------------------------------------------
# Some code below reference to crcmod which base on python2 version
# Replace some functions to compat python3+ version
#
is_py3 = (sys.version_info[0] == 3)
if is_py3:
    xrange = range
    long = int
    sys.maxint = sys.maxsize

#-----------------------------------------------------------------------------
# Export mkCombineFun to user to support crc64 combine feature.
#
# Example:
#
#    import crcmod
#
#    _POLY = 0x142F0E1EBA9EA3693
#    _XOROUT = 0XFFFFFFFFFFFFFFFF
#
#    string_a = '12345'
#    string_b = '67890'
#
#    combine_fun = mkCombineFun(_POLY, 0, True, _XOROUT)
#
#    crc64_a = crcmod.Crc(_POLY, initCrc=0, xorOut=_XOROUT)
#    crc64_a.update(string_a)
#
#    crc64_b = crcmod.Crc(_POLY, initCrc=0, xorOut=_XOROUT)
#    crc64_b.update(string_b)
#
#    combine_fun(crc64_a.crcValue, crc64_b.crcValue, len(string_b))
#

def mkCombineFun(poly, initCrc=~long(0), rev=True, xorOut=0):
    # mask = (1L<<n) - 1

    (sizeBits, initCrc, xorOut) = _verifyParams(poly, initCrc, xorOut)

    mask = (long(1)<<sizeBits) - 1
    if rev:
        poly = _bitrev(long(poly) & mask, sizeBits)
    else:
        poly = long(poly) & mask


    if sizeBits == 64:
        fun = _combine64
    else:
        raise NotImplemented

    def combine_fun(crc1, crc2, len2):
        return fun(poly, initCrc ^ xorOut, rev, xorOut, crc1, crc2, len2)

    return combine_fun


#-----------------------------------------------------------------------------
# The below code implemented crc64 combine logic, the algorithm reference to aliyun-oss-ruby-sdk
# See more details please visist:
#   - https://github.com/aliyun/aliyun-oss-ruby-sdk/tree/master/ext/crcx

GF2_DIM = 64

def gf2_matrix_square(square, mat):
    for n in xrange(GF2_DIM):
        square[n] = gf2_matrix_times(mat, mat[n])


def gf2_matrix_times(mat, vec):
    summary = 0
    mat_index = 0

    while vec:
        if vec & 1:
            summary ^= mat[mat_index]

        vec >>= 1
        mat_index += 1

    return summary


def _combine64(poly, initCrc, rev, xorOut, crc1, crc2, len2):
    if len2 == 0:
        return crc1

    even = [0] * GF2_DIM
    odd = [0] * GF2_DIM

    crc1 ^= initCrc ^ xorOut

    if (rev):
        # put operator for one zero bit in odd
        odd[0] = poly  # CRC-64 polynomial
        row = 1
        for n in xrange(1, GF2_DIM):
            odd[n] = row
            row <<= 1
    else:
        row = 2
        for n in xrange(0, GF2_DIM - 1):
            odd[n] = row
            row <<= 1
        odd[GF2_DIM - 1] = poly

    gf2_matrix_square(even, odd)

    gf2_matrix_square(odd, even)

    while True:
        gf2_matrix_square(even, odd)
        if len2 & long(1):
            crc1 = gf2_matrix_times(even, crc1)
        len2 >>= 1
        if len2 == 0:
            break

        gf2_matrix_square(odd, even)
        if len2 & long(1):
            crc1 = gf2_matrix_times(odd, crc1)
        len2 >>= 1

        if len2 == 0:
            break

    crc1 ^= crc2

    return crc1

#-----------------------------------------------------------------------------
# The below code copy from crcmod, see more detail please visist:
# https://bitbucket.org/cmcqueen1975/crcmod/src/8fb658289c35eff1d37cc47799569f90c5b39e1e/python2/crcmod/crcmod.py?at=default&fileviewer=file-view-default

#-----------------------------------------------------------------------------
# Check the polynomial to make sure that it is acceptable and return the number
# of bits in the CRC.

def _verifyPoly(poly):
    msg = 'The degree of the polynomial must be 8, 16, 24, 32 or 64'
    poly = long(poly) # Use a common representation for all operations
    for n in (8,16,24,32,64):
        low = long(1)<<n
        high = low*2
        if low <= poly < high:
            return n
    raise ValueError(msg)

#-----------------------------------------------------------------------------
# Bit reverse the input value.

def _bitrev(x, n):
    x = long(x)
    y = long(0)
    for i in xrange(n):
        y = (y << 1) | (x & long(1))
        x = x >> 1
    if ((long(1)<<n)-1) <= sys.maxint:
        return int(y)
    return y

#-----------------------------------------------------------------------------
# The following function validates the parameters of the CRC, namely,
# poly, and initial/final XOR values.
# It returns the size of the CRC (in bits), and "sanitized" initial/final XOR values.

def _verifyParams(poly, initCrc, xorOut):
    sizeBits = _verifyPoly(poly)

    mask = (long(1)<<sizeBits) - 1

    # Adjust the initial CRC to the correct data type (unsigned value).
    initCrc = long(initCrc) & mask
    if mask <= sys.maxint:
        initCrc = int(initCrc)

    # Similar for XOR-out value.
    xorOut = long(xorOut) & mask
    if mask <= sys.maxint:
        xorOut = int(xorOut)

    return (sizeBits, initCrc, xorOut)
