# -*- coding: utf-8 -*-
#
# Copyright (c) 2011 Red Hat, Inc
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
----------------------------
PEP-386 compliant versioning
----------------------------

:pep:`386` defines a standard format for version strings.  This module
contains a function for creating strings in that format.
'''
__version_info__ = ((1, 0, 0),)

def version_tuple_to_string(version_info):
    '''Return a :pep:`386` version string from a :pep:`386` style version tuple

    :arg version_info: Nested set of tuples that describes the version.  See
        below for an example.
    :returns: a version string

    This function implements just enough of :pep:`386` to satisfy our needs.
    :pep:`386` defines a standard format for version strings and refers to
    a function that will be merged into the |stdlib|_ that transforms a tuple
    of version information into a standard version string.  This function is
    an implementation of that function.  Once that function becomes available
    in the |stdlib|_ we will start using it and deprecate this function.

    :attr:`version_info` takes the form that :pep:`386`'s
    :func:`NormalizedVersion.from_parts` uses::

        ((Major, Minor, [Micros]), [(Alpha/Beta/rc marker, version)],
            [(post/dev marker, version)])

        Ex: ((1, 0, 0), ('a', 2), ('dev', 3456))

    It generates a :pep:`386` compliant version string::

        N.N[.N]+[{a|b|c|rc}N[.N]+][.postN][.devN]

        Ex: 1.0.0a2.dev3456

    .. warning:: This function does next to no error checking.  It's up to the
        person defining the version tuple to make sure that the values make
        sense.  If the :pep:`386` compliant version parser doesn't get
        released soon we'll look at making this function check that the
        version tuple makes sense before transforming it into a string.

    It's recommended that you use this function to keep
    a :data:`__version_info__` tuple and :data:`__version__` string in your
    modules.  Why do we need both a tuple and a string?  The string is often
    useful for putting into human readable locations like release
    announcements, version strings in tarballs, etc.  Meanwhile the tuple is
    very easy for a computer to compare. For example, kitchen sets up its
    version information like this::

        from kitchen.versioning import version_tuple_to_string
        __version_info__ = ((0, 2, 1),)
        __version__ = version_tuple_to_string(__version_info__)

    Other programs that depend on a kitchen version between 0.2.1 and 0.3.0
    can find whether the present version is okay with code like this::

        from kitchen import __version_info__, __version__
        if __version_info__ < ((0, 2, 1),) or __version_info__ >= ((0, 3, 0),):
            print 'kitchen is present but not at the right version.'
            print 'We need at least version 0.2.1 and less than 0.3.0'
            print 'Currently found: kitchen-%s' % __version__
    '''
    ver_components = []
    for values in version_info:
        if isinstance(values[0], int):
            ver_components.append('.'.join(map(str, values)))
        else:
            modifier = values[0]
            if isinstance(modifier, bytes):
                modifier = modifier.decode('ascii')

            if  modifier in ('a', 'b', 'c', 'rc'):
                ver_components.append('{}{}'.format(modifier,
                    '.'.join(map(str, values[1:])) or '0'))
            else:
                # Only 'devXXXX' here
                ver_components.append('.{}{}'.format(modifier,
                    str(values[1])))
    return ''.join(ver_components)


__version__ = version_tuple_to_string(__version_info__)

__all__ = ('version_tuple_to_string',)
