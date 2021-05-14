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
In python-2.4, a builtin :class:`set` type was added to python.  This module
provides a function to emulate that on python-2.3 by using the :mod:`sets`
module.

:func:`set`
    Create a set.  If running on python 2.4+ this is the :class:`set`
    constructor.  If using python-2.3, it's :class:`sets.Set`.

:func:`frozenset`
    Create a frozenset.  If running on python2.4+ this is the
    :class:`frozenset` constructor.  If using python-2.3, it's
    :class:`sets.ImmutableSet`.

.. versionchanged:: 0.2.0 API: kitchen.pycompat24 1.0.0
    Added set and frozenset
'''

# All versions of python3 have set and frozenset.  This module just remains
# for compatibility
import warnings

warnings.warn('In python3, kitchen.pycompat24.sets is deprecated.'
        '  If your code doesn\'t need to maintain compatibility with'
        ' python less than 2.4, there is no reason to use anything in this'
        ' module.', PendingDeprecationWarning, stacklevel=2)

set = set
frozenset = frozenset
add_builtin_set = lambda: None

__all__ = ('add_builtin_set', 'set', 'frozenset')
