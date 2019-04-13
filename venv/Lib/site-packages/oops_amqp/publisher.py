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

"""Publish OOPS reports over amqp."""

from __future__ import absolute_import, print_function

__metaclass__ = type

from hashlib import md5
from threading import local

import amqp

from oops_amqp.anybson import dumps
from oops_amqp.utils import (
    amqplib_error_types,
    is_amqplib_connection_error,
    )

__all__ = [
    'Publisher',
    ]

class Publisher:
    """Publish OOPS reports over AMQP.
    
    Messages are published as bson dicts via durable messages sent to a
    supplied exchange + routing key.
    """

    def __init__(self, connection_factory, exchange_name, routing_key,
            inherit_id=False):
        """Create a publisher.

        :param connection_factory: A callable which creates an amqplib
            Connection when called. This is used to create connections - one
            per thread which OOPS publishing happens in. This is because
            amqplib is not threadsafe and recommends not sharing connections
            across threads.
        :param exchange_name: The name of the exchange to publish to.
        :param routing_key: The routing key for messages.
        :param inherit_id: If True any 'True' 'id' in an OOPS report is
            preserved. Handy if an id that has already been shown to a user is
            being published (but uniqueness cannot be guaranteed).
        """
        self.connection_factory = connection_factory
        self.exchange_name = exchange_name
        self.routing_key = routing_key
        self.channels = local()
        self.inherit_id = inherit_id

    def get_channel(self):
        if getattr(self.channels, 'channel', None) is None:
            try:
                connection = self.connection_factory()
                connection.connect()
                self.channels.channel = connection.channel()
            except amqplib_error_types as e:
                if is_amqplib_connection_error(e):
                    # Could not connect
                    return None
                # Unknown error mode : don't hide it.
                raise
        return self.channels.channel

    def __call__(self, report):
        # Don't mess with the passed in report.
        report = dict(report)
        if not self.inherit_id or not report.get('id'):
            # Discard any existing id.
            original_id = report.pop('id', None)
            # Hash it, to make an ID
            oops_id = "OOPS-%s" % md5(dumps(report)).hexdigest()
            # Store the id in what we send on the wire, so that the recipient
            # has it.
            report['id'] = oops_id
        message = amqp.Message(dumps(report))
        # We don't want to drop OOPS on the floor if rabbit is restarted.
        message.properties["delivery_mode"] = 2
        channel = self.get_channel()
        if channel is None:
            return []
        try:
            channel.basic_publish(
                message, self.exchange_name, routing_key=self.routing_key)
        except amqplib_error_types as e:
            self.channels.channel = None
            if is_amqplib_connection_error(e):
                # Could not connect / interrupted connection
                return []
            # Unknown error mode : don't hide it.
            raise
        return [report['id']]
