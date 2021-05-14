Introduction to iniparse
------------------------

[![Build Status](https://travis-ci.org/candlepin/python-iniparse.svg?branch=master)](https://travis-ci.org/candlepin/python-iniparse)

iniparse is a INI parser for Python which is:

* Compatible with ConfigParser: Backward compatible implementations
  of ConfigParser, RawConfigParser, and SafeConfigParser are included
  that are API-compatible with the Python standard library.

* Preserves structure of INI files: Order of sections & options,
  indentation, comments, and blank lines are preserved as far as
  possible when data is updated.

* More convenient: Values can be accessed using dotted notation
  (`cfg.user.name`), or using container syntax (`cfg['user']['name']`).

It is very useful for config files that are updated both by users and by
programs, since it is very disorienting for a user to have her config file
completely rearranged whenever a program changes it. iniparse also allows
making the order of entries in a config file significant, which is desirable
in applications like image galleries.

Website: https://github.com/candlepin/python-iniparse/


Copyright (c) 2001-2008 Python Software Foundation

Copyright (c) 2004-2009 Paramjit Oberoi <param.cs.wisc.edu>

Copyright (c) 2007 Tim Lauridsen <tla@rasmil.dk>

All Rights Reserved.  See LICENSE-PSF & LICENSE for details.
