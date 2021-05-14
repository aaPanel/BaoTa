'''
Information about this kitchen release.
'''

from kitchen import _, __version__

NAME = 'kitchen'
VERSION = __version__
DESCRIPTION = _('Kitchen contains a cornucopia of useful code')
LONG_DESCRIPTION = _('''
We've all done it.  In the process of writing a brand new application we've
discovered that we need a little bit of code that we've invented before.
Perhaps it's something to handle unicode text.  Perhaps it's something to make
a bit of python-2.5 code run on python-2.3.  Whatever it is, it ends up being
a tiny bit of code that seems too small to worry about pushing into its own
module so it sits there, a part of your current project, waiting to be cut and
pasted into your next project.  And the next.  And the next.  And since that
little bittybit of code proved so useful to you, it's highly likely that it
proved useful to someone else as well.  Useful enough that they've written it
and copy and pasted it over and over into each of their new projects.

Well, no longer!  Kitchen aims to pull these small snippets of code into a few
python modules which you can import and use within your project.  No more copy
and paste!  Now you can let someone else maintain and release these small
snippets so that you can get on with your life.
''')
AUTHOR = 'Toshio Kuratomi, Seth Vidal, others'
EMAIL = 'toshio@fedoraproject.org'
COPYRIGHT = '2012 Red Hat, Inc. and others'
URL = 'https://fedorahosted.org/kitchen'
DOWNLOAD_URL = 'https://pypi.python.org/pypi/kitchen'
LICENSE = 'LGPLv2+'

__all__ = ('NAME', 'VERSION', 'DESCRIPTION', 'LONG_DESCRIPTION', 'AUTHOR',
        'EMAIL', 'COPYRIGHT', 'URL', 'DOWNLOAD_URL', 'LICENSE')
