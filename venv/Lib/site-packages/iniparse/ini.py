"""Access and/or modify INI files

* Compatiable with ConfigParser
* Preserves order of sections & options
* Preserves comments/blank lines/etc
* More conveninet access to data

Example:

    >>> from six import StringIO
    >>> sio = StringIO('''# configure foo-application
    ... [foo]
    ... bar1 = qualia
    ... bar2 = 1977
    ... [foo-ext]
    ... special = 1''')

    >>> cfg = INIConfig(sio)
    >>> print(cfg.foo.bar1)
    qualia
    >>> print(cfg['foo-ext'].special)
    1
    >>> cfg.foo.newopt = 'hi!'
    >>> cfg.baz.enabled = 0

    >>> print(cfg)
    # configure foo-application
    [foo]
    bar1 = qualia
    bar2 = 1977
    newopt = hi!
    [foo-ext]
    special = 1
    <BLANKLINE>
    [baz]
    enabled = 0

"""

# An ini parser that supports ordered sections/options
# Also supports updates, while preserving structure
# Backward-compatiable with ConfigParser

import re
from .configparser import DEFAULTSECT, ParsingError, MissingSectionHeaderError

import six

from . import config


class LineType(object):
    line = None

    def __init__(self, line=None):
        if line is not None:
            self.line = line.strip('\n')

    # Return the original line for unmodified objects
    # Otherwise construct using the current attribute values
    def __str__(self):
        if self.line is not None:
            return self.line
        else:
            return self.to_string()

    # If an attribute is modified after initialization
    # set line to None since it is no longer accurate.
    def __setattr__(self, name, value):
        if hasattr(self,name):
            self.__dict__['line'] = None
        self.__dict__[name] = value

    def to_string(self):
        raise Exception('This method must be overridden in derived classes')


class SectionLine(LineType):
    regex = re.compile(r'^\['
                       r'(?P<name>[^]]+)'
                       r'\]\s*'
                       r'((?P<csep>;|#)(?P<comment>.*))?$')

    def __init__(self, name, comment=None, comment_separator=None,
                             comment_offset=-1, line=None):
        super(SectionLine, self).__init__(line)
        self.name = name
        self.comment = comment
        self.comment_separator = comment_separator
        self.comment_offset = comment_offset

    def to_string(self):
        out = '[' + self.name + ']'
        if self.comment is not None:
            # try to preserve indentation of comments
            out = (out+' ').ljust(self.comment_offset)
            out = out + self.comment_separator + self.comment
        return out

    def parse(cls, line):
        m = cls.regex.match(line.rstrip())
        if m is None:
            return None
        return cls(m.group('name'), m.group('comment'),
                   m.group('csep'), m.start('csep'),
                   line)
    parse = classmethod(parse)


class OptionLine(LineType):
    def __init__(self, name, value, separator=' = ', comment=None,
                 comment_separator=None, comment_offset=-1, line=None):
        super(OptionLine, self).__init__(line)
        self.name = name
        self.value = value
        self.separator = separator
        self.comment = comment
        self.comment_separator = comment_separator
        self.comment_offset = comment_offset

    def to_string(self):
        out = '%s%s%s' % (self.name, self.separator, self.value)
        if self.comment is not None:
            # try to preserve indentation of comments
            out = (out+' ').ljust(self.comment_offset)
            out = out + self.comment_separator + self.comment
        return out

    regex = re.compile(r'^(?P<name>[^:=\s[][^:=]*)'
                       r'(?P<sep>[:=]\s*)'
                       r'(?P<value>.*)$')

    def parse(cls, line):
        m = cls.regex.match(line.rstrip())
        if m is None:
            return None

        name = m.group('name').rstrip()
        value = m.group('value')
        sep = m.group('name')[len(name):] + m.group('sep')

        # comments are not detected in the regex because
        # ensuring total compatibility with ConfigParser
        # requires that:
        #     option = value    ;comment   // value=='value'
        #     option = value;1  ;comment   // value=='value;1  ;comment'
        #
        # Doing this in a regex would be complicated.  I
        # think this is a bug.  The whole issue of how to
        # include ';' in the value needs to be addressed.
        # Also, '#' doesn't mark comments in options...

        coff = value.find(';')
        if coff != -1 and value[coff-1].isspace():
            comment = value[coff+1:]
            csep = value[coff]
            value = value[:coff].rstrip()
            coff = m.start('value') + coff
        else:
            comment = None
            csep = None
            coff = -1

        return cls(name, value, sep, comment, csep, coff, line)
    parse = classmethod(parse)


def change_comment_syntax(comment_chars='%;#', allow_rem=False):
    comment_chars = re.sub(r'([\]\-\^])', r'\\\1', comment_chars)
    regex = r'^(?P<csep>[%s]' % comment_chars
    if allow_rem:
        regex += '|[rR][eE][mM]'
    regex += r')(?P<comment>.*)$'
    CommentLine.regex = re.compile(regex)


class CommentLine(LineType):
    regex = re.compile(r'^(?P<csep>[;#]|[rR][eE][mM])'
                       r'(?P<comment>.*)$')

    def __init__(self, comment='', separator='#', line=None):
        super(CommentLine, self).__init__(line)
        self.comment = comment
        self.separator = separator

    def to_string(self):
        return self.separator + self.comment

    def parse(cls, line):
        m = cls.regex.match(line.rstrip())
        if m is None:
            return None
        return cls(m.group('comment'), m.group('csep'), line)

    parse = classmethod(parse)


class EmptyLine(LineType):
    # could make this a singleton
    def to_string(self):
        return ''

    value = property(lambda self: '')

    def parse(cls, line):
        if line.strip():
            return None
        return cls(line)

    parse = classmethod(parse)


class ContinuationLine(LineType):
    regex = re.compile(r'^\s+(?P<value>.*)$')

    def __init__(self, value, value_offset=None, line=None):
        super(ContinuationLine, self).__init__(line)
        self.value = value
        if value_offset is None:
            value_offset = 8
        self.value_offset = value_offset

    def to_string(self):
        return ' '*self.value_offset + self.value

    def parse(cls, line):
        m = cls.regex.match(line.rstrip())
        if m is None:
            return None
        return cls(m.group('value'), m.start('value'), line)

    parse = classmethod(parse)


class LineContainer(object):
    def __init__(self, d=None):
        self.contents = []
        self.orgvalue = None
        if d:
            if isinstance(d, list): self.extend(d)
            else: self.add(d)

    def add(self, x):
        self.contents.append(x)

    def extend(self, x):
        for i in x: self.add(i)

    def get_name(self):
        return self.contents[0].name

    def set_name(self, data):
        self.contents[0].name = data

    def get_value(self):
        if self.orgvalue is not None:
            return self.orgvalue
        elif len(self.contents) == 1:
            return self.contents[0].value
        else:
            return '\n'.join([('%s' % x.value) for x in self.contents
                              if not isinstance(x, CommentLine)])

    def set_value(self, data):
        self.orgvalue = data
        lines = ('%s' % data).split('\n')

        # If there is an existing ContinuationLine, use its offset
        value_offset = None
        for v in self.contents:
            if isinstance(v, ContinuationLine):
                value_offset = v.value_offset
                break

        # Rebuild contents list, preserving initial OptionLine
        self.contents = self.contents[0:1]
        self.contents[0].value = lines[0]
        del lines[0]
        for line in lines:
            if line.strip():
                self.add(ContinuationLine(line, value_offset))
            else:
                self.add(EmptyLine())

    name = property(get_name, set_name)

    value = property(get_value, set_value)

    def __str__(self):
        s = [x.__str__() for x in self.contents]
        return '\n'.join(s)

    def finditer(self, key):
        for x in self.contents[::-1]:
            if hasattr(x, 'name') and x.name==key:
                yield x

    def find(self, key):
        for x in self.finditer(key):
            return x
        raise KeyError(key)


def _make_xform_property(myattrname, srcattrname=None):
    private_attrname = myattrname + 'value'
    private_srcname = myattrname + 'source'
    if srcattrname is None:
        srcattrname = myattrname

    def getfn(self):
        srcobj = getattr(self, private_srcname)
        if srcobj is not None:
            return getattr(srcobj, srcattrname)
        else:
            return getattr(self, private_attrname)

    def setfn(self, value):
        srcobj = getattr(self, private_srcname)
        if srcobj is not None:
            setattr(srcobj, srcattrname, value)
        else:
            setattr(self, private_attrname, value)

    return property(getfn, setfn)


class INISection(config.ConfigNamespace):
    _lines = None
    _options = None
    _defaults = None
    _optionxformvalue = None
    _optionxformsource = None
    _compat_skip_empty_lines = set()

    def __init__(self, lineobj, defaults=None, optionxformvalue=None, optionxformsource=None):
        self._lines = [lineobj]
        self._defaults = defaults
        self._optionxformvalue = optionxformvalue
        self._optionxformsource = optionxformsource
        self._options = {}

    _optionxform = _make_xform_property('_optionxform')

    def _compat_get(self, key):
        # identical to __getitem__ except that _compat_XXX
        # is checked for backward-compatible handling
        if key == '__name__':
            return self._lines[-1].name
        if self._optionxform: key = self._optionxform(key)
        try:
            value = self._options[key].value
            del_empty = key in self._compat_skip_empty_lines
        except KeyError:
            if self._defaults and key in self._defaults._options:
                value = self._defaults._options[key].value
                del_empty = key in self._defaults._compat_skip_empty_lines
            else:
                raise
        if del_empty:
            value = re.sub('\n+', '\n', value)
        return value

    def _getitem(self, key):
        if key == '__name__':
            return self._lines[-1].name
        if self._optionxform: key = self._optionxform(key)
        try:
            return self._options[key].value
        except KeyError:
            if self._defaults and key in self._defaults._options:
                return self._defaults._options[key].value
            else:
                raise

    def __setitem__(self, key, value):
        if self._optionxform: xkey = self._optionxform(key)
        else: xkey = key
        if xkey in self._compat_skip_empty_lines:
            self._compat_skip_empty_lines.remove(xkey)
        if xkey not in self._options:
            # create a dummy object - value may have multiple lines
            obj = LineContainer(OptionLine(key, ''))
            self._lines[-1].add(obj)
            self._options[xkey] = obj
        # the set_value() function in LineContainer
        # automatically handles multi-line values
        self._options[xkey].value = value

    def __delitem__(self, key):
        if self._optionxform: key = self._optionxform(key)
        if key in self._compat_skip_empty_lines:
            self._compat_skip_empty_lines.remove(key)
        for l in self._lines:
            remaining = []
            for o in l.contents:
                if isinstance(o, LineContainer):
                    n = o.name
                    if self._optionxform: n = self._optionxform(n)
                    if key != n: remaining.append(o)
                else:
                    remaining.append(o)
            l.contents = remaining
        del self._options[key]

    def __iter__(self):
        d = set()
        for l in self._lines:
            for x in l.contents:
                if isinstance(x, LineContainer):
                    if self._optionxform:
                        ans = self._optionxform(x.name)
                    else:
                        ans = x.name
                    if ans not in d:
                        yield ans
                        d.add(ans)
        if self._defaults:
            for x in self._defaults:
                if x not in d:
                    yield x
                    d.add(x)

    def _new_namespace(self, name):
        raise Exception('No sub-sections allowed', name)


def make_comment(line):
    return CommentLine(line.rstrip('\n'))


def readline_iterator(f):
    """iterate over a file by only using the file object's readline method"""

    have_newline = False
    while True:
        line = f.readline()

        if not line:
            if have_newline:
                yield ""
            return

        if line.endswith('\n'):
            have_newline = True
        else:
            have_newline = False

        yield line


def lower(x):
    return x.lower()


class INIConfig(config.ConfigNamespace):
    _data = None
    _sections = None
    _defaults = None
    _optionxformvalue = None
    _optionxformsource = None
    _sectionxformvalue = None
    _sectionxformsource = None
    _parse_exc = None
    _bom = False

    def __init__(self, fp=None, defaults=None, parse_exc=True,
                 optionxformvalue=lower, optionxformsource=None,
                 sectionxformvalue=None, sectionxformsource=None):
        self._data = LineContainer()
        self._parse_exc = parse_exc
        self._optionxformvalue = optionxformvalue
        self._optionxformsource = optionxformsource
        self._sectionxformvalue = sectionxformvalue
        self._sectionxformsource = sectionxformsource
        self._sections = {}
        if defaults is None: defaults = {}
        self._defaults = INISection(LineContainer(), optionxformsource=self)
        for name, value in defaults.items():
            self._defaults[name] = value
        if fp is not None:
            self._readfp(fp)

    _optionxform = _make_xform_property('_optionxform', 'optionxform')
    _sectionxform = _make_xform_property('_sectionxform', 'optionxform')

    def _getitem(self, key):
        if key == DEFAULTSECT:
            return self._defaults
        if self._sectionxform: key = self._sectionxform(key)
        return self._sections[key]

    def __setitem__(self, key, value):
        raise Exception('Values must be inside sections', key, value)

    def __delitem__(self, key):
        if self._sectionxform: key = self._sectionxform(key)
        for line in self._sections[key]._lines:
            self._data.contents.remove(line)
        del self._sections[key]

    def __iter__(self):
        d = set()
        d.add(DEFAULTSECT)
        for x in self._data.contents:
            if isinstance(x, LineContainer):
                if x.name not in d:
                    yield x.name
                    d.add(x.name)

    def _new_namespace(self, name):
        if self._data.contents:
            self._data.add(EmptyLine())
        obj = LineContainer(SectionLine(name))
        self._data.add(obj)
        if self._sectionxform: name = self._sectionxform(name)
        if name in self._sections:
            ns = self._sections[name]
            ns._lines.append(obj)
        else:
            ns = INISection(obj, defaults=self._defaults,
                            optionxformsource=self)
            self._sections[name] = ns
        return ns

    def __str__(self):
        if self._bom:
            fmt = u'\ufeff%s'
        else:
            fmt = '%s'
        return fmt % self._data.__str__()

    __unicode__ = __str__

    _line_types = [EmptyLine, CommentLine,
                   SectionLine, OptionLine,
                   ContinuationLine]

    def _parse(self, line):
        for linetype in self._line_types:
            lineobj = linetype.parse(line)
            if lineobj:
                return lineobj
        else:
            # can't parse line
            return None

    def _readfp(self, fp):
        cur_section = None
        cur_option = None
        cur_section_name = None
        cur_option_name = None
        pending_lines = []
        pending_empty_lines = False
        try:
            fname = fp.name
        except AttributeError:
            fname = '<???>'
        line_count = 0
        exc = None
        line = None

        for line in readline_iterator(fp):
            # Check for BOM on first line
            if line_count == 0 and isinstance(line, six.text_type):
                if line[0] == u'\ufeff':
                    line = line[1:]
                    self._bom = True

            line_obj = self._parse(line)
            line_count += 1

            if not cur_section and not isinstance(line_obj, (CommentLine, EmptyLine, SectionLine)):
                if self._parse_exc:
                    raise MissingSectionHeaderError(fname, line_count, line)
                else:
                    line_obj = make_comment(line)

            if line_obj is None:
                if self._parse_exc:
                    if exc is None:
                        exc = ParsingError(fname)
                    exc.append(line_count, line)
                line_obj = make_comment(line)

            if isinstance(line_obj, ContinuationLine):
                if cur_option:
                    if pending_lines:
                        cur_option.extend(pending_lines)
                        pending_lines = []
                        if pending_empty_lines:
                            optobj._compat_skip_empty_lines.add(cur_option_name)
                            pending_empty_lines = False
                    cur_option.add(line_obj)
                else:
                    # illegal continuation line - convert to comment
                    if self._parse_exc:
                        if exc is None:
                            exc = ParsingError(fname)
                        exc.append(line_count, line)
                    line_obj = make_comment(line)

            if isinstance(line_obj, OptionLine):
                if pending_lines:
                    cur_section.extend(pending_lines)
                    pending_lines = []
                    pending_empty_lines = False
                cur_option = LineContainer(line_obj)
                cur_section.add(cur_option)
                if self._optionxform:
                    cur_option_name = self._optionxform(cur_option.name)
                else:
                    cur_option_name = cur_option.name
                if cur_section_name == DEFAULTSECT:
                    optobj = self._defaults
                else:
                    optobj = self._sections[cur_section_name]
                optobj._options[cur_option_name] = cur_option

            if isinstance(line_obj, SectionLine):
                self._data.extend(pending_lines)
                pending_lines = []
                pending_empty_lines = False
                cur_section = LineContainer(line_obj)
                self._data.add(cur_section)
                cur_option = None
                cur_option_name = None
                if cur_section.name == DEFAULTSECT:
                    self._defaults._lines.append(cur_section)
                    cur_section_name = DEFAULTSECT
                else:
                    if self._sectionxform:
                        cur_section_name = self._sectionxform(cur_section.name)
                    else:
                        cur_section_name = cur_section.name
                    if cur_section_name not in self._sections:
                        self._sections[cur_section_name] = \
                                INISection(cur_section, defaults=self._defaults,
                                           optionxformsource=self)
                    else:
                        self._sections[cur_section_name]._lines.append(cur_section)

            if isinstance(line_obj, (CommentLine, EmptyLine)):
                pending_lines.append(line_obj)
                if isinstance(line_obj, EmptyLine):
                    pending_empty_lines = True

        self._data.extend(pending_lines)
        if line and line[-1] == '\n':
            self._data.add(EmptyLine())

        if exc:
            raise exc
