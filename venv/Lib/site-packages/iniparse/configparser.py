try:
    from ConfigParser import *
    # not all objects get imported with __all__
    from ConfigParser import Error, InterpolationMissingOptionError
except ImportError:
    from configparser import *
    from configparser import Error, InterpolationMissingOptionError
