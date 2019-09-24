from __future__ import absolute_import, division, print_function, unicode_literals

import sys

USING_PYTHON2 = True if sys.version_info < (3, 0) else False

if USING_PYTHON2:
    str = unicode  # noqa
else:
    str = str
