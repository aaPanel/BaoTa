# All versions of python3 include defaultdict.  This module just exists for
# backwards compatibility
#
import warnings

warnings.warn('In python3, kitchen.pycompat25.collections is deprecated'
        ' If you do not need to maintain compatibility with python less'
        ' than 2.5 use collections from the stdlib instead.',
        PendingDeprecationWarning, stacklevel=2)

from collections import defaultdict as _d

class defaultdict(_d):
    '''*Deprecated*.  See help(collections.defaultdict) for usage'''
    def __init__(self, *args, **kwargs):
        warnings.warn('In python3, kitchen.pycompat25.collections.defaultdict'
                ' is deprecated.  If you do not need to maintain compatibility'
                ' with python less than 2.5 use collections.defaultdict from'
                ' the stdlib instead.',
                PendingDeprecationWarning, stacklevel=2)
        super(defaultdict, self).__init__(*args, **kwargs)

__all__ = ('defaultdict',)
