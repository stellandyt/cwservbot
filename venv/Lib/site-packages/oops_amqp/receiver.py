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

"""Receive OOPS reports over amqp and republish locally."""

from __future__ import absolute_import, print_function

__metaclass__ = type

import time

from oops_amqp import anybson as bson
from oops_amqp.utils import (
    amqplib_error_types,
    close_ignoring_connection_errors,
    is_amqplib_connection_error,
    )

__all__ = [
    'Receiver',
    ]

class Receiver:
    """Republish OOPS reports from AMQP to a local oops.Config.
    
    :ivar stopping: When True will cause Receiver to break out of run_forever.
        Calls to run_forever reset this to False.
    :ivar sentinel: If a message identical to the sentinel is received,
        handle_report will set stopping to True.
    """

    def __init__(self, config, connection_factory, queue_name):
        """Create a Receiver.

        :param config: An oops.Config to republish the OOPS reports.
        :param connection_factory: An amqplib connection factory, used to make
            the initial connection and to reconnect if that connection is
            interrupted.
        :param queue_name: The queue to listen for reports on.
        """
        self.config = config
        self.connection = None
        self.channel = None
        self.connection_factory = connection_factory
        self.queue_name = queue_name
        self.sentinel = None

    def handle_report(self, message):
        # bson requires bytes.
        body = message.body
        if not isinstance(body, bytes):
            body = body.encode(message.content_encoding or 'UTF-8')
        if body == self.sentinel:
            self.stopping = True
            self.channel.basic_ack(message.delivery_tag)
            return
        try:
            report = bson.loads(body)
        except KeyError:
            # Garbage in the queue. Possibly this should raise an OOPS itself
            # (through a different config) or log an info level message.
            pass
        self.config.publish(report)
        # ACK last so errors here don't eat the message.
        self.channel.basic_ack(message.delivery_tag)
    
    def run_forever(self):
        """Run in a loop handling messages.

        If the amqp server is down or uncontactable for > 120 seconds, error
        out.
        """
        self.stopping = False
        self.went_bad = None
        while (not self.stopping and
               (not self.went_bad or time.time() < self.went_bad + 120)):
            try:
                self._run_forever()
            except amqplib_error_types as e:
                if not is_amqplib_connection_error(e):
                    # Something unknown went wrong.
                    raise
                if not self.went_bad:
                    self.went_bad = time.time()
                # Don't probe immediately, give the network/process time to
                # come back.
                time.sleep(0.1)

    def _run_forever(self):
        self.connection = self.connection_factory()
        self.connection.connect()
        # A successful connection: record this so run_forever won't bail early.
        self.went_bad = None
        try:
            self.channel = self.connection.channel()
            try:
                self.consume_tag = self.channel.basic_consume(
                    self.queue_name, callback=self.handle_report)
                try:
                    while True:
                        self.connection.drain_events(timeout=1)
                        if self.stopping:
                            break
                finally:
                    if self.channel.is_open:
                        self.channel.basic_cancel(self.consume_tag)
            finally:
                close_ignoring_connection_errors(self.channel)
        finally:
            close_ignoring_connection_errors(self.connection)
