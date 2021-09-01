from __future__ import absolute_import, division, print_function, unicode_literals

from . import utils
from .otp import OTP
from .compat import str

class HOTP(OTP):
    """
    Handler for HMAC-based OTP counters.
    """
    def at(self, count):
        """
        Generates the OTP for the given count.

        :param count: the OTP HMAC counter
        :type count: int
        :returns: OTP
        :rtype: str
        """
        return self.generate_otp(count)

    def verify(self, otp, counter):
        """
        Verifies the OTP passed in against the current counter OTP.

        :param otp: the OTP to check against
        :type otp: str
        :param count: the OTP HMAC counter
        :type count: int
        """
        return utils.strings_equal(str(otp), str(self.at(counter)))

    def provisioning_uri(self, name, initial_count=0, issuer_name=None):
        """
        Returns the provisioning URI for the OTP.  This can then be
        encoded in a QR Code and used to provision an OTP app like
        Google Authenticator.

        See also:
            https://github.com/google/google-authenticator/wiki/Key-Uri-Format

        :param name: name of the user account
        :type name: str
        :param initial_count: starting HMAC counter value, defaults to 0
        :type initial_count: int
        :param issuer_name: the name of the OTP issuer; this will be the
            organization title of the OTP entry in Authenticator
        :returns: provisioning URI
        :rtype: str
        """
        return utils.build_uri(
            self.secret,
            name,
            initial_count=initial_count,
            issuer_name=issuer_name,
            algorithm=self.digest().name,
            digits=self.digits
        )
