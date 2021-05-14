# -*- coding: utf-8 -*-
#
# Copyright (c) 2012 Red Hat, Inc
#
# kitchen is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# kitchen is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with kitchen; if not, see <http://www.gnu.org/licenses/>
#
# Authors:
#   Toshio Kuratomi <toshio@fedoraproject.org>
'''
----------
StrictDict
----------

:class:`kitchen.collections.StrictDict` provides a dictionary that treats
:class:`bytes` and :class:`str` as distinct key values.
'''

# Pylint disabled messages:
# :C0111: We're implementing the dict interface so just reference the dict
#   documentation rather than having our own docstrings

import warnings

warnings.warn('In python3, kitchen.collections.strictdict is deprecated.'
        '  If your code doesn\'t have to remain compatible with python2 use'
        ' python3\'s native dict or defaultdict types instead',
        PendingDeprecationWarning, stacklevel=2)

try:
    # :E0611: Pylint false positive.  We try to import from the stdlib but we
    #   have a fallback so this is okay.
    #pylint:disable-msg=E0611
    from collections import defaultdict
except ImportError:
    from kitchen.pycompat25.collections import defaultdict

# in python3, ordinary dictionaries keep bytes and strings separate
StrictDict = defaultdict

__all__ = ('StrictDict',)
