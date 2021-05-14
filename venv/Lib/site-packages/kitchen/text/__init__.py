'''
------------
Kitchen.text
------------

Kitchen.text contains functions for manipulating text in python.

This includes things like converting between byte strings and unicode,
and displaying text on the screen.
'''

from kitchen.versioning import version_tuple_to_string

__version_info__ = ((2, 2, 0),)
__version__ = version_tuple_to_string(__version_info__)

__all__ = ('converters', 'exceptions', 'misc',)
