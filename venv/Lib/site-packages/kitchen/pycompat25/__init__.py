'''
The :mod:`kitchen.pycompat25` module contains implementations of functionality
introduced in python-2.5.
'''
import warnings

warnings.warn('In python3, kitchen.pycompat25 is deprecated because all'
        ' functionality in this module is found in the python3 stdlib.'
        '  If your code doesn\'t need to maintain compatibility with'
        ' python less than 2.5, use collections.defaultdict from the python3'
        ' stdlib.',
        PendingDeprecationWarning, stacklevel=2)

from kitchen.versioning import version_tuple_to_string

__version_info__ = ((1, 0, 0),)
__version__ = version_tuple_to_string(__version_info__)


__all__ = ('collections',)
