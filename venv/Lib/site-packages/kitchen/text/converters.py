# -*- coding: utf-8 -*-
#
# Copyright (c) 2011-2012 Red Hat, Inc.
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
#   Seth Vidal
#
# Portions of code taken from yum/i18n.py and
# python-fedora: fedora/textutils.py

'''
Functions to handle conversion of byte :class:`bytes` and :class:`str`
strings.

.. versionchanged:: kitchen 0.2a2 ; API kitchen.text 2.0.0
    Added :func:`~kitchen.text.converters.getwriter`

.. versionchanged:: kitchen 0.2.2  ; API kitchen.text 2.1.0
    Added :func:`~kitchen.text.converters.exception_to_unicode`,
    :func:`~kitchen.text.converters.exception_to_bytes`,
    :data:`~kitchen.text.converters.EXCEPTION_CONVERTERS`,
    and :data:`~kitchen.text.converters.BYTE_EXCEPTION_CONVERTERS`

.. versionchanged:: kitchen 1.0.1 ; API kitchen.text 2.1.1
    Deprecated :data:`~kitchen.text.converters.BYTE_EXCEPTION_CONVERTERS` as
    we've simplified :func:`~kitchen.text.converters.exception_to_unicode` and
    :func:`~kitchen.text.converters.exception_to_bytes` to make it unnecessary

'''
from base64 import b64encode, b64decode

import codecs
import warnings
import xml.sax.saxutils

from kitchen.text.exceptions import ControlCharError, XmlEncodeError
from kitchen.text.misc import guess_encoding, html_entities_unescape, \
        isbytestring, isunicodestring, process_control_chars

#: Aliases for the utf-8 codec
_UTF8_ALIASES = frozenset(('utf-8', 'UTF-8', 'utf8', 'UTF8', 'utf_8', 'UTF_8',
    'utf', 'UTF', 'u8', 'U8'))
#: Aliases for the latin-1 codec
_LATIN1_ALIASES = frozenset(('latin-1', 'LATIN-1', 'latin1', 'LATIN1',
    'latin', 'LATIN', 'l1', 'L1', 'cp819', 'CP819', '8859', 'iso8859-1',
    'ISO8859-1', 'iso-8859-1', 'ISO-8859-1'))

# EXCEPTION_CONVERTERS is defined below due to using to_unicode

def to_unicode(obj, encoding='utf-8', errors='replace', nonstring=None,
        non_string=None):
    '''Convert an object into a :class:`str` string

    :arg obj: Object to convert to a :class:`str` string.  This should
        normally be a byte :class:`bytes`
    :kwarg encoding: What encoding to try converting the byte :class:`bytes` as.
        Defaults to :term:`utf-8`
    :kwarg errors: If errors are found while decoding, perform this action.
        Defaults to ``replace`` which replaces the invalid bytes with
        a character that means the bytes were unable to be decoded.  Other
        values are the same as the error handling schemes in the `codec base
        classes
        <http://docs.python.org/library/codecs.html#codec-base-classes>`_.
        For instance ``strict`` which raises an exception and ``ignore`` which
        simply omits the non-decodable characters.
    :kwarg nonstring: How to treat nonstring values.  Possible values are:

        :simplerepr: Attempt to call the object's "simple representation"
            method and return that value.  Python-2.3+ has two methods that
            try to return a simple representation: :meth:`object.__unicode__`
            and :meth:`object.__str__`.  We first try to get a usable value
            from :meth:`object.__unicode__`.  If that fails we try the same
            with :meth:`object.__str__`.
        :empty: Return an empty :class:`str` string
        :strict: Raise a :exc:`TypeError`
        :passthru: Return the object unchanged
        :repr: Attempt to return a :class:`str` string of the repr of the
            object

        Default is ``simplerepr``

    :kwarg non_string: *Deprecated* Use :attr:`nonstring` instead
    :raises TypeError: if :attr:`nonstring` is ``strict`` and
        a non-:class:`basestring` object is passed in or if :attr:`nonstring`
        is set to an unknown value
    :raises UnicodeDecodeError: if :attr:`errors` is ``strict`` and
        :attr:`obj` is not decodable using the given encoding
    :returns: :class:`str` string or the original object depending on the
        value of :attr:`nonstring`.

    Usually this should be used on a byte :class:`bytes` but it can take both
    byte :class:`bytes` and :class:`str` strings intelligently.  Nonstring
    objects are handled in different ways depending on the setting of the
    :attr:`nonstring` parameter.

    The default values of this function are set so as to always return
    a :class:`str` string and never raise an error when converting from
    a byte :class:`bytes` to a :class:`str` string.  However, when you do
    not pass validly encoded text (or a nonstring object), you may end up with
    output that you don't expect.  Be sure you understand the requirements of
    your data, not just ignore errors by passing it through this function.

    .. versionchanged:: 0.2.1a2
        Deprecated :attr:`non_string` in favor of :attr:`nonstring` parameter and changed
        default value to ``simplerepr``
    '''
    # Could use isbasestring/isunicode here but we want this code to be as
    # fast as possible
    if isinstance(obj, str):
        return obj

    if isinstance(obj, (bytes, bytearray)):
        if encoding in _UTF8_ALIASES:
            return str(obj, 'utf-8', errors)
        if encoding in _LATIN1_ALIASES:
            return obj.decode('latin-1', errors)
        return obj.decode(encoding, errors)

    if non_string:
        warnings.warn('non_string is a deprecated parameter of'
            ' to_unicode().  Use nonstring instead', DeprecationWarning,
            stacklevel=2)
        if not nonstring:
            nonstring = non_string

    if not nonstring:
        nonstring = 'simplerepr'
    if nonstring == 'empty':
        return ''
    elif nonstring == 'passthru':
        return obj
    elif nonstring == 'simplerepr':
        try:
            simple = str(obj)
        except UnicodeError:
            try:
                simple = obj.__str__()
            except (UnicodeError, AttributeError):
                simple = ''
        if not isunicodestring(simple):
            return str(simple, encoding, errors)
        return simple
    elif nonstring in ('repr', 'strict'):
        obj_repr = repr(obj)
        if not isunicodestring(obj_repr):
            obj_repr = str(obj_repr, encoding, errors)
        if nonstring == 'repr':
            return obj_repr
        raise TypeError('to_unicode was given "%(obj)s" which is neither'
            ' a byte string (str) or a unicode string' %
            {'obj': obj_repr.encode(encoding, 'replace')})

    raise TypeError('nonstring value, %(param)s, is not set to a valid'
        ' action' % {'param': nonstring})

def to_bytes(obj, encoding='utf-8', errors='replace', nonstring=None,
        non_string=None):
    '''Convert an object into a byte :class:`bytes`

    :arg obj: Object to convert to a byte :class:`bytes`.  This should normally
        be a :class:`str` string.
    :kwarg encoding: Encoding to use to convert the :class:`str` string
        into a byte :class:`bytes`.  Defaults to :term:`utf-8`.
    :kwarg errors: If errors are found while encoding, perform this action.
        Defaults to ``replace`` which replaces the invalid bytes with
        a character that means the bytes were unable to be encoded.  Other
        values are the same as the error handling schemes in the `codec base
        classes
        <http://docs.python.org/library/codecs.html#codec-base-classes>`_.
        For instance ``strict`` which raises an exception and ``ignore`` which
        simply omits the non-encodable characters.
    :kwarg nonstring: How to treat nonstring values.  Possible values are:

        :simplerepr: Attempt to call the object's "simple representation"
            method and return that value.  Python-2.3+ has two methods that
            try to return a simple representation: :meth:`object.__unicode__`
            and :meth:`object.__str__`.  We first try to get a usable value
            from :meth:`object.__str__`.  If that fails we try the same
            with :meth:`object.__unicode__`.
        :empty: Return an empty byte :class:`bytes`
        :strict: Raise a :exc:`TypeError`
        :passthru: Return the object unchanged
        :repr: Attempt to return a byte :class:`bytes` of the :func:`repr` of the
            object

        Default is ``simplerepr``.

    :kwarg non_string: *Deprecated* Use :attr:`nonstring` instead.
    :raises TypeError: if :attr:`nonstring` is ``strict`` and
        a non-:class:`basestring` object is passed in or if :attr:`nonstring`
        is set to an unknown value.
    :raises UnicodeEncodeError: if :attr:`errors` is ``strict`` and all of the
        bytes of :attr:`obj` are unable to be encoded using :attr:`encoding`.
    :returns: byte :class:`bytes` or the original object depending on the value
        of :attr:`nonstring`.

    .. warning::

        If you pass a byte :class:`bytes` into this function the byte
        :class:`bytes` is returned unmodified.  It is **not** re-encoded with
        the specified :attr:`encoding`.  The easiest way to achieve that is::

            to_bytes(to_unicode(text), encoding='utf-8')

        The initial :func:`to_unicode` call will ensure text is
        a :class:`str` string.  Then, :func:`to_bytes` will turn that into
        a byte :class:`bytes` with the specified encoding.

    Usually, this should be used on a :class:`str` string but it can take
    either a byte :class:`bytes` or a :class:`str` string intelligently.
    Nonstring objects are handled in different ways depending on the setting
    of the :attr:`nonstring` parameter.

    The default values of this function are set so as to always return a byte
    :class:`bytes` and never raise an error when converting from unicode to
    bytes.  However, when you do not pass an encoding that can validly encode
    the object (or a non-string object), you may end up with output that you
    don't expect.  Be sure you understand the requirements of your data, not
    just ignore errors by passing it through this function.

    .. versionchanged:: 0.2.1a2
        Deprecated :attr:`non_string` in favor of :attr:`nonstring` parameter
        and changed default value to ``simplerepr``
    '''
    # Could use isbasestring, isbytestring here but we want this to be as fast
    # as possible
    if isinstance(obj, (bytes, bytearray)):
        return obj
    if isinstance(obj, str):
        return obj.encode(encoding, errors)

    if non_string:
        warnings.warn('non_string is a deprecated parameter of'
            ' to_bytes().  Use nonstring instead', DeprecationWarning,
            stacklevel=2)
        if not nonstring:
            nonstring = non_string
    if not nonstring:
        nonstring = 'simplerepr'

    if nonstring == 'empty':
        return b''
    elif nonstring == 'passthru':
        return obj
    elif nonstring == 'simplerepr':
        simple = str(obj)
        simple = simple.encode(encoding, 'replace')
        return simple
    elif nonstring in ('repr', 'strict'):
        try:
            obj_repr = repr(obj)
        except (AttributeError, UnicodeError):
            obj_repr = ''
        if nonstring == 'repr':
            obj_repr = obj_repr.encode(encoding, errors)
            return obj_repr
        raise TypeError('to_bytes was given "%(obj)s" which is neither'
            ' a unicode string or a byte string (str)' % {'obj': obj_repr})

    raise TypeError('nonstring value, %(param)s, is not set to a valid'
        ' action' % {'param': nonstring})

def getwriter(encoding):
    '''Return a :class:`codecs.StreamWriter` that resists tracing back.

    :arg encoding: Encoding to use for transforming :class:`str` strings
        into byte :class:`bytes`.
    :rtype: :class:`codecs.StreamWriter`
    :returns: :class:`~codecs.StreamWriter` that you can instantiate to wrap output
        streams to automatically translate :class:`str` strings into :attr:`encoding`.

    This is a reimplemetation of :func:`codecs.getwriter` that returns
    a :class:`~codecs.StreamWriter` that resists issuing tracebacks.  The
    :class:`~codecs.StreamWriter` that is returned uses
    :func:`kitchen.text.converters.to_bytes` to convert :class:`str`
    strings into byte :class:`bytes`.  The departures from
    :func:`codecs.getwriter` are:

    1) The :class:`~codecs.StreamWriter` that is returned will take byte
       :class:`bytes` as well as :class:`str` strings.  Any byte
       :class:`bytes` will be passed through unmodified.
    2) The default error handler for unknown bytes is to ``replace`` the bytes
       with the unknown character (``?`` in most ascii-based encodings, ``�``
       in the utf encodings) whereas :func:`codecs.getwriter` defaults to
       ``strict``.  Like :class:`codecs.StreamWriter`, the returned
       :class:`~codecs.StreamWriter` can have its error handler changed in
       code by setting ``stream.errors = 'new_handler_name'``

    Example usage::

        $ LC_ALL=C python
        >>> import sys
        >>> from kitchen.text.converters import getwriter
        >>> UTF8Writer = getwriter('utf-8')
        >>> unwrapped_stdout = sys.stdout
        >>> sys.stdout = UTF8Writer(unwrapped_stdout)
        >>> print 'caf\\xc3\\xa9'
        café
        >>> print u'caf\\xe9'
        café
        >>> ASCIIWriter = getwriter('ascii')
        >>> sys.stdout = ASCIIWriter(unwrapped_stdout)
        >>> print 'caf\\xc3\\xa9'
        café
        >>> print u'caf\\xe9'
        caf?

    .. seealso::

        API docs for :class:`codecs.StreamWriter` and :func:`codecs.getwriter`
        and `Print Fails <http://wiki.python.org/moin/PrintFails>`_ on the
        python wiki.

    .. versionadded:: kitchen 0.2a2, API: kitchen.text 1.1.0
    '''
    class _StreamWriter(codecs.StreamWriter):
        # :W0223: We don't need to implement all methods of StreamWriter.
        #   This is not the actual class that gets used but a replacement for
        #   the actual class.
        # :C0111: We're implementing an API from the stdlib.  Just point
        #   people at that documentation instead of writing docstrings here.
        #pylint:disable-msg=W0223,C0111
        def __init__(self, stream, errors='replace'):
            codecs.StreamWriter.__init__(self, stream, errors)

        def encode(self, msg, errors='replace'):
            print(type(msg))
            print(repr(msg))
            return (to_bytes(msg, encoding=self.encoding, errors=errors),
                    len(msg))

    _StreamWriter.encoding = encoding
    return _StreamWriter

def to_utf8(obj, errors='replace', non_string='passthru'):
    '''*Deprecated*

    Convert :class:`str` to an encoded :term:`utf-8` byte :class:`bytes`.
    You should be using :func:`to_bytes` instead::

        to_bytes(obj, encoding='utf-8', non_string='passthru')
    '''
    warnings.warn('kitchen.text.converters.to_utf8 is deprecated.  Use'
        ' kitchen.text.converters.to_bytes(obj, encoding="utf-8",'
        ' nonstring="passthru" instead.', DeprecationWarning, stacklevel=2)
    return to_bytes(obj, encoding='utf-8', errors=errors,
            nonstring=non_string)

### str is also the type name for byte strings so it's not a good name for
### something that can return unicode strings
def to_str(obj):
    '''*Deprecated*

    This function converts something to a byte :class:`bytes` if it isn't one.
    It's used to call :func:`str` or :func:`unicode` on the object to get its
    simple representation without danger of getting a :exc:`UnicodeError`.
    You should be using :func:`to_unicode` or :func:`to_bytes` explicitly
    instead.

    If you need :class:`str` strings::

        to_unicode(obj, nonstring='simplerepr')

    If you need byte :class:`bytes`::

        to_bytes(obj, nonstring='simplerepr')
    '''
    warnings.warn('to_str is deprecated.  Use to_unicode or to_bytes'
        ' instead.  See the to_str docstring for porting information.',
        DeprecationWarning, stacklevel=2)
    return to_bytes(obj, nonstring='simplerepr')

# Exception message extraction functions
EXCEPTION_CONVERTERS = (lambda e: e.args[0], lambda e: e)
''' Tuple of functions to try to use to convert an exception into a string
    representation.  Its main use is to extract a string (:class:`str` or
    :class:`bytes`) from an exception object in :func:`exception_to_unicode` and
    :func:`exception_to_bytes`.  The functions here will try the exception's
    ``args[0]`` and the exception itself (roughly equivalent to
    `str(exception)`) to extract the message. This is only a default and can
    be easily overridden when calling those functions.  There are several
    reasons you might wish to do that.  If you have exceptions where the best
    string representing the exception is not returned by the default
    functions, you can add another function to extract from a different
    field::

        from kitchen.text.converters import (EXCEPTION_CONVERTERS,
                exception_to_unicode)

        class MyError(Exception):
            def __init__(self, message):
                self.value = message

        c = [lambda e: e.value]
        c.extend(EXCEPTION_CONVERTERS)
        try:
            raise MyError('An Exception message')
        except MyError, e:
            print exception_to_unicode(e, converters=c)

    Another reason would be if you're converting to a byte :class:`bytes` and
    you know the :class:`bytes` needs to be a non-:term:`utf-8` encoding.
    :func:`exception_to_bytes` defaults to :term:`utf-8` but if you convert
    into a byte :class:`bytes` explicitly using a converter then you can choose
    a different encoding::

        from kitchen.text.converters import (EXCEPTION_CONVERTERS,
                exception_to_bytes, to_bytes)
        c = [lambda e: to_bytes(e.args[0], encoding='euc_jp'),
                lambda e: to_bytes(e, encoding='euc_jp')]
        c.extend(EXCEPTION_CONVERTERS)
        try:
            do_something()
        except Exception, e:
            log = open('logfile.euc_jp', 'a')
            log.write('%s\n' % exception_to_bytes(e, converters=c)
            log.close()

    Each function in this list should take the exception as its sole argument
    and return a string containing the message representing the exception.
    The functions may return the message as a :byte class:`bytes`,
    a :class:`str` string, or even an object if you trust the object to
    return a decent string representation.  The :func:`exception_to_unicode`
    and :func:`exception_to_bytes` functions will make sure to convert the
    string to the proper type before returning.

    .. versionadded:: 0.2.2
'''

BYTE_EXCEPTION_CONVERTERS = (lambda e: to_bytes(e.args[0]), to_bytes)
'''*Deprecated*: Use :data:`EXCEPTION_CONVERTERS` instead.

    Tuple of functions to try to use to convert an exception into a string
    representation.  This tuple is similar to the one in
    :data:`EXCEPTION_CONVERTERS` but it's used with :func:`exception_to_bytes`
    instead.  Ideally, these functions should do their best to return the data
    as a byte :class:`bytes` but the results will be run through
    :func:`to_bytes` before being returned.

    .. versionadded:: 0.2.2
    .. versionchanged:: 1.0.1
        Deprecated as simplifications allow :data:`EXCEPTION_CONVERTERS` to
        perform the same function.
'''

def exception_to_unicode(exc, converters=EXCEPTION_CONVERTERS):
    '''Convert an exception object into a unicode representation

    :arg exc: Exception object to convert
    :kwarg converters: List of functions to use to convert the exception into
        a string.  See :data:`EXCEPTION_CONVERTERS` for the default value and
        an example of adding other converters to the defaults.  The functions
        in the list are tried one at a time to see if they can extract
        a string from the exception.  The first one to do so without raising
        an exception is used.
    :returns: :class:`str` string representation of the exception.  The
        value extracted by the :attr:`converters` will be converted into
        :class:`str` before being returned using the :term:`utf-8`
        encoding.  If you know you need to use an alternate encoding add
        a function that does that to the list of functions in
        :attr:`converters`)

    .. versionadded:: 0.2.2
    '''
    msg = '<exception failed to convert to text>'
    for func in converters:
        try:
            msg = func(exc)
        except:
            pass
        else:
            break
    return to_unicode(msg)

def exception_to_bytes(exc, converters=EXCEPTION_CONVERTERS):
    '''Convert an exception object into a str representation

    :arg exc: Exception object to convert
    :kwarg converters: List of functions to use to convert the exception into
        a string.  See :data:`EXCEPTION_CONVERTERS` for the default value and
        an example of adding other converters to the defaults.  The functions
        in the list are tried one at a time to see if they can extract
        a string from the exception.  The first one to do so without raising
        an exception is used.
    :returns: byte :class:`bytes` representation of the exception.  The value
        extracted by the :attr:`converters` will be converted into
        :class:`bytes` before being returned using the :term:`utf-8` encoding.
        If you know you need to use an alternate encoding add a function that
        does that to the list of functions in :attr:`converters`)

    .. versionadded:: 0.2.2
    .. versionchanged:: 1.0.1
        Code simplification allowed us to switch to using
        :data:`EXCEPTION_CONVERTERS` as the default value of
        :attr:`converters`.
    '''
    msg = b'<exception failed to convert to text>'
    for func in converters:
        try:
            msg = func(exc)
        except:
            pass
        else:
            break
    return to_bytes(msg)

#
# XML Related Functions
#

def unicode_to_xml(string, encoding='utf-8', attrib=False,
        control_chars='replace'):
    '''Take a :class:`str` string and turn it into a byte :class:`bytes`
    suitable for xml

    :arg string: :class:`str` string to encode into an XML compatible byte
        :class:`bytes`
    :kwarg encoding: encoding to use for the returned byte :class:`bytes`.
        Default is to encode to :term:`UTF-8`.  If some of the characters in
        :attr:`string` are not encodable in this encoding, the unknown
        characters will be entered into the output string using xml character
        references.
    :kwarg attrib: If :data:`True`, quote the string for use in an xml
        attribute.  If :data:`False` (default), quote for use in an xml text
        field.
    :kwarg control_chars: :term:`control characters` are not allowed in XML
        documents.  When we encounter those we need to know what to do.  Valid
        options are:

        :replace: (default) Replace the control characters with ``?``
        :ignore: Remove the characters altogether from the output
        :strict: Raise an :exc:`~kitchen.text.exceptions.XmlEncodeError`  when
            we encounter a :term:`control character`

    :raises kitchen.text.exceptions.XmlEncodeError: If :attr:`control_chars`
        is set to ``strict`` and the string to be made suitable for output to
        xml contains :term:`control characters` or if :attr:`string` is not
        a :class:`str` string then we raise this exception.
    :raises ValueError: If :attr:`control_chars` is set to something other than
        ``replace``, ``ignore``, or ``strict``.
    :rtype: byte :class:`bytes`
    :returns: representation of the :class:`str` string as a valid XML
        byte :class:`bytes`

    XML files consist mainly of text encoded using a particular charset.  XML
    also denies the use of certain bytes in the encoded text (example: ``ASCII
    Null``).  There are also special characters that must be escaped if they
    are present in the input (example: ``<``).  This function takes care of
    all of those issues for you.

    There are a few different ways to use this function depending on your
    needs.  The simplest invocation is like this::

       unicode_to_xml(u'String with non-ASCII characters: <"á と">')

    This will return the following to you, encoded in :term:`utf-8`::

      'String with non-ASCII characters: &lt;"á と"&gt;'

    Pretty straightforward.  Now, what if you need to encode your document in
    something other than :term:`utf-8`?  For instance, ``latin-1``?  Let's
    see::

       unicode_to_xml(u'String with non-ASCII characters: <"á と">', encoding='latin-1')
       'String with non-ASCII characters: &lt;"á &#12392;"&gt;'

    Because the ``と`` character is not available in the ``latin-1`` charset,
    it is replaced with ``&#12392;`` in our output.  This is an xml character
    reference which represents the character at unicode codepoint ``12392``, the
    ``と`` character.

    When you want to reverse this, use :func:`xml_to_unicode` which will turn
    a byte :class:`bytes` into a :class:`str` string and replace the xml
    character references with the unicode characters.

    XML also has the quirk of not allowing :term:`control characters` in its
    output.  The :attr:`control_chars` parameter allows us to specify what to
    do with those.  For use cases that don't need absolute character by
    character fidelity (example: holding strings that will just be used for
    display in a GUI app later), the default value of ``replace`` works well::

        unicode_to_xml(u'String with disallowed control chars: \\u0000\\u0007')
        'String with disallowed control chars: ??'

    If you do need to be able to reproduce all of the characters at a later
    date (examples: if the string is a key value in a database or a path on a
    filesystem) you have many choices.  Here are a few that rely on ``utf-7``,
    a verbose encoding that encodes :term:`control characters` (as well as
    non-:term:`ASCII` unicode values) to characters from within the
    :term:`ASCII` printable characters.  The good thing about doing this is
    that the code is pretty simple.  You just need to use ``utf-7`` both when
    encoding the field for xml and when decoding it for use in your python
    program::

        unicode_to_xml(u'String with unicode: と and control char: \u0007', encoding='utf7')
        'String with unicode: +MGg and control char: +AAc-'
        # [...]
        xml_to_unicode('String with unicode: +MGg and control char: +AAc-', encoding='utf7')
        u'String with unicode: と and control char: \u0007'

    As you can see, the ``utf-7`` encoding will transform even characters that
    would be representable in :term:`utf-8`.  This can be a drawback if you
    want unicode characters in the file to be readable without being decoded
    first.  You can work around this with increased complexity in your
    application code::

        encoding = 'utf-8'
        u_string = u'String with unicode: と and control char: \u0007'
        try:
            # First attempt to encode to utf8
            data = unicode_to_xml(u_string, encoding=encoding, errors='strict')
        except XmlEncodeError:
            # Fallback to utf-7
            encoding = 'utf-7'
            data = unicode_to_xml(u_string, encoding=encoding, errors='strict')
        write_tag('<mytag encoding=%s>%s</mytag>' % (encoding, data))
        # [...]
        encoding = tag.attributes.encoding
        u_string = xml_to_unicode(u_string, encoding=encoding)

    Using code similar to that, you can have some fields encoded using your
    default encoding and fallback to ``utf-7`` if there are :term:`control
    characters` present.

    .. note::

        If your goal is to preserve the :term:`control characters` you cannot
        save the entire file as ``utf-7`` and set the xml encoding parameter
        to ``utf-7`` if your goal is to preserve the :term:`control
        characters`.  Because XML doesn't allow :term:`control characters`,
        you have to encode those separate from any encoding work that the XML
        parser itself knows about.

    .. seealso::

        :func:`bytes_to_xml`
            if you're dealing with bytes that are non-text or of an unknown
            encoding that you must preserve on a byte for byte level.
        :func:`guess_encoding_to_xml`
            if you're dealing with strings in unknown encodings that you don't
            need to save with char-for-char fidelity.
    '''
    if not string:
        # Small optimization
        return b''
    try:
        process_control_chars(string, strategy=control_chars)
    except TypeError:
        raise XmlEncodeError('unicode_to_xml must have a unicode type as'
                ' the first argument.  Use bytes_string_to_xml for byte'
                ' strings.')
    except ValueError:
        raise ValueError('The control_chars argument to unicode_to_xml'
                ' must be one of ignore, replace, or strict')
    except ControlCharError as exc:
        raise XmlEncodeError(exc.args[0])

    # Escape characters that have special meaning in xml
    if attrib:
        string = xml.sax.saxutils.escape(string, entities={'"': "&quot;"})
    else:
        string = xml.sax.saxutils.escape(string)

    string = string.encode(encoding, 'xmlcharrefreplace')

    return string

def xml_to_unicode(byte_string, encoding='utf-8', errors='replace'):
    '''Transform a byte :class:`bytes` from an xml file into a :class:`str`
    string

    :arg byte_string: byte :class:`bytes` to decode
    :kwarg encoding: encoding that the byte :class:`bytes` is in
    :kwarg errors: What to do if not every character is  valid in
        :attr:`encoding`.  See the :func:`to_unicode` documentation for legal
        values.
    :rtype: :class:`str` string
    :returns: string decoded from :attr:`byte_string`

    This function attempts to reverse what :func:`unicode_to_xml` does.  It
    takes a byte :class:`bytes` (presumably read in from an xml file) and
    expands all the html entities into unicode characters and decodes the byte
    :class:`bytes` into a :class:`str` string.  One thing it cannot do is
    restore any :term:`control characters` that were removed prior to
    inserting into the file.  If you need to keep such characters you need to
    use :func:`xml_to_bytes` and :func:`bytes_to_xml` or use on of the
    strategies documented in :func:`unicode_to_xml` instead.
    '''
    string = to_unicode(byte_string, encoding=encoding, errors=errors)
    string = html_entities_unescape(string)
    return string

def byte_string_to_xml(byte_string, input_encoding='utf-8', errors='replace',
        output_encoding='utf-8', attrib=False, control_chars='replace'):
    '''Make sure a byte :class:`bytes` is validly encoded for xml output

    :arg byte_string: Byte :class:`bytes` to turn into valid xml output
    :kwarg input_encoding: Encoding of :attr:`byte_string`.  Default ``utf-8``
    :kwarg errors: How to handle errors encountered while decoding the
        :attr:`byte_string` into :class:`str` at the beginning of the
        process.  Values are:

        :replace: (default) Replace the invalid bytes with a ``?``
        :ignore: Remove the characters altogether from the output
        :strict: Raise an :exc:`UnicodeDecodeError` when we encounter
            a non-decodable character

    :kwarg output_encoding: Encoding for the xml file that this string will go
        into.  Default is ``utf-8``.  If all the characters in
        :attr:`byte_string` are not encodable in this encoding, the unknown
        characters will be entered into the output string using xml character
        references.
    :kwarg attrib: If :data:`True`, quote the string for use in an xml
        attribute.  If :data:`False` (default), quote for use in an xml text
        field.
    :kwarg control_chars: XML does not allow :term:`control characters`.  When
        we encounter those we need to know what to do.  Valid options are:

        :replace: (default) Replace the :term:`control characters` with ``?``
        :ignore: Remove the characters altogether from the output
        :strict: Raise an error when we encounter a :term:`control character`

    :raises XmlEncodeError: If :attr:`control_chars` is set to ``strict`` and
        the string to be made suitable for output to xml contains
        :term:`control characters` then we raise this exception.
    :raises UnicodeDecodeError: If errors is set to ``strict`` and the
        :attr:`byte_string` contains bytes that are not decodable using
        :attr:`input_encoding`, this error is raised
    :rtype: byte :class:`bytes`
    :returns: representation of the byte :class:`bytes` in the output encoding with
        any bytes that aren't available in xml taken care of.

    Use this when you have a byte :class:`bytes` representing text that you need
    to make suitable for output to xml.  There are several cases where this
    is the case.  For instance, if you need to transform some strings encoded
    in ``latin-1`` to :term:`utf-8` for output::

        utf8_string = byte_string_to_xml(latin1_string, input_encoding='latin-1')

    If you already have strings in the proper encoding you may still want to
    use this function to remove :term:`control characters`::

        cleaned_string = byte_string_to_xml(string, input_encoding='utf-8', output_encoding='utf-8')

    .. seealso::

        :func:`unicode_to_xml`
            for other ideas on using this function
    '''
    if not isbytestring(byte_string):
        raise XmlEncodeError('byte_string_to_xml can only take a byte'
                ' string as its first argument.  Use unicode_to_xml for'
                ' unicode (str) strings')

    # Decode the string into unicode
    u_string = str(byte_string, input_encoding, errors)
    return unicode_to_xml(u_string, encoding=output_encoding,
            attrib=attrib, control_chars=control_chars)

def xml_to_byte_string(byte_string, input_encoding='utf-8', errors='replace',
        output_encoding='utf-8'):
    '''Transform a byte :class:`bytes` from an xml file into :class:`str`
    string

    :arg byte_string: byte :class:`bytes` to decode
    :kwarg input_encoding: encoding that the byte :class:`bytes` is in
    :kwarg errors: What to do if not every character is valid in
        :attr:`encoding`.  See the :func:`to_unicode` docstring for legal
        values.
    :kwarg output_encoding: Encoding for the output byte :class:`bytes`
    :returns: :class:`str` string decoded from :attr:`byte_string`

    This function attempts to reverse what :func:`unicode_to_xml` does.  It
    takes a byte :class:`bytes` (presumably read in from an xml file) and
    expands all the html entities into unicode characters and decodes the
    byte :class:`bytes` into a :class:`str` string.  One thing it cannot do
    is restore any :term:`control characters` that were removed prior to
    inserting into the file.  If you need to keep such characters you need to
    use :func:`xml_to_bytes` and :func:`bytes_to_xml` or use one of the
    strategies documented in :func:`unicode_to_xml` instead.
    '''
    string = xml_to_unicode(byte_string, input_encoding, errors)
    return to_bytes(string, output_encoding, errors)

def bytes_to_xml(byte_string, *args, **kwargs):
    '''Return a byte :class:`bytes` encoded so it is valid inside of any xml
    file

    :arg byte_string: byte :class:`bytes` to transform
    :arg \*args, \*\*kwargs: extra arguments to this function are passed on to
        the function actually implementing the encoding.  You can use this to
        tweak the output in some cases but, as a general rule, you shouldn't
        because the underlying encoding function is not guaranteed to remain
        the same.
    :rtype: byte :class:`bytes` consisting of all :term:`ASCII` characters
    :returns: byte :class:`bytes` representation of the input.  This will be encoded
        using base64.

    This function is made especially to put binary information into xml
    documents.

    This function is intended for encoding things that must be preserved
    byte-for-byte.  If you want to encode a byte string that's text and don't
    mind losing the actual bytes you probably want to try :func:`byte_string_to_xml`
    or :func:`guess_encoding_to_xml` instead.

    .. note::

        Although the current implementation uses :func:`base64.b64encode` and
        there's no plans to change it, that isn't guaranteed.  If you want to
        make sure that you can encode and decode these messages it's best to
        use :func:`xml_to_bytes` if you use this function to encode.
    '''
    # Can you do this yourself?  Yes, you can.
    return b64encode(byte_string, *args, **kwargs)

def xml_to_bytes(byte_string, *args, **kwargs):
    '''Decode a string encoded using :func:`bytes_to_xml`

    :arg byte_string: byte :class:`bytes` to transform.  This should be a base64
        encoded sequence of bytes originally generated by :func:`bytes_to_xml`.
    :arg \*args, \*\*kwargs: extra arguments to this function are passed on to
        the function actually implementing the encoding.  You can use this to
        tweak the output in some cases but, as a general rule, you shouldn't
        because the underlying encoding function is not guaranteed to remain
        the same.
    :rtype: byte :class:`bytes`
    :returns: byte :class:`bytes` that's the decoded input

    If you've got fields in an xml document that were encoded with
    :func:`bytes_to_xml` then you want to use this function to undecode them.
    It converts a base64 encoded string into a byte :class:`bytes`.

    .. note::

        Although the current implementation uses :func:`base64.b64decode` and
        there's no plans to change it, that isn't guaranteed.  If you want to
        make sure that you can encode and decode these messages it's best to
        use :func:`bytes_to_xml` if you use this function to decode.
    '''
    return b64decode(byte_string, *args, **kwargs)

def guess_encoding_to_xml(string, output_encoding='utf-8', attrib=False,
        control_chars='replace'):
    '''Return a byte :class:`bytes` suitable for inclusion in xml

    :arg string: :class:`str` or byte :class:`bytes` to be transformed into
        a byte :class:`bytes` suitable for inclusion in xml.  If string is
        a byte :class:`bytes` we attempt to guess the encoding.  If we cannot guess,
        we fallback to ``latin-1``.
    :kwarg output_encoding: Output encoding for the byte :class:`bytes`.  This
        should match the encoding of your xml file.
    :kwarg attrib: If :data:`True`, escape the item for use in an xml
        attribute.  If :data:`False` (default) escape the item for use in
        a text node.
    :returns: :term:`utf-8` encoded byte :class:`bytes`

    '''
    # Unicode strings can just be run through unicode_to_xml()
    if isunicodestring(string):
        return unicode_to_xml(string, encoding=output_encoding,
                attrib=attrib, control_chars=control_chars)

    # Guess the encoding of the byte strings
    input_encoding = guess_encoding(string)

    # Return the new byte string
    return byte_string_to_xml(string, input_encoding=input_encoding,
            errors='replace', output_encoding=output_encoding,
            attrib=attrib, control_chars=control_chars)

def to_xml(string, encoding='utf-8', attrib=False, control_chars='ignore'):
    '''*Deprecated*: Use :func:`guess_encoding_to_xml` instead
    '''
    warnings.warn('kitchen.text.converters.to_xml is deprecated.  Use'
            ' kitchen.text.converters.guess_encoding_to_xml instead.',
            DeprecationWarning, stacklevel=2)
    return guess_encoding_to_xml(string, output_encoding=encoding,
            attrib=attrib, control_chars=control_chars)

__all__ = ('BYTE_EXCEPTION_CONVERTERS', 'EXCEPTION_CONVERTERS',
        'byte_string_to_xml', 'bytes_to_xml', 'exception_to_bytes',
        'exception_to_unicode', 'getwriter', 'guess_encoding_to_xml',
        'to_bytes', 'to_str', 'to_unicode', 'to_utf8', 'to_xml',
        'unicode_to_xml', 'xml_to_byte_string', 'xml_to_bytes',
        'xml_to_unicode')
