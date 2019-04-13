# Copyright (c) 2010, 2011, Canonical Ltd
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

"""oops creation and filtering hooks for working with WSGI."""

from __future__ import absolute_import, print_function

import re

__all__ = [
    'copy_environ',
    'hide_cookie',
    'install_hooks',
    'update_report',
    ]

_wsgi_standard_env_keys = set([
    'REQUEST_METHOD',
    'SCRIPT_NAME',
    'PATH_INFO',
    'QUERY_STRING',
    'CONTENT_TYPE',
    'CONTENT_LENGTH',
    'SERVER_NAME',
    'SERVER_PORT',
    'SERVER_PROTOCOL',
    'wsgi.version',
    'wsgi.url_scheme',
    ])


def copy_environ(report, context):
    """Copy useful variables from the wsgi environment if it is present.

    This should be in the context as 'wsgi_environ'.

    e.g. 
    report = config.create(context=dict(wsgi_environ=environ))
    """
    environ = context.get('wsgi_environ', {})
    if 'req_vars' not in report:
        report['req_vars'] = {}
    req_vars = report['req_vars']
    for key, value in sorted(environ.items()):
        if (key in _wsgi_standard_env_keys or
                key.startswith('HTTP_')):
            req_vars[key] = value


def hide_cookie(report, context):
    """If there is an HTTP_COOKIE entry in the report, hide its value.

    The entry is looked for either as a top level key or in the req_vars dict.

    The COOKIE header is often used to carry session tokens and thus permits
    folk analyzing crash reports to log in as an arbitrary user (e.g. your
    sysadmin users).

    The same goes for the AUTHORIZATION header, although in that case we
    permit the authorization scheme to remain visible.
    """
    if 'HTTP_COOKIE' in report:
        report['HTTP_COOKIE'] = '<hidden>'
    if 'HTTP_COOKIE' in report.get('req_vars', {}):
        report['req_vars']['HTTP_COOKIE'] = '<hidden>'
    if 'HTTP_AUTHORIZATION' in report:
        report['HTTP_AUTHORIZATION'] = re.sub(
            r'(.*?)\s+.*', r'\1 <hidden>', report['HTTP_AUTHORIZATION'])
    if 'HTTP_AUTHORIZATION' in report.get('req_vars', {}):
        report['req_vars']['HTTP_AUTHORIZATION'] = re.sub(
            r'(.*?)\s+.*', r'\1 <hidden>',
            report['req_vars']['HTTP_AUTHORIZATION'])


def install_hooks(config):
    """Install the default wsgi hooks into config."""
    config.on_create.extend([copy_environ, hide_cookie])
    config.on_create.insert(0, update_report)


def update_report(report, context):
    """Copy the oops.report contents from the wsgi environment to report."""
    report.update(context.get('wsgi_environ', {}).get('oops.report', {}))
