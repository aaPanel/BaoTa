from __future__ import absolute_import, division, print_function, unicode_literals

import unicodedata
try:
    from itertools import izip_longest
except ImportError:
    from itertools import zip_longest as izip_longest

try:
    from urllib.parse import quote, urlencode
except ImportError:
    from urllib import quote, urlencode


def build_uri(secret, name, initial_count=None, issuer_name=None,
              algorithm=None, digits=None, period=None):
    """
    Returns the provisioning URI for the OTP; works for either TOTP or HOTP.

    This can then be encoded in a QR Code and used to provision the Google
    Authenticator app.

    For module-internal use.

    See also:
        https://github.com/google/google-authenticator/wiki/Key-Uri-Format

    :param secret: the hotp/totp secret used to generate the URI
    :type secret: str
    :param name: name of the account
    :type name: str
    :param initial_count: starting counter value, defaults to None.
        If none, the OTP type will be assumed as TOTP.
    :type initial_count: int
    :param issuer_name: the name of the OTP issuer; this will be the
        organization title of the OTP entry in Authenticator
    :type issuer_name: str
    :param algorithm: the algorithm used in the OTP generation.
    :type algorithm: str
    :param digits: the length of the OTP generated code.
    :type digits: int
    :param period: the number of seconds the OTP generator is set to
        expire every code.
    :type period: int
    :returns: provisioning uri
    :rtype: str
    """
    # initial_count may be 0 as a valid param
    is_initial_count_present = (initial_count is not None)

    # Handling values different from defaults
    is_algorithm_set = (algorithm is not None and algorithm != 'sha1')
    is_digits_set = (digits is not None and digits != 6)
    is_period_set = (period is not None and period != 30)

    otp_type = 'hotp' if is_initial_count_present else 'totp'
    base_uri = 'otpauth://{0}/{1}?{2}'

    url_args = {'secret': secret}

    label = quote(name)
    if issuer_name is not None:
        label = quote(issuer_name) + ':' + label
        url_args['issuer'] = issuer_name

    if is_initial_count_present:
        url_args['counter'] = initial_count
    if is_algorithm_set:
        url_args['algorithm'] = algorithm.upper()
    if is_digits_set:
        url_args['digits'] = digits
    if is_period_set:
        url_args['period'] = period

    uri = base_uri.format(otp_type, label, urlencode(url_args).replace("+", "%20"))
    return uri


def _compare_digest(s1, s2):
    differences = 0
    for c1, c2 in izip_longest(s1, s2):
        if c1 is None or c2 is None:
            differences = 1
            continue
        differences |= ord(c1) ^ ord(c2)
    return differences == 0


try:
    # Python 3.3+ and 2.7.7+ include a timing-attack-resistant
    # comparison function, which is probably more reliable than ours.
    # Use it if available.
    from hmac import compare_digest
except ImportError:
    compare_digest = _compare_digest


def strings_equal(s1, s2):
    """
    Timing-attack resistant string comparison.

    Normal comparison using == will short-circuit on the first mismatching
    character. This avoids that by scanning the whole string, though we
    still reveal to a timing attack whether the strings are the same
    length.
    """
    s1 = unicodedata.normalize('NFKC', s1)
    s2 = unicodedata.normalize('NFKC', s2)
    return compare_digest(s1.encode("utf-8"), s2.encode("utf-8"))
