# -*- coding: utf-8 -*-
#
# Copyright (c) 2010 Red Hat, Inc
#
# kitchen is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# kitchen is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with kitchen; if not, see <http://www.gnu.org/licenses/>
#
# Authors:
#   Toshio Kuratomi <toshio@fedoraproject.org>
#
'''
-----------------------
Kitchen.text exceptions
-----------------------

Exception classes thrown by kitchen's text processing routines.
'''
from kitchen import exceptions

class XmlEncodeError(exceptions.KitchenError):
    '''Exception thrown by error conditions when encoding an xml string.
    '''
    pass

class ControlCharError(exceptions.KitchenError):
    '''Exception thrown when an ascii control character is encountered.
    '''
    pass

__all__ = ('XmlEncodeError', 'ControlCharError')
