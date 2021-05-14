# Copyright (c) 2001, 2002, 2003 Python Software Foundation
# Copyright (c) 2004-2008 Paramjit Oberoi <param.cs.wisc.edu>
# All Rights Reserved.  See LICENSE-PSF & LICENSE for details.

"""Compatibility interfaces for ConfigParser

Interfaces of ConfigParser, RawConfigParser and SafeConfigParser
should be completely identical to the Python standard library
versions.  Tested with the unit tests included with Python-2.3.4

The underlying INIConfig object can be accessed as cfg.data
"""

import re
from .configparser import DuplicateSectionError,    \
                   NoSectionError, NoOptionError,   \
                   InterpolationMissingOptionError, \
                   InterpolationDepthError,         \
                   InterpolationSyntaxError,        \
                   DEFAULTSECT, MAX_INTERPOLATION_DEPTH

# These are imported only for compatiability.
# The code below does not reference them directly.
from .configparser import Error, InterpolationError, \
                   MissingSectionHeaderError, ParsingError

import six

from . import ini


class RawConfigParser(object):
    def __init__(self, defaults=None, dict_type=dict):
        if dict_type != dict:
            raise ValueError('Custom dict types not supported')
        self.data = ini.INIConfig(defaults=defaults, optionxformsource=self)

    def optionxform(self, optionstr):
        return optionstr.lower()

    def defaults(self):
        d = {}
        secobj = self.data._defaults
        for name in secobj._options:
            d[name] = secobj._compat_get(name)
        return d

    def sections(self):
        """Return a list of section names, excluding [DEFAULT]"""
        return list(self.data)

    def add_section(self, section):
        """Create a new section in the configuration.

        Raise DuplicateSectionError if a section by the specified name
        already exists.  Raise ValueError if name is DEFAULT or any of
        its case-insensitive variants.
        """
        # The default section is the only one that gets the case-insensitive
        # treatment - so it is special-cased here.
        if section.lower() == "default":
            raise ValueError('Invalid section name: %s' % section)

        if self.has_section(section):
            raise DuplicateSectionError(section)
        else:
            self.data._new_namespace(section)

    def has_section(self, section):
        """Indicate whether the named section is present in the configuration.

        The DEFAULT section is not acknowledged.
        """
        return section in self.data

    def options(self, section):
        """Return a list of option names for the given section name."""
        if section in self.data:
            return list(self.data[section])
        else:
            raise NoSectionError(section)

    def read(self, filenames):
        """Read and parse a filename or a list of filenames.

        Files that cannot be opened are silently ignored; this is
        designed so that you can specify a list of potential
        configuration file locations (e.g. current directory, user's
        home directory, systemwide directory), and all existing
        configuration files in the list will be read.  A single
        filename may also be given.
        """
        files_read = []
        if isinstance(filenames, six.string_types):
            filenames = [filenames]
        for filename in filenames:
            try:
                fp = open(filename)
            except IOError:
                continue
            files_read.append(filename)
            self.data._readfp(fp)
            fp.close()
        return files_read

    def readfp(self, fp, filename=None):
        """Like read() but the argument must be a file-like object.

        The `fp' argument must have a `readline' method.  Optional
        second argument is the `filename', which if not given, is
        taken from fp.name.  If fp has no `name' attribute, `<???>' is
        used.
        """
        self.data._readfp(fp)

    def get(self, section, option, vars=None):
        if not self.has_section(section):
            raise NoSectionError(section)

        sec = self.data[section]
        if option in sec:
            return sec._compat_get(option)
        else:
            raise NoOptionError(option, section)

    def items(self, section):
        if section in self.data:
            ans = []
            for opt in self.data[section]:
                ans.append((opt, self.get(section, opt)))
            return ans
        else:
            raise NoSectionError(section)

    def getint(self, section, option):
        return int(self.get(section, option))

    def getfloat(self, section, option):
        return float(self.get(section, option))

    _boolean_states = {'1': True, 'yes': True, 'true': True, 'on': True,
                       '0': False, 'no': False, 'false': False, 'off': False}

    def getboolean(self, section, option):
        v = self.get(section, option)
        if v.lower() not in self._boolean_states:
            raise ValueError('Not a boolean: %s' % v)
        return self._boolean_states[v.lower()]

    def has_option(self, section, option):
        """Check for the existence of a given option in a given section."""
        if section in self.data:
            sec = self.data[section]
        else:
            raise NoSectionError(section)
        return (option in sec)

    def set(self, section, option, value):
        """Set an option."""
        if section in self.data:
            self.data[section][option] = value
        else:
            raise NoSectionError(section)

    def write(self, fp):
        """Write an .ini-format representation of the configuration state."""
        fp.write(str(self.data))

    def remove_option(self, section, option):
        """Remove an option."""
        if section in self.data:
            sec = self.data[section]
        else:
            raise NoSectionError(section)
        if option in sec:
            del sec[option]
            return 1
        else:
            return 0

    def remove_section(self, section):
        """Remove a file section."""
        if not self.has_section(section):
            return False
        del self.data[section]
        return True


class ConfigDict(object):
    """Present a dict interface to a ini section."""

    def __init__(self, cfg, section, vars):
        self.cfg = cfg
        self.section = section
        self.vars = vars

    def __getitem__(self, key):
        try:
            return RawConfigParser.get(self.cfg, self.section, key, self.vars)
        except (NoOptionError, NoSectionError):
            raise KeyError(key)


class ConfigParser(RawConfigParser):

    def get(self, section, option, raw=False, vars=None):
        """Get an option value for a given section.

        All % interpolations are expanded in the return values, based on the
        defaults passed into the constructor, unless the optional argument
        `raw' is true.  Additional substitutions may be provided using the
        `vars' argument, which must be a dictionary whose contents overrides
        any pre-existing defaults.

        The section DEFAULT is special.
        """
        if section != DEFAULTSECT and not self.has_section(section):
            raise NoSectionError(section)

        option = self.optionxform(option)
        value = RawConfigParser.get(self, section, option, vars)

        if raw:
            return value
        else:
            d = ConfigDict(self, section, vars)
            return self._interpolate(section, option, value, d)

    def _interpolate(self, section, option, rawval, vars):
        # do the string interpolation
        value = rawval
        depth = MAX_INTERPOLATION_DEPTH
        while depth:                    # Loop through this until it's done
            depth -= 1
            if "%(" in value:
                try:
                    value = value % vars
                except KeyError as e:
                    raise InterpolationMissingOptionError(
                        option, section, rawval, e.args[0])
            else:
                break
        if value.find("%(") != -1:
            raise InterpolationDepthError(option, section, rawval)
        return value

    def items(self, section, raw=False, vars=None):
        """Return a list of tuples with (name, value) for each option
        in the section.

        All % interpolations are expanded in the return values, based on the
        defaults passed into the constructor, unless the optional argument
        `raw' is true.  Additional substitutions may be provided using the
        `vars' argument, which must be a dictionary whose contents overrides
        any pre-existing defaults.

        The section DEFAULT is special.
        """
        if section != DEFAULTSECT and not self.has_section(section):
            raise NoSectionError(section)
        if vars is None:
            options = list(self.data[section])
        else:
            options = []
            for x in self.data[section]:
                if x not in vars:
                    options.append(x)
            options.extend(vars.keys())

        if "__name__" in options:
            options.remove("__name__")

        d = ConfigDict(self, section, vars)
        if raw:
            return [(option, d[option])
                    for option in options]
        else:
            return [(option, self._interpolate(section, option, d[option], d))
                    for option in options]


class SafeConfigParser(ConfigParser):
    _interpvar_re = re.compile(r"%\(([^)]+)\)s")
    _badpercent_re = re.compile(r"%[^%]|%$")

    def set(self, section, option, value):
        if not isinstance(value, six.string_types):
            raise TypeError("option values must be strings")
        # check for bad percent signs:
        # first, replace all "good" interpolations
        tmp_value = self._interpvar_re.sub('', value)
        # then, check if there's a lone percent sign left
        m = self._badpercent_re.search(tmp_value)
        if m:
            raise ValueError("invalid interpolation syntax in %r at "
                             "position %d" % (value, m.start()))

        ConfigParser.set(self, section, option, value)

    def _interpolate(self, section, option, rawval, vars):
        # do the string interpolation
        L = []
        self._interpolate_some(option, L, rawval, section, vars, 1)
        return ''.join(L)

    _interpvar_match = re.compile(r"%\(([^)]+)\)s").match

    def _interpolate_some(self, option, accum, rest, section, map, depth):
        if depth > MAX_INTERPOLATION_DEPTH:
            raise InterpolationDepthError(option, section, rest)
        while rest:
            p = rest.find("%")
            if p < 0:
                accum.append(rest)
                return
            if p > 0:
                accum.append(rest[:p])
                rest = rest[p:]
            # p is no longer used
            c = rest[1:2]
            if c == "%":
                accum.append("%")
                rest = rest[2:]
            elif c == "(":
                m = self._interpvar_match(rest)
                if m is None:
                    raise InterpolationSyntaxError(option, section, "bad interpolation variable reference %r" % rest)
                var = m.group(1)
                rest = rest[m.end():]
                try:
                    v = map[var]
                except KeyError:
                    raise InterpolationMissingOptionError(
                        option, section, rest, var)
                if "%" in v:
                    self._interpolate_some(option, accum, v,
                                           section, map, depth + 1)
                else:
                    accum.append(v)
            else:
                raise InterpolationSyntaxError(
                    option, section,
                    "'%' must be followed by '%' or '(', found: " + repr(rest))
