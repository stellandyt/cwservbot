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

"""Publish OOPS reports over AMQP.

The oops_amqp package provides an AMQP OOPS http://pypi.python.org/pypi/oops)
publisher, and a small daemon that listens on amqp for OOPS reports and
republishes them (into a supplied publisher). The OOPS framework permits
falling back to additional publishers if AMQP is down.

Usage
=====

Publishing to AMQP
++++++++++++++++++

Where you are creating OOPS reports, configure oops_amqp.Publisher. This takes
a connection factory - a simple callable that creates an amqp
connection - and the exchange name and routing key to submit to.

  >>> factory = partial(amqp.Connection, host="localhost:5672",
  ...     userid="guest", password="guest", virtual_host="/")
  >>> publisher = oops_amqp.Publisher(factory, "oopses", "")

Provide the publisher to your OOPS config::

  >>> config = oops.Config()
  >>> config.publisher = publisher

Any oops published via that config will now be sent via amqp.

OOPS ids are generating by hashing the oops message (without the id field) -
this ensures unique ids.

The reason a factory is used is because amqp is not threadsafe - the
publisher maintains a thread locals object to hold the factories and creates
connections when new threads are created(when they first generate an OOPS).

Dealing with downtime
---------------------

From time to time your AMQP server may be unavailable. If that happens then
the Publisher will not assign an oops id - it will return None to signal that
the publication failed. To prevent losing the OOPS its a good idea to have a
fallback publisher - either another AMQP publisher (to a different server) or
one that spools locally (where you can pick up the OOPSes via rsync or some
other mechanism. Using the oops standard helper publish_with_fallback will let
you wrap the fallback publisher so that it only gets invoked if the primary
method failed::

  >>> fallback_factory = partial(amqp.Connection, host="otherserver:5672",
  ...     userid="guest", password="guest", virtual_host="/")
  >>> fallback_publisher = oops_amqp.Publisher(fallback_factory, "oopses", "")
  >>> config.publisher = publish_with_fallback(publisher, fallback_publisher)

Receiving from AMQP
+++++++++++++++++++

There is a simple method that will run an infinite loop processing reports from
AMQP. To use it you need to configure a local config to publish the received
reports. A full config is used because that includes support for filtering
(which can be useful if you need to throttle volume, for instance).
Additionally you need an amqp connection factory (to handle the amqp server
being restarted) and a queue name to receive from.

This example uses the DateDirRepo publisher, telling it to accept whatever
id was assigned by the process publishing to AMQP::

  >>> publisher = oops_datedir_repo.DateDirRepo('.', inherit_id=True)
  >>> config = oops.Config()
  >>> config.publisher = publisher.publish
  >>> receiver = oops_amqp.Receiver(config, factory, "my queue")
  >>> receiver.run_forever()
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
__version__ = (0, 1, 0, 'final', 0)

__all__ = [
    'Publisher',
    'Receiver',
    ]

from oops_amqp.publisher import Publisher
from oops_amqp.receiver import Receiver
