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
Implement the modern subprocess interface

Python-2.5 and python-2.7 introduce new API features to subprocess.  This is
a backport of that module for use on earlier python versions.

.. seealso::
    :mod:`subprocess`
        for information about using the functions provided here.
'''
import warnings

warnings.warn('In python3, kitchen.pycompat27.subprocess is deprecated.'
        '  If your code doesn\'t have to remain compatible with python less'
        ' than 2.7 use subprocess from the python3 stdlib',
        PendingDeprecationWarning, stacklevel=2)

# :W0401,W0611,W0614: We're importing compatibility to the python-2.7 version
#   of subprocess.
#pylint:disable-msg=W0401,W0611,W0614
# All versions of python3 have a modern enough subprocess.  This module only
# exists for backwards compatibility
from subprocess import *
from subprocess import list2cmdline
from subprocess import __all__

# subprocess.MAXFD was removed in python-3.5
# https://github.com/fedora-infra/kitchen/issues/10
try:
    from subprocess import MAXFD
except ImportError:
    try:
        import os
        MAXFD = os.sysconf("SC_OPEN_MAX")
    except ValueError:
        MAXFD = 256

# subprocess.mswindows was renamed in python-3.5
# https://github.com/fedora-infra/kitchen/issues/12
try:
    from subprocess import mswindows
except ImportError:
    # Python 3.5
    from subprocess import _mswindows as mswindows
