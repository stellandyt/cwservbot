#
# Copyright (c) 2011, Canonical Ltd
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, version 3 only.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# GNU Lesser General Public License version 3 (see the file LICENSE).

"""oops <-> wsgi integration.

oops_wsgi provides integration with an oops.Config, permitting errors in your
web application to be gathered centrally, with tracebacks and other diagnostic
information.

Typically, something like this:

* Setup your configuration::

  >>> from oops import Config
  >>> config = Config()

Note that you will probably want at least one publisher, or your reports will
be discarded.

* Add in wsgi specific hooks to the config::

  >>> oops_wsgi.install_hooks(config)

This is a convenience function - you are welcome to pick and choose the creation
or filter hooks you want from oops_wsgi.hooks.

* Create your wsgi app as normal, and then wrap it::

  >>> app = oops_wsgi.make_app(app, config)

If any exception bubbles up through this middleware, an oops will be logged. If
the body of the request had not started, then a custom page is shown that
shows the OOPS id, and the exception is swallowed. Exceptions that indicate
normal situations like end-of-file on a socket do not trigger OOPSes. If the
OOPS is filtered, or no publishers are configured, then the exception will
propogate up the stack - the oops middleware cannot do anything useful in these
cases. (For instance, if you have a custom 404 middleware above the oops
middleware in the wsgi stack, and filter 404 exceptions so they do not create
reports, then if the oops middleware did anything other than propogate the
exception, your custom 404 middleware would not work.

If the body had started, then there is no way to communicate the OOPS id to the
client and the exception will propogate up the wsgi app stack.

You can customise the error page if you supply a helper that accepts (environ,
report) and returns HTML to be sent to the client.

   >>> def myerror_html(environ, report):
   ...    return '<html><body><h1>OOPS! %s</h1></body></html>' % report['id']
   >>> app = oops_wsgi.make_app(app, config, error_render=myerror_html)

Or you can supply a string template to be formatted with the report.

   >>> json_template='{"oopsid" : "%(id)s"}'
   >>> app = oops_wsgi.make_app(app, config, error_template=json_template)

If the wrapped app errors by sending exc_info to start_response, that will be
used to create an OOPS report, and the id added to the headers under the
X-Oops-Id header. This is also present when an OOPS is triggered by catching an
exception in the wrapped app (as long as the body hasn't started).

You can request that reports be created when a given status code is used (e.g.
to gather stats on the number of 404's occuring without doing log processing).

   >>> app = oops_wsgi.make_app(app, config, oops_on_status=['404'])

The oops middleware injects two variables into the WSGI environ to make it easy
for cooperating code to report additional data.

The `oops.report` variable is a dict which is copied into the report. See the
`oops` package documentation for documentation on what should be present in an
oops report. This requires the update_report hook to be installed (which
`install_hooks` will do for you).

The `oops.context` variable is a dict used for generating the report - keys and
values added to that can be used in the `config.on_create` hooks to populate
custom data without needing to resort to global variables.

If a timeline is present in the WSGI environ (as 'timeline.timeline') it is
automatically captured to the oops context when generating an OOPS. See the
oops-timeline module for hooks to use this.

`pydoc oops_wsgi.make_app` describes the entire capabilities of the
middleware.
"""


from __future__ import absolute_import, print_function

# same format as sys.version_info: "A tuple containing the five components of
# the version number: major, minor, micro, releaselevel, and serial. All
# values except releaselevel are integers; the release level is 'alpha',
# 'beta', 'candidate', or 'final'. The version_info value corresponding to the
# Python version 2.0 is (2, 0, 0, 'final', 0)."  Additionally we use a
# releaselevel of 'dev' for unreleased under-development code.
#
# If the releaselevel is 'alpha' then the major/minor/micro components are not
# established at this point, and setup.py will use a version of next-$(revno).
# If the releaselevel is 'final', then the tarball will be major.minor.micro.
# Otherwise it is major.minor.micro~$(revno).
__version__ = (0, 0, 10, 'beta', 0)

__all__ = [
    'install_hooks',
    'make_app'
    ]

from oops_wsgi.middleware import make_app
from oops_wsgi.hooks import install_hooks
