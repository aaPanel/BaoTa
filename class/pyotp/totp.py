from __future__ import absolute_import, division, print_function, unicode_literals

import datetime
import time

from . import utils
from .otp import OTP
from .compat import str

class TOTP(OTP):
    """
    Handler for time-based OTP counters.
    """
    def __init__(self, *args, **kwargs):
        """
        :param interval: the time interval in seconds
            for OTP. This defaults to 30.
        :type interval: int
        """
        self.interval = kwargs.pop('interval', 30)
        super(TOTP, self).__init__(*args, **kwargs)

    def at(self, for_time, counter_offset=0):
        """
        Accepts either a Unix timestamp integer or a datetime object.

        :param for_time: the time to generate an OTP for
        :type for_time: int or datetime
        :param counter_offset: the amount of ticks to add to the time counter
        :returns: OTP value
        :rtype: str
        """
        if not isinstance(for_time, datetime.datetime):
            for_time = datetime.datetime.fromtimestamp(int(for_time))
        return self.generate_otp(self.timecode(for_time) + counter_offset)

    def now(self):
        """
        Generate the current time OTP

        :returns: OTP value
        :rtype: str
        """
        return self.generate_otp(self.timecode(datetime.datetime.now()))

    def verify(self, otp, for_time=None, valid_window=0):
        """
        Verifies the OTP passed in against the current time OTP.

        :param otp: the OTP to check against
        :type otp: str
        :param for_time: Time to check OTP at (defaults to now)
        :type for_time: int or datetime
        :param valid_window: extends the validity to this many counter ticks before and after the current one
        :type valid_window: int
        :returns: True if verification succeeded, False otherwise
        :rtype: bool
        """
        if for_time is None:
            for_time = datetime.datetime.now()

        if valid_window:
            for i in range(-valid_window, valid_window + 1):
                if utils.strings_equal(str(otp), str(self.at(for_time, i))):
                    return True
            return False

        return utils.strings_equal(str(otp), str(self.at(for_time)))

    def provisioning_uri(self, name, issuer_name=None):
        """
        Returns the provisioning URI for the OTP.  This can then be
        encoded in a QR Code and used to provision an OTP app like
        Google Authenticator.

        See also:
            https://github.com/google/google-authenticator/wiki/Key-Uri-Format

        :param name: name of the user account
        :type name: str
        :param issuer_name: the name of the OTP issuer; this will be the
            organization title of the OTP entry in Authenticator
        :returns: provisioning URI
        :rtype: str
        """
        return utils.build_uri(self.secret, name, issuer_name=issuer_name,
                               algorithm=self.digest().name,
                               digits=self.digits, period=self.interval)

    def timecode(self, for_time):
        i = time.mktime(for_time.timetuple())
        return int(i / self.interval)
