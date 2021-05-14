# :W0401, W0611, W0614: Rather than have two versions of subprocess, we import
#   the python2.7 version here as well
#pylint:disable-msg=W0401,W0611,W0614
import kitchen.pycompat27.subprocess as __s
from kitchen.pycompat27.subprocess import *
from kitchen.pycompat27.subprocess import __all__

import warnings

warnings.warn('In python3, kitchen.pycompat24.subprocess is deprecated.'
        '  If your code doesn\'t have to remain compatible with python less'
        ' than 2.4 use subprocess from the python3 stdlib',
        PendingDeprecationWarning, stacklevel=2)
