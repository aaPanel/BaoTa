'''
The :mod:`kitchen.pycompat24` module contains implementations of functionality
introduced in python-2.4 for use on earlier versions of python.
'''
import warnings

warnings.warn('In python3, kitchen.pycompat24 is deprecated because the'
        ' python stdlib has this code in all python3 versions.  If your code'
        ' doesn\'t have to remain compatible with python less than 2.4 use'
        ' python3\'s stdlib versions of base64, subprocess, and the builtin'
        ' set types instead',
        PendingDeprecationWarning, stacklevel=2)

from kitchen.versioning import version_tuple_to_string

__version_info__ = ((1, 1, 0),)
__version__ = version_tuple_to_string(__version_info__)

__all__ = ('base64', 'sets', 'subprocess')
