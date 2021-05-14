# -*- coding: utf-8 -*-
# Copyright (C) 2011 Sebastian Wiesner <lunaryorn@gmail.com>

# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation; either version 2.1 of the License, or (at your
# option) any later version.

# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
# for more details.

# You should have received a copy of the GNU Lesser General Public License
# along with this library; if not, write to the Free Software Foundation,
# Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
"""
    pyudev._compat
    ==============

    Compatibility for Python versions, that lack certain functions.

    .. moduleauthor::  Sebastian Wiesner  <lunaryorn@gmail.com>
"""

from __future__ import (print_function, division, unicode_literals,
                        absolute_import)

from subprocess import Popen, CalledProcessError, PIPE


def check_output(command):
    """
    Compatibility with :func:`subprocess.check_output` from Python 2.7 and
    upwards.
    """
    proc = Popen(command, stdout=PIPE)
    output = proc.communicate()[0]
    if proc.returncode != 0:
        raise CalledProcessError(proc.returncode, command)
    return output
