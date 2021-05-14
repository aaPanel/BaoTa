# -*- coding: utf-8 -*-
# Copyright (c) 2012 Red Hat, Inc
# Copyright (c) 2010 Seth Vidal
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
#   James Antill
#   Toshio Kuratomi <toshio@fedoraproject.org>
#   Seth Vidal
#
# Portions of this code taken from yum/misc.py and yum/i18n.py
'''
---------------------------------------------
Miscellaneous functions for manipulating text
---------------------------------------------

Collection of text functions that don't fit in another category.

.. versionchanged:: kitchen 1.2.0, API: kitchen.text 2.2.0
    Added :func:`~kitchen.text.misc.isbasestring`,
    :func:`~kitchen.text.misc.isbytestring`, and
    :func:`~kitchen.text.misc.isunicodestring` to help tell which string type
    is which on python2 and python3
'''
import html.entities
import itertools
import re

try:
    import chardet
except ImportError:
    chardet = None

from kitchen.text.exceptions import ControlCharError

# Define a threshold for chardet confidence.  If we fall below this we decode
# byte strings we're guessing about as latin1
_CHARDET_THRESHHOLD = 0.6

# ASCII control codes (the c0 codes) that are illegal in xml 1.0
# Also unicode control codes (the C1 codes): also illegal in xml
_CONTROL_CODES = frozenset(itertools.chain(range(0, 8), (11, 12), range(14, 32), range(128, 160)))
_CONTROL_CHARS = frozenset(map(chr, _CONTROL_CODES))
_IGNORE_TABLE = dict(zip(_CONTROL_CODES, [None] * len(_CONTROL_CODES)))
_REPLACE_TABLE = dict(zip(_CONTROL_CODES, ['?'] * len(_CONTROL_CODES)))

# _ENTITY_RE
_ENTITY_RE = re.compile(r'(?s)<[^>]*>|&#?\w+;')

def isbasestring(obj):
    '''Determine if obj is a byte :class:`bytes` or :class:`str` string

    In python2 this is eqiuvalent to isinstance(obj, basestring).  In python3
    it checks whether the object is an instance of str, bytes, or bytearray.
    This is an aid to porting code that needed to test whether an object was
    derived from basestring in python2 (commonly used in unicode-bytes
    conversion functions)

    :arg obj: Object to test
    :returns: True if the object is a :class:`basestring`.  Otherwise False.

    .. versionadded:: Kitchen: 1.2.0, API kitchen.text 2.2.0
    '''
    if isinstance(obj, (str, bytes, bytearray)):
        return True
    return False

def isbytestring(obj):
    '''Determine if obj is a byte :class:`bytes`

    In python2 this is equivalent to isinstance(obj, str).  In python3 it
    checks whether the object is an instance of bytes or bytearray.

    :arg obj: Object to test
    :returns: True if the object is a byte :class:`bytes`.  Otherwise, False.

    .. versionadded:: Kitchen: 1.2.0, API kitchen.text 2.2.0
    '''
    if isinstance(obj, (bytes, bytearray)):
        return True
    return False

def isunicodestring(obj):
    '''Determine if obj is a :class:`str` string

    In python2 this is equivalent to isinstance(obj, unicode).  In python3 it
    checks whether the object is an instance of :class:`bytes`.

    :arg obj: Object to test
    :returns: True if the object is a :class:`str` string.  Otherwise, False.

    .. versionadded:: Kitchen: 1.2.0, API kitchen.text 2.2.0
    '''
    if isinstance(obj, str):
        return True
    return False

def guess_encoding(byte_string, disable_chardet=False):
    '''Try to guess the encoding of a byte :class:`bytes`

    :arg byte_string: byte :class:`bytes` to guess the encoding of
    :kwarg disable_chardet: If this is True, we never attempt to use
        :mod:`chardet` to guess the encoding.  This is useful if you need to
        have reproducibility whether :mod:`chardet` is installed or not.
        Default: :data:`False`.
    :raises TypeError: if :attr:`byte_string` is not a byte :class:`bytes` type
    :returns: string containing a guess at the encoding of
        :attr:`byte_string`.  This is appropriate to pass as the encoding
        argument when encoding and decoding unicode strings.

    We start by attempting to decode the byte :class:`bytes` as :term:`UTF-8`.
    If this succeeds we tell the world it's :term:`UTF-8` text.  If it doesn't
    and :mod:`chardet` is installed on the system and :attr:`disable_chardet`
    is False this function will use it to try detecting the encoding of
    :attr:`byte_string`.  If it is not installed or :mod:`chardet` cannot
    determine the encoding with a high enough confidence then we rather
    arbitrarily claim that it is ``latin-1``.  Since ``latin-1`` will encode
    to every byte, decoding from ``latin-1`` to :class:`str` will not
    cause :exc:`UnicodeErrors` although the output might be mangled.
    '''
    if not isbytestring(byte_string):
        raise TypeError('byte_string must be a byte string (bytes, bytearray)')
    input_encoding = 'utf-8'
    try:
        str(byte_string, input_encoding, 'strict')
    except UnicodeDecodeError:
        input_encoding = None

    if not input_encoding and chardet and not disable_chardet:
        detection_info = chardet.detect(byte_string)
        if detection_info['confidence'] >= _CHARDET_THRESHHOLD:
            input_encoding = detection_info['encoding']

    if not input_encoding:
        input_encoding = 'latin-1'

    return input_encoding

def str_eq(str1, str2, encoding='utf-8', errors='replace'):
    '''Compare two strings, converting to byte :class:`bytes` if one is
    :class:`str`

    :arg str1: First string to compare
    :arg str2: Second string to compare
    :kwarg encoding: If we need to convert one string into a byte :class:`bytes`
        to compare, the encoding to use.  Default is :term:`utf-8`.
    :kwarg errors: What to do if we encounter errors when encoding the string.
        See the :func:`kitchen.text.converters.to_bytes` documentation for
        possible values.  The default is ``replace``.

    This function prevents :exc:`UnicodeError` (python-2.4 or less) and
    :exc:`UnicodeWarning` (python 2.5 and higher) when we compare
    a :class:`str` string to a byte :class:`bytes`.  The errors normally
    arise because the conversion is done to :term:`ASCII`.  This function
    lets you convert to :term:`utf-8` or another encoding instead.

    .. note::

        When we need to convert one of the strings from :class:`str` in
        order to compare them we convert the :class:`str` string into
        a byte :class:`bytes`.  That means that strings can compare differently
        if you use different encodings for each.

    Note that ``str1 == str2`` is faster than this function if you can accept
    the following limitations:

    * Limited to python-2.5+ (otherwise a :exc:`UnicodeDecodeError` may be
      thrown)
    * Will generate a :exc:`UnicodeWarning` if non-:term:`ASCII` byte
      :class:`bytes` is compared to :class:`str` string.
    '''
    try:
        return (not str1 < str2) and (not str1 > str2)
    except TypeError:
        pass

    if isunicodestring(str1):
        str1 = str1.encode(encoding, errors)
    else:
        str2 = str2.encode(encoding, errors)
    if str1 == str2:
        return True

    return False

def process_control_chars(string, strategy='replace'):
    '''Look for and transform :term:`control characters` in a string

    :arg string: string to search for and transform :term:`control characters`
        within
    :kwarg strategy: XML does not allow :term:`ASCII` :term:`control
        characters`.  When we encounter those we need to know what to do.
        Valid options are:

        :replace: (default) Replace the :term:`control characters`
            with ``"?"``
        :ignore: Remove the characters altogether from the output
        :strict: Raise a :exc:`~kitchen.text.exceptions.ControlCharError` when
            we encounter a control character
    :raises TypeError: if :attr:`string` is not a unicode string.
    :raises ValueError: if the strategy is not one of replace, ignore, or
        strict.
    :raises kitchen.text.exceptions.ControlCharError: if the strategy is
        ``strict`` and a :term:`control character` is present in the
        :attr:`string`
    :returns: :class:`str` string with no :term:`control characters` in
        it.

    .. versionchanged:: kitchen 1.2.0, API: kitchen.text 2.2.0
        Strip out the C1 control characters in addition to the C0 control
        characters.
    '''
    if not isunicodestring(string):
        raise TypeError('process_control_char must have a unicode type'
                ' (str) as the first argument.')
    if strategy not in ('replace', 'ignore', 'strict'):
        raise ValueError('The strategy argument to process_control_chars'
                ' must be one of ignore, replace, or strict')

    # Most strings don't have control chars and translating carries
    # a higher cost than testing whether the chars are in the string
    # So only translate if necessary
    if not _CONTROL_CHARS.isdisjoint(string):
        if strategy == 'replace':
            control_table = _REPLACE_TABLE
        elif strategy == 'ignore':
            control_table = _IGNORE_TABLE
        else:
            # strategy can only equal 'strict'
            raise ControlCharError('ASCII control code present in string'
                    ' input')
        string = string.translate(control_table)

    return string

# Originally written by Fredrik Lundh (January 15, 2003) and placed in the
# public domain::
#
#   Unless otherwise noted, source code can be be used freely. Examples, test
#   scripts and other short code fragments can be considered as being in the
#   public domain.
#
# http://effbot.org/zone/re-sub.htm#unescape-html
# http://effbot.org/zone/copyright.htm
#
def html_entities_unescape(string):
    '''Substitute unicode characters for HTML entities

    :arg string: :class:`str` string to substitute out html entities
    :raises TypeError: if something other than a :class:`str` string is
        given
    :rtype: :class:`str` string
    :returns: The plain text without html entities
    '''
    def fixup(match):
        string = match.group(0)
        if string[:1] == "<":
            return "" # ignore tags
        if string[:2] == "&#":
            try:
                if string[:3] == "&#x":
                    return chr(int(string[3:-1], 16))
                else:
                    return chr(int(string[2:-1]))
            except ValueError:
                # If the value is outside the unicode codepoint range, leave
                # it in the output as is
                pass
        elif string[:1] == "&":
            entity = html.entities.entitydefs.get(string[1:-1])
            if entity:
                if entity[:2] == "&#":
                    try:
                        return chr(int(entity[2:-1]))
                    except ValueError:
                        # If the value is outside the unicode codepoint range,
                        # leave it in the output as is
                        pass
                else:
                    return entity
        return string # leave as is

    if not isunicodestring(string):
        raise TypeError('html_entities_unescape must have a unicode type (str)'
                ' for its first argument')
    return re.sub(_ENTITY_RE, fixup, string)

def byte_string_valid_xml(byte_string, encoding='utf-8'):
    '''Check that a byte :class:`bytes` would be valid in xml

    :arg byte_string: Byte :class:`bytes` to check
    :arg encoding: Encoding of the xml file.  Default: :term:`UTF-8`
    :returns: :data:`True` if the string is valid.  :data:`False` if it would
        be invalid in the xml file

    In some cases you'll have a whole bunch of byte strings and rather than
    transforming them to :class:`str` and back to byte :class:`bytes` for
    output to xml, you will just want to make sure they work with the xml file
    you're constructing.  This function will help you do that.  Example::

        ARRAY_OF_MOSTLY_UTF8_STRINGS = [...]
        processed_array = []
        for string in ARRAY_OF_MOSTLY_UTF8_STRINGS:
            if byte_string_valid_xml(string, 'utf-8'):
                processed_array.append(string)
            else:
                processed_array.append(guess_bytes_to_xml(string, encoding='utf-8'))
        output_xml(processed_array)
    '''
    if not isbytestring(byte_string):
        # Not a byte string
        return False

    try:
        u_string = str(byte_string, encoding)
    except UnicodeError:
        # Not encoded with the xml file's encoding
        return False

    data = frozenset(u_string)
    if data.intersection(_CONTROL_CHARS):
        # Contains control codes
        return False

    # The byte string is compatible with this xml file
    return True

def byte_string_valid_encoding(byte_string, encoding='utf-8'):
    '''Detect if a byte :class:`bytes` is valid in a specific encoding

    :arg byte_string: Byte :class:`bytes` to test for bytes not valid in this
        encoding
    :kwarg encoding: encoding to test against.  Defaults to :term:`UTF-8`.
    :returns: :data:`True` if there are no invalid :term:`UTF-8` characters.
        :data:`False` if an invalid character is detected.

    .. note::

        This function checks whether the byte :class:`bytes` is valid in the
        specified encoding.  It **does not** detect whether the byte
        :class:`bytes` actually was encoded in that encoding.  If you want that
        sort of functionality, you probably want to use
        :func:`~kitchen.text.misc.guess_encoding` instead.
    '''
    try:
        str(byte_string, encoding)
    except UnicodeError:
        # Not encoded with the xml file's encoding
        return False

    # byte string is valid in this encoding
    return True

__all__ = ('byte_string_valid_encoding', 'byte_string_valid_xml',
        'guess_encoding', 'html_entities_unescape', 'isbasestring',
        'isbytestring', 'isunicodestring', 'process_control_chars', 'str_eq')
