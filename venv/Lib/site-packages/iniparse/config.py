class ConfigNamespace(object):
    """Abstract class representing the interface of Config objects.

    A ConfigNamespace is a collection of names mapped to values, where
    the values may be nested namespaces.  Values can be accessed via
    container notation - obj[key] - or via dotted notation - obj.key.
    Both these access methods are equivalent.

    To minimize name conflicts between namespace keys and class members,
    the number of class members should be minimized, and the names of
    all class members should start with an underscore.

    Subclasses must implement the methods for container-like access,
    and this class will automatically provide dotted access.

    """

    # Methods that must be implemented by subclasses

    def _getitem(self, key):
        return NotImplementedError(key)

    def __setitem__(self, key, value):
        raise NotImplementedError(key, value)

    def __delitem__(self, key):
        raise NotImplementedError(key)

    def __iter__(self):
        return NotImplementedError()

    def _new_namespace(self, name):
        raise NotImplementedError(name)

    def __contains__(self, key):
        try:
            self._getitem(key)
        except KeyError:
            return False
        return True

    # Machinery for converting dotted access into container access,
    # and automatically creating new sections/namespaces.
    #
    # To distinguish between accesses of class members and namespace
    # keys, we first call object.__getattribute__().  If that succeeds,
    # the name is assumed to be a class member.  Otherwise it is
    # treated as a namespace key.
    #
    # Therefore, member variables should be defined in the class,
    # not just in the __init__() function.  See BasicNamespace for
    # an example.

    def __getitem__(self, key):
        try:
            return self._getitem(key)
        except KeyError:
            return Undefined(key, self)

    def __getattr__(self, name):
        try:
            return self._getitem(name)
        except KeyError:
            if name.startswith('__') and name.endswith('__'):
                raise AttributeError
            return Undefined(name, self)

    def __setattr__(self, name, value):
        try:
            object.__getattribute__(self, name)
            object.__setattr__(self, name, value)
        except AttributeError:
            self.__setitem__(name, value)

    def __delattr__(self, name):
        try:
            object.__getattribute__(self, name)
            object.__delattr__(self, name)
        except AttributeError:
            self.__delitem__(name)

    # During unpickling, Python checks if the class has a __setstate__
    # method.  But, the data dicts have not been initialised yet, which
    # leads to  _getitem and hence __getattr__ raising an exception.  So
    # we explicitly impement default __setstate__ behavior.
    def __setstate__(self, state):
        self.__dict__.update(state)


class Undefined(object):
    """Helper class used to hold undefined names until assignment.

    This class helps create any undefined subsections when an
    assignment is made to a nested value.  For example, if the
    statement is "cfg.a.b.c = 42", but "cfg.a.b" does not exist yet.
    """

    def __init__(self, name, namespace):
        object.__setattr__(self, 'name', name)
        object.__setattr__(self, 'namespace', namespace)

    def __setattr__(self, name, value):
        obj = self.namespace._new_namespace(self.name)
        obj[name] = value

    def __setitem__(self, name, value):
        obj = self.namespace._new_namespace(self.name)
        obj[name] = value


# ---- Basic implementation of a ConfigNamespace

class BasicConfig(ConfigNamespace):
    """Represents a hierarchical collection of named values.

    Values are added using dotted notation:

    >>> n = BasicConfig()
    >>> n.x = 7
    >>> n.name.first = 'paramjit'
    >>> n.name.last = 'oberoi'

    ...and accessed the same way, or with [...]:

    >>> n.x
    7
    >>> n.name.first
    'paramjit'
    >>> n.name.last
    'oberoi'
    >>> n['x']
    7
    >>> n['name']['first']
    'paramjit'

    Iterating over the namespace object returns the keys:

    >>> l = list(n)
    >>> l.sort()
    >>> l
    ['name', 'x']

    Values can be deleted using 'del' and printed using 'print'.

    >>> n.aaa = 42
    >>> del n.x
    >>> print(n)
    aaa = 42
    name.first = paramjit
    name.last = oberoi

    Nested namespaces are also namespaces:

    >>> isinstance(n.name, ConfigNamespace)
    True
    >>> print(n.name)
    first = paramjit
    last = oberoi
    >>> sorted(list(n.name))
    ['first', 'last']

    Finally, values can be read from a file as follows:

    >>> from six import StringIO
    >>> sio = StringIO('''
    ... # comment
    ... ui.height = 100
    ... ui.width = 150
    ... complexity = medium
    ... have_python
    ... data.secret.password = goodness=gracious me
    ... ''')
    >>> n = BasicConfig()
    >>> n._readfp(sio)
    >>> print(n)
    complexity = medium
    data.secret.password = goodness=gracious me
    have_python
    ui.height = 100
    ui.width = 150
    """

    # this makes sure that __setattr__ knows this is not a namespace key
    _data = None

    def __init__(self):
        self._data = {}

    def _getitem(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __delitem__(self, key):
        del self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __str__(self, prefix=''):
        lines = []
        keys = list(self._data.keys())
        keys.sort()
        for name in keys:
            value = self._data[name]
            if isinstance(value, ConfigNamespace):
                lines.append(value.__str__(prefix='%s%s.' % (prefix,name)))
            else:
                if value is None:
                    lines.append('%s%s' % (prefix, name))
                else:
                    lines.append('%s%s = %s' % (prefix, name, value))
        return '\n'.join(lines)

    def _new_namespace(self, name):
        obj = BasicConfig()
        self._data[name] = obj
        return obj

    def _readfp(self, fp):
        while True:
            line = fp.readline()
            if not line:
                break

            line = line.strip()
            if not line: continue
            if line[0] == '#': continue
            data = line.split('=', 1)
            if len(data) == 1:
                name = line
                value = None
            else:
                name = data[0].strip()
                value = data[1].strip()
            name_components = name.split('.')
            ns = self
            for n in name_components[:-1]:
                if n in ns:
                    ns = ns[n]
                    if not isinstance(ns, ConfigNamespace):
                        raise TypeError('value-namespace conflict', n)
                else:
                    ns = ns._new_namespace(n)
            ns[name_components[-1]] = value


# ---- Utility functions

def update_config(target, source):
    """Imports values from source into target.

    Recursively walks the <source> ConfigNamespace and inserts values
    into the <target> ConfigNamespace.  For example:

    >>> n = BasicConfig()
    >>> n.playlist.expand_playlist = True
    >>> n.ui.display_clock = True
    >>> n.ui.display_qlength = True
    >>> n.ui.width = 150
    >>> print(n)
    playlist.expand_playlist = True
    ui.display_clock = True
    ui.display_qlength = True
    ui.width = 150

    >>> from iniparse import ini
    >>> i = ini.INIConfig()
    >>> update_config(i, n)
    >>> print(i)
    [playlist]
    expand_playlist = True
    <BLANKLINE>
    [ui]
    display_clock = True
    display_qlength = True
    width = 150

    """
    for name in sorted(source):
        value = source[name]
        if isinstance(value, ConfigNamespace):
            if name in target:
                myns = target[name]
                if not isinstance(myns, ConfigNamespace):
                    raise TypeError('value-namespace conflict')
            else:
                myns = target._new_namespace(name)
            update_config(myns, value)
        else:
            target[name] = value
