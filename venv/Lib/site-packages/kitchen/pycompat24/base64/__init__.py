# -*- coding: utf-8 -*-
#
# Copyright (c) 2012 Red Hat, Inc
#
# This file is part of kitchen
#
# kitchen is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# kitchen is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for
# more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with kitchen; if not, see <http://www.gnu.org/licenses/>
#
# Authors:
#   Toshio Kuratomi <toshio@fedoraproject.org>

'''
Implement the modern base64 interface.

Python-2.4 and above have a new API for the base64 module.  This is a backport
of that module for use on python-2.3.

.. seealso::
    :mod:`base64`
        for information about using the functions provided here.
'''
# All versions of python3 include a base64 module.  This module just exists for
# compatibility


# :W0401,W0614: The purpose of this module is to create a backport of base64
# so we ignore these pylint warnings

import warnings

warnings.warn('In python3, kitchen.pycompat24.base64 is deprecated.'
        '  If your code doesn\'t have to remain compatible with python2 use'
        ' python3\'s native dict or defaultdict types instead',
        PendingDeprecationWarning, stacklevel=2)

#pylint:disable-msg=W0401,W0614
from base64 import *

decodestring = decode
encodestring = encode

__all__ = ('b16decode', 'b16encode', 'b32decode', 'b32encode', 'b64decode',
        'b64encode', 'decode', 'decodebytes', 'decodestring', 'encode',
        'encodebytes', 'encodestring', 'standard_b64decode',
        'standard_b64encode', 'urlsafe_b64decode', 'urlsafe_b64encode',)

# These were added in python3.4, so we'll let them shine through...
import sys
_major, _minor = sys.version_info[:2]
if _major == 3 and _minor >= 4:
    __all__ = __all__ + (
        'b85decode', 'a85decode', 'b85encode', 'a85encode',
    )
