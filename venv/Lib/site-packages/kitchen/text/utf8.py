# -*- coding: utf-8 -*-
#
# Copyright (c) 2012 Red Hat, Inc.
# Copyright (c) 2010 Ville Skyttä
# Copyright (c) 2009 Tim Lauridsen
# Copyright (c) 2007 Marcus Kuhn
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
#   James Antill <james@fedoraproject.org>
#   Marcus Kuhn
#   Toshio Kuratomi <toshio@fedoraproject.org>
#   Tim Lauridsen
#   Ville Skyttä
#
# Portions of this are from yum/i18n.py
'''
-----
UTF-8
-----

Functions for operating on byte :class:`bytes` encoded as :term:`UTF-8`

.. note::

    In many cases, it is better to convert to :class:`str`, operate on the
    strings, then convert back to :term:`UTF-8`.  :class:`str` type can
    handle many of these functions itself.  For those that it doesn't
    (removing control characters from length calculations, for instance) the
    code to do so with a :class:`str` type is often simpler.

.. warning::

    All of the functions in this module are deprecated.  Most of them have
    been replaced with functions that operate on unicode values in
    :mod:`kitchen.text.display`.  :func:`kitchen.text.utf8.utf8_valid` has
    been replaced with a function in :mod:`kitchen.text.misc`.
'''
import warnings

from kitchen.text.converters import to_unicode, to_bytes
from kitchen.text.misc import byte_string_valid_encoding, isunicodestring
from kitchen.text.display import _textual_width_le, \
        byte_string_textual_width_fill, fill, textual_width, \
        textual_width_chop, wrap

#
# Deprecated functions
#

def utf8_valid(msg):
    '''**Deprecated** Detect if a string is valid :term:`utf-8`

    Use :func:`kitchen.text.misc.byte_string_valid_encoding` instead.
    '''
    warnings.warn('kitchen.text.utf8.utf8_valid is deprecated.  Use'
            ' kitchen.text.misc.byte_string_valid_encoding(msg) instead',
            DeprecationWarning, stacklevel=2)
    return byte_string_valid_encoding(msg)

def utf8_width(msg):
    '''**Deprecated** Get the :term:`textual width` of a :term:`utf-8` string

    Use :func:`kitchen.text.display.textual_width` instead.
    '''
    warnings.warn('kitchen.text.utf8.utf8_width is deprecated.  Use'
        ' kitchen.text.display.textual_width(msg) instead',
        DeprecationWarning, stacklevel=2)
    return textual_width(msg)


def utf8_width_chop(msg, chop=None):
    '''**Deprecated** Return a string chopped to a given :term:`textual width`

    Use :func:`~kitchen.text.display.textual_width_chop` and
    :func:`~kitchen.text.display.textual_width` instead::

        >>> msg = 'く ku ら ra と to み mi'
        >>> # Old way:
        >>> utf8_width_chop(msg, 5)
        (5, 'く ku')
        >>> # New way
        >>> from kitchen.text.converters import to_bytes
        >>> from kitchen.text.display import textual_width, textual_width_chop
        >>> (textual_width(msg), to_bytes(textual_width_chop(msg, 5)))
        (5, 'く ku')
    '''
    warnings.warn('kitchen.text.utf8.utf8_width_chop is deprecated.  Use'
        ' kitchen.text.display.textual_width_chop instead', DeprecationWarning,
        stacklevel=2)

    if chop == None:
        return textual_width(msg), msg

    as_bytes = not isunicodestring(msg)

    chopped_msg = textual_width_chop(msg, chop)
    if as_bytes:
        chopped_msg = to_bytes(chopped_msg)
    return textual_width(chopped_msg), chopped_msg

def utf8_width_fill(msg, fill, chop=None, left=True, prefix='', suffix=''):
    '''**Deprecated** Pad a :term:`utf-8` string to fill a specified width

    Use :func:`~kitchen.text.display.byte_string_textual_width_fill` instead
    '''
    warnings.warn('kitchen.text.utf8.utf8_width_fill is deprecated.  Use'
        ' kitchen.text.display.byte_string_textual_width_fill instead',
        DeprecationWarning, stacklevel=2)

    return byte_string_textual_width_fill(msg, fill, chop=chop, left=left,
            prefix=prefix, suffix=suffix)

def utf8_text_wrap(text, width=70, initial_indent='', subsequent_indent=''):
    '''**Deprecated** Similar to :func:`textwrap.wrap` but understands
    :term:`utf-8` data and doesn't screw up lists/blocks/etc

    Use :func:`kitchen.text.display.wrap` instead
    '''
    warnings.warn('kitchen.text.utf8.utf8_text_wrap is deprecated.  Use'
        ' kitchen.text.display.wrap instead',
        DeprecationWarning, stacklevel=2)

    as_bytes = not isunicodestring(text)

    text = to_unicode(text)
    lines = wrap(text, width=width, initial_indent=initial_indent,
            subsequent_indent=subsequent_indent)
    if as_bytes:
        lines = [to_bytes(m) for m in lines]

    return lines

def utf8_text_fill(text, *args, **kwargs):
    '''**Deprecated** Similar to :func:`textwrap.fill` but understands
    :term:`utf-8` strings and doesn't screw up lists/blocks/etc.

    Use :func:`kitchen.text.display.fill` instead.
    '''
    warnings.warn('kitchen.text.utf8.utf8_text_fill is deprecated.  Use'
        ' kitchen.text.display.fill instead',
        DeprecationWarning, stacklevel=2)
    # This assumes that all args. are utf8.
    return fill(text, *args, **kwargs)

def _utf8_width_le(width, *args):
    '''**Deprecated** Convert the arguments to unicode and use
    :func:`kitchen.text.display._textual_width_le` instead.
    '''
    warnings.warn('kitchen.text.utf8._utf8_width_le is deprecated.  Use'
        ' kitchen.text.display._textual_width_le instead',
        DeprecationWarning, stacklevel=2)
    # This assumes that all args. are utf8.
    return _textual_width_le(width, to_unicode(''.join(args)))

__all__ = ('utf8_text_fill', 'utf8_text_wrap', 'utf8_valid', 'utf8_width',
        'utf8_width_chop', 'utf8_width_fill')
