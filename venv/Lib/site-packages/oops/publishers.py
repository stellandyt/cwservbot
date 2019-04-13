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

"""Generic publisher support and utility code."""

from __future__ import absolute_import, print_function

__metaclass__ = type

__all__ = [
    'pprint_to_stream',
    'publish_with_fallback',
    'publish_to_many',
    ]

from hashlib import md5
from pprint import pformat


def pprint_to_stream(stream):
    """Pretty print reports to text stream.
    
    Reports will be given an id by hashing the report if none is present.
    """
    def pprinter(report):
        report = dict(report)
        output = pformat(report)
        if not report.get('id'):
            report['id'] = md5(output.encode('UTF-8')).hexdigest()
            output = pformat(report)
        stream.write(output)
        stream.write('\n')
        stream.flush()
        return [report['id']]
    return pprinter


def publish_new_only(publisher):
    """Wraps a publisher with a check that the report has not had an id set.

    This permits having fallback publishers that only publish if the earlier
    one failed.

    For instance:

      >>> config.publishers.append(amqp_publisher)
      >>> config.publishers.append(publish_new_only(datedir_repo.publish))

    This function is deprecated. Instead please use publish_with_fallback.
    """
    def result(report):
        if report.get('id'):
            return None
        return publisher(report)
    return result


def publish_with_fallback(*publishers):
    """A publisher to fallback publishing through a list of publishers

    This is a publisher, see Config.publish for the calling and return
    conventions. This publisher delegates to the supplied publishers
    by calling them all until one reports that it has published the
    report, and aggregates the results.

    :param *publishers: a list of callables to publish oopses to.
    :return: a callable that will publish a report to each
        of the publishers when called.
    """
    def result(report):
        ret = []
        for publisher in publishers:
            ret.extend(publisher(report))
            if ret:
                break
        return ret
    return result


def publish_to_many(*publishers):
    """A fan-out publisher of oops reports.

    This is a publisher, see Config.publish for the calling and return
    conventions. This publisher delegates to the supplied publishers
    by calling them all, and aggregates the results.

    If a publisher returns a non-emtpy list (indicating that the report was
    published) then the last item of this list will be set as the 'id' key
    in the report before the report is passed to the next publisher. This
    makes it possible for publishers later in the chain to re-use the id.

    :param *publishers: a list of callables to publish oopses to.
    :return: a callable that will publish a report to each
        of the publishers when called.
    """
    def result(report):
        ret = []
        for publisher in publishers:
            if ret:
                report['id'] = ret[-1]
            ret.extend(publisher(report))
        return ret
    return result


def convert_result_to_list(publisher):
    """Ensure that a publisher returns a list.

    The old protocol for publisher callables was to return an id, or
    a False value if the report was not published. The new protocol
    is to return a list, which is empty if the report was not
    published.

    This function coverts a publisher using the old protocol in to one that
    uses the  new protocol, translating values as needed.
    """
    def publish(report):
        ret = publisher(report)
        if ret:
            return [ret]
        else:
            return []
    return publish
