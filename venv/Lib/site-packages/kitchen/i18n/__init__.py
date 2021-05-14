# -*- coding: utf-8 -*-
#
# Copyright (c) 2010-2012 Red Hat, Inc
# Copyright (c) 2009 Milos Komarcevic
# Copyright (c) 2008 Tim Lauridsen
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
# Authors: James Antill
#   Milos Komarcevic
#   Toshio Kuratomi <toshio@fedoraproject.org>
#   Tim Lauridsen
#   Luke Macken <lmacken@redhat.com>
#   Seth Vidal <skvidal@fedoraproject.org>
#
# Portions of code taken from yum/i18n.py
# Portions of code adapted from |stdlib|_ gettext.py
'''
:term:`I18N` is an important piece of any modern program.  Unfortunately,
setting up :term:`i18n` in your program is often a confusing process.  The
functions provided here aim to make the programming side of that a little
easier.

Most projects will be able to do something like this when they startup::

    # myprogram/__init__.py:

    import os
    import sys

    from kitchen.i18n import easy_gettext_setup

    _, N_  = easy_gettext_setup('myprogram', localedirs=(
            os.path.join(os.path.realpath(os.path.dirname(__file__)), 'locale'),
            os.path.join(sys.prefix, 'lib', 'locale')
            ))

Then, in other files that have strings that need translating::

    # myprogram/commands.py:

    from myprogram import _, N_

    def print_usage():
        print _(u"""available commands are:
        --help              Display help
        --version           Display version of this program
        --bake-me-a-cake    as fast as you can
            """)

    def print_invitations(age):
        print _('Please come to my party.')
        print N_('I will be turning %(age)s year old',
            'I will be turning %(age)s years old', age) % {'age': age}

See the documentation of :func:`easy_gettext_setup` and
:func:`get_translation_object` for more details.

    .. seealso::

        :mod:`gettext`
            for details of how the python gettext facilities work
        `babel <http://babel.edgewall.org>`_
            The babel module for in depth information on gettext, :term:`message
            catalogs`, and translating your app.  babel provides some nice
            features for :term:`i18n` on top of :mod:`gettext`
'''
# Pylint disabled messages:
# :E1101: NewGNUTranslations is modeled as a replacement for GNUTranslations.
#   That module invokes the _parse message to create some of its attributes.
#   Pylint doesn't see those attributes being defined since it doesn't know
#   when _parse() is called.  We disable E1101 when accessing self._catalog
#   and self.plural for this reason.
# :C0103: We're replicating the gettext API here so we need to use method and
#   parameter names that mirror gettext.
# :C0111: We're replicating the gettext API here so for the gettext
#   translation object methods we point people at the stdlib docs

from kitchen.versioning import version_tuple_to_string

__version_info__ = ((2, 2, 0),)
__version__ = version_tuple_to_string(__version_info__)

import copy
from errno import ENOENT
import gettext
import itertools
import locale
import os
import sys
import warnings

# We use the _default_localedir definition in get_translation_object
try:
    from gettext import _default_localedir as _DEFAULT_LOCALEDIR
except ImportError:
    _DEFAULT_LOCALEDIR = os.path.join(sys.prefix, 'share', 'locale')

from kitchen.text.converters import to_bytes, to_unicode
from kitchen.text.misc import byte_string_valid_encoding, isbasestring

# We cache parts of the translation objects just like stdlib's gettext so that
# we don't reparse the message files and keep them in memory separately if the
# same catalog is opened twice.
_translations = {}

class DummyTranslations(gettext.NullTranslations):
    '''Safer version of :class:`gettext.NullTranslations`

    This Translations class doesn't translate the strings and is intended to
    be used as a fallback when there were errors setting up a real
    Translations object.  It's safer than :class:`gettext.NullTranslations` in
    its handling of byte :class:`bytes` vs :class:`str` strings.

    Unlike :class:`~gettext.NullTranslations`, this Translation class will
    never throw a :exc:`~exceptions.UnicodeError`.  The code that you have
    around a call to :class:`DummyTranslations` might throw
    a :exc:`~exceptions.UnicodeError` but at least that will be in code you
    control and can fix.  Also, unlike :class:`~gettext.NullTranslations` all
    of this Translation object's methods guarantee to return byte :class:`bytes`
    except for :meth:`ugettext` and :meth:`ungettext` which guarantee to
    return :class:`str` strings.

    When byte :class:`bytes` are returned, the strings will be encoded according
    to this algorithm:

    1) If a fallback has been added, the fallback will be called first.
       You'll need to consult the fallback to see whether it performs any
       encoding changes.
    2) If a byte :class:`bytes` was given, the same byte :class:`bytes` will
       be returned.
    3) If a :class:`str` string was given and :meth:`set_output_charset`
       has been called then we encode the string using the
       :attr:`output_charset`
    4) If a :class:`str` string was given and this is :meth:`gettext` or
       :meth:`ngettext` and :attr:`_charset` was set output in that charset.
    5) If a :class:`str` string was given and this is :meth:`gettext`
       or :meth:`ngettext` we encode it using 'utf-8'.
    6) If a :class:`str` string was given and this is :meth:`lgettext`
       or :meth:`lngettext` we encode using the value of
       :func:`locale.getpreferredencoding`

    For :meth:`ugettext` and :meth:`ungettext`, we go through the same set of
    steps with the following differences:

    * We transform byte :class:`bytes` into :class:`str` strings for
      these methods.
    * The encoding used to decode the byte :class:`bytes` is taken from
      :attr:`input_charset` if it's set, otherwise we decode using
      :term:`UTF-8`.

    .. attribute:: input_charset

        is an extension to the |stdlib|_ :mod:`gettext` that specifies what
        charset a message is encoded in when decoding a message to
        :class:`str`.  This is used for two purposes:

    1) If the message string is a byte :class:`bytes`, this is used to decode
       the string to a :class:`str` string before looking it up in the
       :term:`message catalog`.
    2) In :meth:`~kitchen.i18n.DummyTranslations.ugettext` and
       :meth:`~kitchen.i18n.DummyTranslations.ungettext` methods, if a byte
       :class:`bytes` is given as the message and is untranslated this is used
       as the encoding when decoding to :class:`str`.  This is different
       from :attr:`_charset` which may be set when a :term:`message catalog`
       is loaded because :attr:`input_charset` is used to describe an encoding
       used in a python source file while :attr:`_charset` describes the
       encoding used in the :term:`message catalog` file.

    Any characters that aren't able to be transformed from a byte :class:`bytes`
    to :class:`str` string or vice versa will be replaced with
    a replacement character (ie: ``u'�'`` in unicode based encodings, ``'?'`` in other
    :term:`ASCII` compatible encodings).

    .. seealso::

        :class:`gettext.NullTranslations`
            For information about what methods are available and what they do.

    .. versionchanged:: kitchen-1.1.0 ; API kitchen.i18n 2.1.0
        * Although we had adapted :meth:`gettext`, :meth:`ngettext`,
          :meth:`lgettext`, and :meth:`lngettext` to always return byte
          :class:`bytes`, we hadn't forced those byte :class:`bytes` to always be
          in a specified charset.  We now make sure that :meth:`gettext` and
          :meth:`ngettext` return byte :class:`bytes` encoded using
          :attr:`output_charset` if set, otherwise :attr:`charset` and if
          neither of those, :term:`UTF-8`.  With :meth:`lgettext` and
          :meth:`lngettext` :attr:`output_charset` if set, otherwise
          :func:`locale.getpreferredencoding`.
        * Make setting :attr:`input_charset` and :attr:`output_charset` also
          set those attributes on any fallback translation objects.

    .. versionchanged:: kitchen-1.2.0 ; API kitchen.i18n 2.2.0
        Add python2_api parameter to __init__()
    '''
    #pylint: disable-msg=C0103,C0111
    def __init__(self, fp=None, python2_api=True):
        gettext.NullTranslations.__init__(self, fp)

        # Python 2.3 compat
        if not hasattr(self, '_output_charset'):
            self._output_charset = None

        # Extension for making ugettext and ungettext more sane
        # 'utf-8' is only a default here.  Users can override.
        self._input_charset = 'utf-8'

        # Decide whether to mimic the python2 or python3 api
        self.python2_api = python2_api

    def _set_api(self):
        if self._python2_api:
            warnings.warn('Kitchen.i18n provides gettext objects that'
                    ' implement either the python2 or python3 gettext api.'
                    '  You are currently using the python2 api.  Consider'
                    ' switching to the python3 api by setting'
                    ' python2_api=False when creating the gettext object',
                    PendingDeprecationWarning, stacklevel=2)
            self.gettext = self._gettext
            self.lgettext = self._lgettext
            self.ugettext = self._ugettext
            self.ngettext = self._ngettext
            self.lngettext = self._lngettext
            self.ungettext = self._ungettext
        else:
            self.gettext = self._ugettext
            self.lgettext = self._lgettext
            self.ngettext = self._ungettext
            self.lngettext = self._lngettext
            self.ugettext = self._removed_method_factory('ugettext')
            self.ungettext = self._removed_method_factory('ungettext')

    def _removed_method_factory(self, name):
        def _removed_method(*args, **kwargs):
            raise AttributeError("'%s' object has no attribute '%s'" %
                    (self.__class__.__name__, name))
        return _removed_method

    def _set_python2_api(self, value):
        self._python2_api = value
        self._set_api()

    def _get_python2_api(self):
        return self._python2_api

    python2_api = property(_get_python2_api, _set_python2_api)

    def _set_input_charset(self, charset):
        if self._fallback:
            try:
                self._fallback.input_charset = charset
            except AttributeError:
                pass
        self._input_charset = charset

    def _get_input_charset(self):
        return self._input_charset

    input_charset = property(_get_input_charset, _set_input_charset)

    def set_output_charset(self, charset):
        '''Set the output charset

        This serves two purposes.  The normal
        :meth:`gettext.NullTranslations.set_output_charset` does not set the
        output on fallback objects.  On python-2.3,
        :class:`gettext.NullTranslations` objects don't contain this method.
        '''
        if self._fallback:
            try:
                self._fallback.set_output_charset(charset)
            except AttributeError:
                pass
        try:
            gettext.NullTranslations.set_output_charset(self, charset)
        except AttributeError:
            self._output_charset = charset

    if not hasattr(gettext.NullTranslations, 'output_charset'):
        def output_charset(self):
            '''Compatibility for python2.3 which doesn't have output_charset'''
            return self._output_charset

    def _reencode_if_necessary(self, message, output_encoding):
        '''Return a byte string that's valid in a specific charset.

        .. warning:: This method may mangle the message if the inpput encoding
            is not known or the message isn't represntable in the chosen
            output encoding.
        '''
        valid = False
        msg = None
        try:
            valid = byte_string_valid_encoding(message, output_encoding)
        except TypeError:
            # input was unicode, so it needs to be encoded
            pass

        if valid:
            return message
        try:
            # Decode to unicode so we can re-encode to desired encoding
            msg = to_unicode(message, encoding=self.input_charset,
                    nonstring='strict')
        except TypeError:
            # Not a string; return an empty byte string
            return b''

        # Make sure that we're returning a str of the desired encoding
        return to_bytes(msg, encoding=output_encoding)

    def _gettext(self, message):
        # First use any fallback gettext objects.  Since DummyTranslations
        # doesn't do any translation on its own, this is a good first step.
        if self._fallback:
            try:
                message = self._fallback.gettext(message)
            except (AttributeError, UnicodeError):
                # Ignore UnicodeErrors: We'll do our own encoding next
                pass

        # Next decide what encoding to use for the strings we return
        output_encoding = (self._output_charset or self._charset or
                self.input_charset)
        return self._reencode_if_necessary(message, output_encoding)

    def _ngettext(self, msgid1, msgid2, n):
        # Default
        if n == 1:
            message = msgid1
        else:
            message = msgid2

        # The fallback method might return something different
        if self._fallback:
            try:
                message = self._fallback.ngettext(msgid1, msgid2, n)
            except (AttributeError, UnicodeError):
                # Ignore UnicodeErrors: We'll do our own encoding next
                pass

        # Next decide what encoding to use for the strings we return
        output_encoding = (self._output_charset or self._charset or
                self.input_charset)

        return self._reencode_if_necessary(message, output_encoding)

    def _lgettext(self, message):
        if self._fallback:
            try:
                message = self._fallback.lgettext(message)
            except (AttributeError, UnicodeError):
                # Ignore UnicodeErrors: we'll do our own encoding next
                # AttributeErrors happen on py2.3 where lgettext is not
                # implemented
                pass

        # Next decide what encoding to use for the strings we return
        output_encoding = (self._output_charset or
                locale.getpreferredencoding())

        return self._reencode_if_necessary(message, output_encoding)

    def _lngettext(self, msgid1, msgid2, n):
        # Default
        if n == 1:
            message = msgid1
        else:
            message = msgid2
        # Fallback method might have something different
        if self._fallback:
            try:
                message = self._fallback.lngettext(msgid1, msgid2, n)
            except (AttributeError, UnicodeError):
                # Ignore UnicodeErrors: we'll do our own encoding next
                # AttributeError happens on py2.3 where lngettext is not
                # implemented
                pass

        # Next decide what encoding to use for the strings we return
        output_encoding = (self._output_charset or
                locale.getpreferredencoding())

        return self._reencode_if_necessary(message, output_encoding)

    def _ugettext(self, message):
        if not isbasestring(message):
            return ''
        if self._fallback:
            msg = to_unicode(message, encoding=self.input_charset)
            try:
                message = self._fallback.ugettext(msg)
            except (AttributeError, UnicodeError):
                # Ignore UnicodeErrors: We'll do our own decoding later
                pass

        # Make sure we're returning unicode
        return to_unicode(message, encoding=self.input_charset)

    def _ungettext(self, msgid1, msgid2, n):
        # Default
        if n == 1:
            message = msgid1
        else:
            message = msgid2
        # Fallback might override this
        if self._fallback:
            msgid1 = to_unicode(msgid1, encoding=self.input_charset)
            msgid2 = to_unicode(msgid2, encoding=self.input_charset)
            try:
                message = self._fallback.ungettext(msgid1, msgid2, n)
            except (AttributeError, UnicodeError):
                # Ignore UnicodeErrors: We'll do our own decoding later
                pass

        # Make sure we're returning unicode
        return to_unicode(message, encoding=self.input_charset,
                nonstring='empty')


class NewGNUTranslations(DummyTranslations, gettext.GNUTranslations):
    '''Safer version of :class:`gettext.GNUTranslations`

    :class:`gettext.GNUTranslations` suffers from two problems that this
    class fixes.

    1) :class:`gettext.GNUTranslations` can throw a
       :exc:`~exceptions.UnicodeError` in
       :meth:`gettext.GNUTranslations.ugettext` if the message being
       translated has non-:term:`ASCII` characters and there is no translation
       for it.
    2) :class:`gettext.GNUTranslations` can return byte :class:`bytes` from
       :meth:`gettext.GNUTranslations.ugettext` and :class:`str`
       strings from the other :meth:`~gettext.GNUTranslations.gettext`
       methods if the message being translated is the wrong type

    When byte :class:`bytes` are returned, the strings will be encoded
    according to this algorithm:

    1) If a fallback has been added, the fallback will be called first.
       You'll need to consult the fallback to see whether it performs any
       encoding changes.
    2) If a byte :class:`bytes` was given, the same byte :class:`bytes` will
       be returned.
    3) If a :class:`str` string was given and
       :meth:`set_output_charset` has been called then we encode the
       string using the :attr:`output_charset`
    4) If a :class:`str` string was given and this is :meth:`gettext`
       or :meth:`ngettext` and a charset was detected when parsing the
       :term:`message catalog`, output in that charset.
    5) If a :class:`str` string was given and this is :meth:`gettext`
       or :meth:`ngettext` we encode it using :term:`UTF-8`.
    6) If a :class:`str` string was given and this is :meth:`lgettext`
       or :meth:`lngettext` we encode using the value of
       :func:`locale.getpreferredencoding`

    For :meth:`ugettext` and :meth:`ungettext`, we go through the same set of
    steps with the following differences:

    * We transform byte :class:`bytes` into :class:`str` strings for these
      methods.
    * The encoding used to decode the byte :class:`bytes` is taken from
      :attr:`input_charset` if it's set, otherwise we decode using
      :term:`UTF-8`

    .. attribute:: input_charset

        an extension to the |stdlib|_ :mod:`gettext` that specifies what
        charset a message is encoded in when decoding a message to
        :class:`str`.  This is used for two purposes:

    1) If the message string is a byte :class:`bytes`, this is used to decode
       the string to a :class:`str` string before looking it up in the
       :term:`message catalog`.
    2) In :meth:`~kitchen.i18n.DummyTranslations.ugettext` and
       :meth:`~kitchen.i18n.DummyTranslations.ungettext` methods, if a byte
       :class:`bytes` is given as the message and is untranslated his is used as
       the encoding when decoding to :class:`str`.  This is different from
       the :attr:`_charset` parameter that may be set when a :term:`message
       catalog` is loaded because :attr:`input_charset` is used to describe an
       encoding used in a python source file while :attr:`_charset` describes
       the encoding used in the :term:`message catalog` file.

    Any characters that aren't able to be transformed from a byte
    :class:`bytes` to :class:`str` string or vice versa will be replaced
    with a replacement character (ie: ``u'�'`` in unicode based encodings,
    ``'?'`` in other :term:`ASCII` compatible encodings).

    .. seealso::

        :class:`gettext.GNUTranslations.gettext`
            For information about what methods this class has and what they do

    .. versionchanged:: kitchen-1.1.0 ; API kitchen.i18n 2.1.0
        Although we had adapted :meth:`gettext`, :meth:`ngettext`,
        :meth:`lgettext`, and :meth:`lngettext` to always return
        byte :class:`bytes`, we hadn't forced those byte :class:`bytes` to always
        be in a specified charset.  We now make sure that :meth:`gettext` and
        :meth:`ngettext` return byte :class:`bytes` encoded using
        :attr:`output_charset` if set, otherwise :attr:`charset` and if
        neither of those, :term:`UTF-8`.  With :meth:`lgettext` and
        :meth:`lngettext` :attr:`output_charset` if set, otherwise
        :func:`locale.getpreferredencoding`.
    '''
    #pylint: disable-msg=C0103,C0111
    def _parse(self, fp):
        gettext.GNUTranslations._parse(self, fp)

    def _gettext(self, message):
        if not isbasestring(message):
            return b''
        tmsg = message
        u_message = to_unicode(message, encoding=self.input_charset)
        try:
            tmsg = self._catalog[u_message] #pylint:disable-msg=E1101
        except KeyError:
            if self._fallback:
                try:
                    tmsg = self._fallback.gettext(message)
                except (AttributeError, UnicodeError):
                    # Ignore UnicodeErrors: We'll do our own encoding next
                    pass

        # Next decide what encoding to use for the strings we return
        output_encoding = (self._output_charset or self._charset or
                self.input_charset)

        return self._reencode_if_necessary(tmsg, output_encoding)

    def _ngettext(self, msgid1, msgid2, n):
        if n == 1:
            tmsg = msgid1
        else:
            tmsg = msgid2

        if not isbasestring(msgid1):
            return b''
        u_msgid1 = to_unicode(msgid1, encoding=self.input_charset)
        try:
            #pylint:disable-msg=E1101
            tmsg = self._catalog[(u_msgid1, self.plural(n))]
        except KeyError:
            if self._fallback:
                try:
                    tmsg = self._fallback.ngettext(msgid1, msgid2, n)
                except (AttributeError, UnicodeError):
                    # Ignore UnicodeErrors: We'll do our own encoding next
                    pass

        # Next decide what encoding to use for the strings we return
        output_encoding = (self._output_charset or self._charset or
                self.input_charset)

        return self._reencode_if_necessary(tmsg, output_encoding)

    def _lgettext(self, message):
        if not isbasestring(message):
            return b''
        tmsg = message
        u_message = to_unicode(message, encoding=self.input_charset)
        try:
            tmsg = self._catalog[u_message] #pylint:disable-msg=E1101
        except KeyError:
            if self._fallback:
                try:
                    tmsg = self._fallback.lgettext(message)
                except (AttributeError, UnicodeError):
                    # Ignore UnicodeErrors: We'll do our own encoding next
                    pass

        # Next decide what encoding to use for the strings we return
        output_encoding = (self._output_charset or
                locale.getpreferredencoding())

        return self._reencode_if_necessary(tmsg, output_encoding)

    def _lngettext(self, msgid1, msgid2, n):
        if n == 1:
            tmsg = msgid1
        else:
            tmsg = msgid2

        if not isbasestring(msgid1):
            return b''
        u_msgid1 = to_unicode(msgid1, encoding=self.input_charset)
        try:
            #pylint:disable-msg=E1101
            tmsg = self._catalog[(u_msgid1, self.plural(n))]
        except KeyError:
            if self._fallback:
                try:
                    tmsg = self._fallback.lngettext(msgid1, msgid2, n)
                except (AttributeError, UnicodeError):
                    # Ignore UnicodeErrors: We'll do our own encoding next
                    pass

        # Next decide what encoding to use for the strings we return
        output_encoding = (self._output_charset or
                locale.getpreferredencoding())

        return self._reencode_if_necessary(tmsg, output_encoding)


    def _ugettext(self, message):
        if not isbasestring(message):
            return ''
        message = to_unicode(message, encoding=self.input_charset)
        try:
            message = self._catalog[message] #pylint:disable-msg=E1101
        except KeyError:
            if self._fallback:
                try:
                    message = self._fallback.ugettext(message)
                except (AttributeError, UnicodeError):
                    # Ignore UnicodeErrors: We'll do our own encoding next
                    pass

        # Make sure that we're returning unicode
        return to_unicode(message, encoding=self.input_charset)

    def _ungettext(self, msgid1, msgid2, n):
        if n == 1:
            tmsg = msgid1
        else:
            tmsg = msgid2

        if not isbasestring(msgid1):
            return ''
        u_msgid1 = to_unicode(msgid1, encoding=self.input_charset)
        try:
            #pylint:disable-msg=E1101
            tmsg = self._catalog[(u_msgid1, self.plural(n))]
        except KeyError:
            if self._fallback:
                try:
                    tmsg = self._fallback.ungettext(msgid1, msgid2, n)
                except (AttributeError, UnicodeError):
                    # Ignore UnicodeErrors: We'll do our own encoding next
                    pass

        # Make sure that we're returning unicode
        return to_unicode(tmsg, encoding=self.input_charset,
                nonstring='empty')


def get_translation_object(domain, localedirs=tuple(), languages=None,
        class_=None, fallback=True, codeset=None, python2_api=True):
    '''Get a translation object bound to the :term:`message catalogs`

    :arg domain: Name of the message domain.  This should be a unique name
        that can be used to lookup the :term:`message catalog` for this app or
        library.
    :kwarg localedirs: Iterator of directories to look for
        :term:`message catalogs` under.  The directories are searched in order
        for :term:`message catalogs`.  For each of the directories searched,
        we check for message catalogs in any language specified
        in:attr:`languages`.  The :term:`message catalogs` are used to create
        the Translation object that we return.  The Translation object will
        attempt to lookup the msgid in the first catalog that we found.  If
        it's not in there, it will go through each subsequent catalog looking
        for a match.  For this reason, the order in which you specify the
        :attr:`localedirs` may be important.  If no :term:`message catalogs`
        are found, either return a :class:`DummyTranslations` object or raise
        an :exc:`IOError` depending on the value of :attr:`fallback`.
        Rhe default localedir from  :mod:`gettext` which is
        :file:`os.path.join(sys.prefix, 'share', 'locale')` on Unix is
        implicitly appended to the :attr:`localedirs`, making it the last
        directory searched.
    :kwarg languages: Iterator of language codes to check for
        :term:`message catalogs`.  If unspecified, the user's locale settings
        will be used.

        .. seealso:: :func:`gettext.find` for information on what environment
            variables are used.

    :kwarg class_:  The class to use to extract translations from the
        :term:`message catalogs`.  Defaults to :class:`NewGNUTranslations`.
    :kwarg fallback: If set to data:`False`, raise an :exc:`IOError` if no
        :term:`message catalogs` are found.  If :data:`True`, the default,
        return a :class:`DummyTranslations` object.
    :kwarg codeset: Set the character encoding to use when returning byte
        :class:`bytes` objects.  This is equivalent to calling
        :meth:`~gettext.GNUTranslations.output_charset` on the Translations
        object that is returned from this function.
    :kwarg python2_api: When data:`True` (default), return Translation objects
        that use the python2 gettext api
        (:meth:`~gettext.GNUTranslations.gettext` and
        :meth:`~gettext.GNUTranslations.lgettext` return byte
        :class:`bytes`.  :meth:`~gettext.GNUTranslations.ugettext` exists and
        returns :class:`str` strings).  When :data:`False`, return
        Translation objects that use the python3 gettext api (gettext returns
        :class:`str` strings and lgettext returns byte :class:`bytes`.
        ugettext does not exist.)
    :return: Translation object to get :mod:`gettext` methods from

    If you need more flexibility than :func:`easy_gettext_setup`, use this
    function.  It sets up a :mod:`gettext` Translation object and returns it
    to you.  Then you can access any of the methods of the object that you
    need directly.  For instance, if you specifically need to access
    :func:`~gettext.GNUTranslations.lgettext`::

        translations = get_translation_object('foo')
        translations.lgettext('My Message')

    This function is similar to the |stdlib|_ :func:`gettext.translation` but
    makes it better in two ways

    1. It returns :class:`NewGNUTranslations` or :class:`DummyTranslations`
        objects by default.  These are superior to the
        :class:`gettext.GNUTranslations` and :class:`gettext.NullTranslations`
        objects because they are consistent in the string type they return and
        they fix several issues that can causethe |stdlib|_ objects to throw
        :exc:`UnicodeError`.
    2. This function takes multiple directories to search for
        :term:`message catalogs`.

    The latter is important when setting up :mod:`gettext` in a portable
    manner.  There is not a common directory for translations across operating
    systems so one needs to look in multiple directories for the translations.
    :func:`get_translation_object` is able to handle that if you give it
    a list of directories to search for catalogs::

        translations = get_translation_object('foo', localedirs=(
             os.path.join(os.path.realpath(os.path.dirname(__file__)), 'locale'),
             os.path.join(sys.prefix, 'lib', 'locale')))

    This will search for several different directories:

    1. A directory named :file:`locale` in the same directory as the module
       that called :func:`get_translation_object`,
    2. In :file:`/usr/lib/locale`
    3. In :file:`/usr/share/locale` (the fallback directory)

    This allows :mod:`gettext` to work on Windows and in development (where the
    :term:`message catalogs` are typically in the toplevel module directory)
    and also when installed under Linux (where the :term:`message catalogs`
    are installed in :file:`/usr/share/locale`).  You (or the system packager)
    just need to install the :term:`message catalogs` in
    :file:`/usr/share/locale` and remove the :file:`locale` directory from the
    module to make this work.  ie::

        In development:
            ~/foo   # Toplevel module directory
            ~/foo/__init__.py
            ~/foo/locale    # With message catalogs below here:
            ~/foo/locale/es/LC_MESSAGES/foo.mo

        Installed on Linux:
            /usr/lib/python2.7/site-packages/foo
            /usr/lib/python2.7/site-packages/foo/__init__.py
            /usr/share/locale/  # With message catalogs below here:
            /usr/share/locale/es/LC_MESSAGES/foo.mo

    .. note::

        This function will setup Translation objects that attempt to lookup
        msgids in all of the found :term:`message catalogs`.  This means if
        you have several versions of the :term:`message catalogs` installed
        in different directories that the function searches, you need to make
        sure that :attr:`localedirs` specifies the directories so that newer
        :term:`message catalogs` are searched first.  It also means that if
        a newer catalog does not contain a translation for a msgid but an
        older one that's in :attr:`localedirs` does, the translation from that
        older catalog will be returned.

    .. versionchanged:: kitchen-1.1.0 ; API kitchen.i18n 2.1.0
        Add more parameters to :func:`~kitchen.i18n.get_translation_object` so
        it can more easily be used as a replacement for
        :func:`gettext.translation`.  Also change the way we use localedirs.
        We cycle through them until we find a suitable locale file rather
        than simply cycling through until we find a directory that exists.
        The new code is based heavily on the |stdlib|_
        :func:`gettext.translation` function.
    .. versionchanged:: kitchen-1.2.0 ; API kitchen.i18n 2.2.0
        Add python2_api parameter
    '''
    if python2_api:
        warnings.warn('get_translation_object returns gettext objects'
                ' that implement either the python2 or python3 gettext api.'
                '  You are currently using the python2 api.  Consider'
                ' switching to the python3 api by setting python2_api=False'
                ' when you call the function.',
                PendingDeprecationWarning, stacklevel=2)
    if not class_:
        class_ = NewGNUTranslations

    mofiles = []
    for localedir in itertools.chain(localedirs, (_DEFAULT_LOCALEDIR,)):
        mofiles.extend(gettext.find(domain, localedir, languages, all=1))
    if not mofiles:
        if fallback:
            return DummyTranslations(python2_api=python2_api)
        raise IOError(ENOENT, 'No translation file found for domain', domain)

    # Accumulate a translation with fallbacks to all the other mofiles
    stacked_translations = None
    for mofile in mofiles:
        full_path = os.path.abspath(mofile)
        translation = _translations.get(full_path)
        if not translation:
            mofile_fh = open(full_path, 'rb')
            try:
                try:
                    translation = _translations.setdefault(full_path,
                            class_(mofile_fh, python2_api=python2_api))
                except TypeError:
                    # Only our translation classes have the python2_api
                    # parameter
                    translation = _translations.setdefault(full_path,
                            class_(mofile_fh))

            finally:
                mofile_fh.close()

        # Shallow copy the object so that the fallbacks and output charset can
        # differ but the data we read from the mofile is shared.
        translation = copy.copy(translation)
        translation.python2_api = python2_api
        if codeset:
            translation.set_output_charset(codeset)
        if not stacked_translations:
            stacked_translations = translation
        else:
            stacked_translations.add_fallback(translation)

    return stacked_translations

def easy_gettext_setup(domain, localedirs=tuple(), use_unicode=True):
    ''' Setup translation functions for an application

    :arg domain: Name of the message domain.  This should be a unique name
        that can be used to lookup the :term:`message catalog` for this app.
    :kwarg localedirs: Iterator of directories to look for :term:`message
        catalogs` under.  The first directory to exist is used regardless of
        whether messages for this domain are present.  If none of the
        directories exist, fallback on ``sys.prefix`` + :file:`/share/locale`
        Default: No directories to search so we just use the fallback.
    :kwarg use_unicode: If :data:`True` return the :mod:`gettext` functions
        for :class:`str` strings else return the functions for byte
        :class:`bytes` for the translations.  Default is :data:`True`.
    :return: tuple of the :mod:`gettext` function and :mod:`gettext` function
        for plurals

    Setting up :mod:`gettext` can be a little tricky because of lack of
    documentation.  This function will setup :mod:`gettext`  using the
    `Class-based API
    <http://docs.python.org/library/gettext.html#class-based-api>`_ for you.
    For the simple case, you can use the default arguments and call it like
    this::

        _, N_ = easy_gettext_setup()

    This will get you two functions, :func:`_` and :func:`N_` that you can use
    to mark strings in your code for translation.  :func:`_` is used to mark
    strings that don't need to worry about plural forms no matter what the
    value of the variable is.  :func:`N_` is used to mark strings that do need
    to have a different form if a variable in the string is plural.

    .. seealso::

        :doc:`api-i18n`
            This module's documentation has examples of using :func:`_` and :func:`N_`
        :func:`get_translation_object`
            for information on how to use :attr:`localedirs` to get the
            proper :term:`message catalogs` both when in development and when
            installed to FHS compliant directories on Linux.

    .. note::

        The gettext functions returned from this function should be superior
        to the ones returned from :mod:`gettext`.  The traits that make them
        better are described in the :class:`DummyTranslations` and
        :class:`NewGNUTranslations` documentation.

    .. versionchanged:: kitchen-0.2.4 ; API kitchen.i18n 2.0.0
        Changed :func:`~kitchen.i18n.easy_gettext_setup` to return the lgettext
        functions instead of gettext functions when use_unicode=False.
    '''
    translations = get_translation_object(domain, localedirs=localedirs, python2_api=False)
    if use_unicode:
        return(translations.gettext, translations.ngettext)
    return(translations.lgettext, translations.lngettext)

__all__ = ('DummyTranslations', 'NewGNUTranslations', 'easy_gettext_setup',
        'get_translation_object')
