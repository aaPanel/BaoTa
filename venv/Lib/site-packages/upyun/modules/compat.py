# -*- coding: utf-8 -*-

import sys

PY3 = sys.version_info[0] == 3

if PY3:
    from urllib.parse import quote, urlencode

    def b(s):
        if isinstance(s, str):
            return s.encode('utf-8')
        return s

    builtin_str = str
    str = str
    bytes = bytes

    def stringify(data):
        return data

else:
    from urllib import quote, urlencode

    def b(s):
        return s

    builtin_str = str
    str = unicode  # noqa
    bytes = str

    def stringify(data):
        if isinstance(data, dict):
            return dict([(stringify(key), stringify(value))
                         for key, value in data.iteritems()])
        elif isinstance(data, list):
            return [stringify(element) for element in data]
        elif isinstance(data, unicode):  # noqa
            return data.encode('utf-8')
        else:
            return data


__all__ = [
    'quote', 'urlencode'
]
