# Copyright (c) 2012, Canonical Ltd
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

"""Trace OOPS reports coming from an AMQP queue."""

from __future__ import absolute_import, print_function

from functools import partial
import sys
import optparse
from textwrap import dedent

import amqp
import oops
import oops_amqp


def main(argv=None):
    if argv is None:
        argv=sys.argv
    usage = dedent("""\
        %prog [options]

        The following options must be supplied:
         --host

        e.g.
        oops-amqp-trace --host "localhost:3472"

        If you do not have a persistent queue, you should run this script
        before generating oopses, as AMQP will discard messages with no
        consumers.
        """)
    description = "Trace OOPS reports coming from an AMQP queue."
    parser = optparse.OptionParser(
        description=description, usage=usage)
    parser.add_option('--host', help="AQMP host / host:port.")
    parser.add_option('--username', help="AQMP username.", default="guest")
    parser.add_option('--password', help="AQMP password.", default="guest")
    parser.add_option('--vhost', help="AMQP vhost.", default="/")
    parser.add_option('--exchange', help="AMQP exchange name.", default="oopses")
    options, args = parser.parse_args(argv[1:])
    def needed(optname):
        if getattr(options, optname, None) is None:
            raise ValueError('option "%s" must be supplied' % optname)
    needed('host')
    factory = partial(
        amqp.Connection, host=options.host, userid=options.username,
        password=options.password, virtual_host=options.vhost)
    connection = factory()
    channel = connection.channel()
    channel.exchange_declare(options.exchange, type="fanout", durable=False,
        auto_delete=True)
    queue = channel.queue_declare(durable=False, auto_delete=True)[0]
    channel.queue_bind(queue, options.exchange)
    config = oops.Config()
    config.publisher = oops.pprint_to_stream(sys.stdout)
    receiver = oops_amqp.Receiver(config, factory, queue)
    try:
        receiver.run_forever()
    except KeyboardInterrupt:
        pass
