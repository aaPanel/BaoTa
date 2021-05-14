# -*- coding: utf-8 -*-
#
# Copyright (c) 2012 Red Hat, Inc
#
# kitchen is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#.
# kitchen is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for
# more details.
#.
# You should have received a copy of the GNU Lesser General Public License
# along with kitchen; if not, see <http://www.gnu.org/licenses/>
#
# Authors:
#   Toshio Kuratomi <toshio@fedoraproject.org>
#   Luke Macken <lmacken@redhat.com>
#
# Portions of code taken from python-fedora fedora/iterutils.py
'''
Functions to manipulate iterables

.. versionadded:: Kitchen: 0.2.1a1

.. moduleauthor:: Toshio Kuratomi <toshio@fedoraproject.org>
.. moduleauthor:: Luke Macken <lmacken@redhat.com>
'''

from kitchen.versioning import version_tuple_to_string

__version_info__ = ((0, 0, 1),)
__version__ = version_tuple_to_string(__version_info__)

from kitchen.text.misc import isbasestring

def isiterable(obj, include_string=False):
    '''Check whether an object is an iterable

    :arg obj: Object to test whether it is an iterable
    :kwarg include_string: If :data:`True` and :attr:`obj` is a byte
        :class:`bytes` or :class:`str` string this function will return
        :data:`True`.  If set to :data:`False`, byte :class:`bytes` and
        :class:`str` strings will cause this function to return
        :data:`False`.  Default :data:`False`.
    :returns: :data:`True` if :attr:`obj` is iterable, otherwise
        :data:`False`.
    '''
    if include_string or not isbasestring(obj):
        try:
            iter(obj)
        except TypeError:
            return False
        else:
            return True
    return False

def iterate(obj, include_string=False):
    '''Generator that can be used to iterate over anything

    :arg obj: The object to iterate over
    :kwarg include_string: if :data:`True`, treat strings as iterables.
        Otherwise treat them as a single scalar value.  Default :data:`False`

    This function will create an iterator out of any scalar or iterable.  It
    is useful for making a value given to you an iterable before operating on it.
    Iterables have their items returned.  scalars are transformed into iterables.
    A string is treated as a scalar value unless the :attr:`include_string`
    parameter is set to :data:`True`.  Example usage::

        >>> list(iterate(None))
        [None]
        >>> list(iterate([None]))
        [None]
        >>> list(iterate([1, 2, 3]))
        [1, 2, 3]
        >>> list(iterate(set([1, 2, 3])))
        [1, 2, 3]
        >>> list(iterate(dict(a='1', b='2')))
        ['a', 'b']
        >>> list(iterate(1))
        [1]
        >>> list(iterate(iter([1, 2, 3])))
        [1, 2, 3]
        >>> list(iterate('abc'))
        ['abc']
        >>> list(iterate('abc', include_string=True))
        ['a', 'b', 'c']
    '''
    if isiterable(obj, include_string=include_string):
        for item in obj:
            yield item
    else:
        yield obj

__all__ = ('isiterable', 'iterate',)
