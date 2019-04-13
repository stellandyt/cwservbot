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

"""Utility functions for oops_amqp."""

from __future__ import absolute_import, print_function

import socket

from amqp.exceptions import ConnectionError

__all__ = [
    'amqplib_error_types',
    'close_ignoring_connection_errors',
    'is_amqplib_connection_error',
    'is_amqplib_ioerror',
    ]

# These exception types always indicate an AMQP connection error/closure.
# However you should catch amqplib_error_types and post-filter with
# is_amqplib_connection_error.
amqplib_connection_errors = (socket.error, ConnectionError)
# A tuple to reduce duplication in different code paths. Lists the types of
# exceptions legitimately raised by amqplib when the AMQP server goes down.
# Not all exceptions *will* be such errors - use is_amqplib_connection_error to
# do a second-stage filter after catching the exception.
amqplib_error_types = amqplib_connection_errors + (IOError,)


def close_ignoring_connection_errors(closable):
    try:
        return closable.close()
    except amqplib_error_types as e:
        if is_amqplib_connection_error(e):
            return
        raise


def is_amqplib_ioerror(e):
    """Returns True if e is an amqplib internal exception."""
    # Raised by amqplib rather than socket.error on ssl issues and short reads.
    return type(e) is IOError and e.args == ('Socket error',)


def is_amqplib_connection_error(e):
    """Return True if e was (probably) raised due to a connection issue."""
    return isinstance(e, amqplib_connection_errors) or is_amqplib_ioerror(e)
