# -*- coding: utf-8 -*-
# Copyright (C) 2013 Sebastian Wiesner <lunaryorn@gmail.com>

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
    pyudev._os.poll
    ===============

    Operating system interface for pyudev.

    .. moduleauthor:: Sebastian Wiesner  <lunaryorn@gmail.com>
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import select

from pyudev._util import eintr_retry_call


class Poll(object):
    """A poll object.

    This object essentially provides a more convenient interface around
    :class:`select.poll`.

    """

    _EVENT_TO_MASK = {'r': select.POLLIN, 'w': select.POLLOUT}

    @staticmethod
    def _has_event(events, event):
        return events & event != 0

    @classmethod
    def for_events(cls, *events):
        """Listen for ``events``.

        ``events`` is a list of ``(fd, event)`` pairs, where ``fd`` is a file
        descriptor or file object and ``event`` either ``'r'`` or ``'w'``.  If
        ``r``, listen for whether that is ready to be read.  If ``w``, listen
        for whether the channel is ready to be written to.

        """
        notifier = eintr_retry_call(select.poll)
        for fd, event in events:
            mask = cls._EVENT_TO_MASK.get(event)
            if not mask:
                raise ValueError('Unknown event type: {0!r}'.format(event))
            notifier.register(fd, mask)
        return cls(notifier)

    def __init__(self, notifier):
        """Create a poll object for the given ``notifier``.

        ``notifier`` is the :class:`select.poll` object wrapped by the new poll
        object.

        """
        self._notifier = notifier

    def poll(self, timeout=None):
        """Poll for events.

        ``timeout`` is an integer specifying how long to wait for events (in
        milliseconds).  If omitted, ``None`` or negative, wait until an event
        occurs.

        Return a list of all events that occurred before ``timeout``, where
        each event is a pair ``(fd, event)``. ``fd`` is the integral file
        descriptor, and ``event`` a string indicating the event type.  If
        ``'r'``, there is data to read from ``fd``.  If ``'w'``, ``fd`` is
        writable without blocking now.  If ``'h'``, the file descriptor was
        hung up (i.e. the remote side of a pipe was closed).

        """
        # Return a list to allow clients to determine whether there are any
        # events at all with a simple truthiness test.
        return list(
            self._parse_events(eintr_retry_call(self._notifier.poll, timeout)))

    def _parse_events(self, events):
        """Parse ``events``.

        ``events`` is a list of events as returned by
        :meth:`select.poll.poll()`.

        Yield all parsed events.

        """
        for fd, event_mask in events:
            if self._has_event(event_mask, select.POLLNVAL):
                raise IOError('File descriptor not open: {0!r}'.format(fd))
            elif self._has_event(event_mask, select.POLLERR):
                raise IOError('Error while polling fd: {0!r}'.format(fd))

            if self._has_event(event_mask, select.POLLIN):
                yield fd, 'r'
            if self._has_event(event_mask, select.POLLOUT):
                yield fd, 'w'
            if self._has_event(event_mask, select.POLLHUP):
                yield fd, 'h'
