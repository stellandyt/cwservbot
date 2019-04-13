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

"""Various hooks that can be used to populate OOPS reports.

The default_hooks list contains some innocuous hooks which most reporters will
want.
"""

from __future__ import absolute_import, print_function

__all__ = [
    'attach_exc_info',
    'attach_date',
    'attach_hostname',
    'copy_reporter',
    'copy_topic',
    'copy_url',
    'default_hooks',
    'safe_unicode',
    ]

__metaclass__ = type

import datetime
import socket
import traceback

from pytz import utc
import six

# Used to detect missing keys.
_sentinel = object()


def _simple_copy(key):
    """Curry a simple hook that copies a key from context to report."""
    def copy_key(report, context):
        value = context.get(key, _sentinel)
        if value is not _sentinel:
            report[key] = value
    copy_key.__doc__ = (
            "Copy the %s field from context to report, if present." % key)
    return copy_key

copy_reporter = _simple_copy('reporter')
copy_topic = _simple_copy('topic')
copy_url = _simple_copy('url')
 

def safe_unicode(obj):
    """Used to reliably get *a* string for an object.

    This is called on objects like exceptions, where bson won't be able to
    serialize it, but a representation is needed for the report. It is
    exposed a convenience for other on_create hook authors.
    """
    if isinstance(obj, six.text_type):
        return obj
    # A call to str(obj) could raise anything at all.
    # We'll ignore these errors, and print something
    # useful instead, but also log the error.
    # We disable the pylint warning for the blank except.
    try:
        value = six.text_type(obj)
    except:
        value = u'<unprintable %s object>' % (
            six.text_type(type(obj).__name__))
    # Some objects give back bytestrings to __unicode__...
    if isinstance(value, six.binary_type):
        value = value.decode('latin-1')
    return value


def attach_date(report, context):
    """Set the time key in report to a datetime of now."""
    report['time'] = datetime.datetime.now(utc)


def attach_exc_info(report, context):
    """Attach exception info to the report.

    This reads the 'exc_info' key from the context and sets the:
    * type
    * value
    * tb_text 
    keys in the report.

    exc_info must be a tuple, but it can contain either live exception
    information or simple strings (allowing exceptions that have been
    serialised and received over the network to be reported).
    """
    info = context.get('exc_info')
    if info is None:
        return
    report['type'] = getattr(info[0], '__name__', info[0])
    report['value'] = safe_unicode(info[1])
    if isinstance(info[2], six.string_types):
        tb_text = info[2]
    else:
        tb_text = u''.join(map(safe_unicode, traceback.format_tb(info[2])))
    report['tb_text'] = tb_text


def attach_hostname(report, context):
    """Add the machine's hostname to report in the 'hostname' key."""
    report['hostname'] = socket.gethostname()


# hooks that are installed into Config objects by default.
default_hooks = [
    attach_exc_info,
    attach_date,
    copy_reporter,
    copy_topic,
    copy_url,
    attach_hostname,
    ]
