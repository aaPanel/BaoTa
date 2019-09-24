from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

from pyotp.hotp import HOTP  # noqa
from pyotp.otp import OTP  # noqa
from pyotp.totp import TOTP  # noqa
from . import utils  # noqa

def random_base32(length=16, random=None,
                  chars=list('ABCDEFGHIJKLMNOPQRSTUVWXYZ234567')):

    # Use secrets module if available (Python version >= 3.6) per PEP 506
    try:
        import secrets
        random = secrets.SystemRandom()
    except ImportError:
        import random as _random
        random = _random.SystemRandom()

    return ''.join(
        random.choice(chars)
        for _ in range(length)
    )
