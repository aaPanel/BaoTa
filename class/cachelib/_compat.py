# flake8: noqa
import sys

PY2 = sys.version_info[0] == 2

if PY2:
    text_type = unicode
    string_types = (str, unicode)
    integer_types = (int, long)
    iteritems = lambda d, *args, **kwargs: d.iteritems(*args, **kwargs)

    def to_native(x, charset=sys.getdefaultencoding(), errors='strict'):
        if x is None or isinstance(x, str):
            return x
        return x.encode(charset, errors)

else:
    text_type = str
    string_types = (str, )
    integer_types = (int, )
    iteritems = lambda d, *args, **kwargs: iter(d.items(*args, **kwargs))

    def to_native(x, charset=sys.getdefaultencoding(), errors='strict'):
        if x is None or isinstance(x, str):
            return x
        return x.decode(charset, errors)
