# Copyright (c) 2011 Canonical Ltd
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

"""Django glue for OOPS integration.

To use:
* Use OOPSWSGIHandler rather than than WSGIHandler.
* Create an oops wrapper with oops_wsgi.make_app(..., oops_on_status=['500'])

This is not needed if you have https://code.djangoproject.com/ticket/16674
fixed in your Django.
"""

from __future__ import absolute_import, print_function

from django.core.handlers import wsgi

__all__ = [
    'OOPSWSGIHandler',
    ]

class OOPSWSGIHandler(wsgi.WSGIHandler):

    def handle_uncaught_exception(self, request, resolver, exc_info):
        if 'oops.context' in request.environ:
            # We are running under python-oops-wsgi - inject the exception into
            # its context. This will provide the exception to the handler, and
            # if you use oops_on_status=['500'] OOPS reports will be created
            # when Django has suffered a failure.
            request.environ['oops.context']['exc_info'] = exc_info
        # Now perform the default django uncaught exception behaviour.
        return super(OOPSWSGIHandler, self).handle_uncaught_exception(
            request, resolver, exc_info)
