'''
The :mod:`kitchen.pycompat27` module contains implementations of functionality
introduced in python-2.7 for use on earlier versions of python.

.. versionchanged:: 0.2.3
    Made mswindows, MAXFD, and list2cmdline available from the module
'''
import warnings

warnings.warn('In python3, kitchen.pycompat27 is deprecated because all'
        ' functionality in this module is found in the python3 stdlib.'
        '  If your code doesn\'t need to maintain compatibility with'
        ' python less than 2.7, use subprocess from the python3 stdlib.',
        PendingDeprecationWarning, stacklevel=2)

from kitchen.versioning import version_tuple_to_string

__version_info__ = ((1, 1, 0),)
__version__ = version_tuple_to_string(__version_info__)

__all__ = ('subprocess',)
