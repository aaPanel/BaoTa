# -*- coding: utf-8 -*-
#
# Copyright (c) 2011-2012 Red Hat, Inc
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
Kitchen

Aggregate of a bunch of unrelated but helpful python modules.
'''

# Pylint disabled messages:
# :C0103: We need gettext aliases for both unicode strings and byte strings.
#   The byte string one (b_) triggers this warning.
from kitchen import i18n
from kitchen import versioning

(_, N_) = i18n.easy_gettext_setup('kitchen.core')
#pylint: disable-msg=C0103
(b_, bN_) = i18n.easy_gettext_setup('kitchen.core', use_unicode=False)
#pylint: enable-msg=C0103

__version_info__ = ((1, 2, 6),)
__version__ = versioning.version_tuple_to_string(__version_info__)

__all__ = ('exceptions', 'release',)
