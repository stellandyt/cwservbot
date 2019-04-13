#
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

"""The primary interface for clients creating OOPS reports.

Typical usage:

* Configure the library::

  >>> from oops import Config
  >>> config = Config()
  >>> def demo_publish(report):
  ...    return 'id 1'
  >>> config.publisher = demo_publish

  This allows aggregation of oops reports from different programs into one
  oops-tools install.

  >>> config.template['reporter'] = 'myprogram'

* Create a report::

  >>> report = config.create()

* And then send it off for storage::

  >>> config.publish(report)
  ['id 1']
  >>> report
  {'id': 'id 1', 'template': 'myprogram'}

* See the Config object pydoc for more information.

The OOPS report is a dictionary, and must be bson serializable. This permits
the inclusion of binary data in the report, and provides cross-language
compatibility.

A minimal report can be empty, but this is fairly useless and may even be
rejected by some repositories.

Some well known keys used by Launchpad in its OOPS reports::

* id: The name of this error report.
* type: The type of the exception that occurred.
* value: The value of the exception that occurred.
* time: The time at which the exception occurred.
* hostname: The hostname of the machine the oops was created on. (Set by default)
* branch_nick: The branch nickname.
* revno: The revision number of the branch.
* tb_text: A text version of the traceback.
* username: The user associated with the request.
* url: The URL for the failed request.
* req_vars: The request variables. This should be a dict of simple string ->
  string mappings. The strings and their values should be either unicode or
  url escaped ascii bytestrings. Older versions of the oops toolchain emitted
  this variable as a list of two-tuples e.g. (key, value). Code expecting to
  receive or process old reports should accept both dicts and tuples. Modern
  or new code can just expect a dict.
* branch_nick: A name for the branch of code that was running when the report
  was triggered.
* revno: The revision that the branch was at.
* reporter: Describes the program creating the report. For instance you might
  put the name of the program, or its website - as long as its distinct from
  other reporters being sent to a single analysis server. For dynamically
  scaled services with multiple instances, the reporter will usually be the
  same for a single set of identical instances.  e.g. all the instances in one
  Amazon EC2 availability zone might be given the same reporter. Differentiated
  backend services for the same front end site would usually get different
  reporters as well. (e.g. auth, cache, render, ...)
* topic: The subject or context for the report. With a command line tool you
  might put the subcommand here, with a web site you might put the template (as
  opposed to the url). This is used as a weak correlation hint: reports from the
  same topic are more likely to have the same cause than reports from different
  topics.
* timeline: A sequence of (start, stop, category, detail) tuples describing the
  events leading up to the OOPS. One way to populate this is the oops-timeline
  package. Consumers should not assume the length of the tuple to be fixed -
  additional fields may be added in future to the right hand side (e.g.
  backtraces).
"""


from __future__ import absolute_import, print_function

__all__ = [
    'Config',
    ]

__metaclass__ = type

from copy import deepcopy
import warnings

from oops.createhooks import default_hooks
from oops.publishers import (
    convert_result_to_list,
    publish_to_many,
    )


class Config:
    """The configuration for the OOPS system.

    :ivar on_create: A list of callables to call when making a new report. Each
        will be called in series with the new report and a creation context
        dict. The return value of the callbacks is ignored.
    :ivar filters: A list of callables to call when filtering a report. Each
        will be called in series with a report that is about to be published.
        If the filter returns true (that is not None, 0, '' or False), then
        the report will not be published, and the call to publish will return
        None to the user.
    :ivar publisher: A callable to call when publishing a report.
        It will be called in series with the report to publish. It is expected
        to return a list of ids. See the publish() method for more
        information.
    :ivar publishers: A list of callables to call when publishing a report.
        Each will be called in series with the report to publish. Their return
        value will be assigned to the reports 'id' key : if a publisher
        allocates a different id than a prior publisher, only the last
        publisher in the list will have its id present in the report at the
        end. See the publish() method for more information. This attribute
        is deprecated, Use the `publisher` attribute instead, and see
        `oops.publishers.publish_to_many` if you want to publish to multiple
        publishers.
    """

    def __init__(self):
        self.filters = []
        self.on_create = list(default_hooks)
        self.template = {}
        self.publisher = None
        self.publishers = []

    def create(self, context=None):
        """Create an OOPS.

        The current template is copied to make the new report, and the new
        report is then passed to all the on_create callbacks for population.

        If a callback raises an exception, that will propgate to the caller.

        :param context: A dict of information that the on_create callbacks can
            use in populating the report. For instance, the attach_exception 
            callback looks for an exc_info key in the context and uses that
            to add information to the report. If context is None, an empty dict
            is created and used with the callbacks.
        :return: A fresh OOPS.
        """
        if context is None:
            context = {}
        result = deepcopy(self.template)
        [callback(result, context) for callback in self.on_create]
        return result

    def publish(self, report):
        """Publish a report.

        The report will be passed through any filters, and then handed
        off to the callable assigned to the `publisher` instance variable,
        if any, and then passed through any publishers in the `publishers`
        list instance variable. The return value will be the list returned
        by `publisher` method, with the ids returned by the `publishers`
        appended. The `publishers` list is deprecated, and the `publisher`
        attribute should be used instead, with
        `oops.publishers.publish_to_many` used if needed.

        The `publisher` should return a list of ids that were
        allocated-or-used for the report. The `publishers` should each return
        any id that was allocated-or-used for the report. The return value of
        the callables in the `publishers` list will be assigned to the `id`
        key of the report. If a publisher in the `publishers` list returns
        anything non-True (that is None, 0, False, ''), it indicates that the
        publisher did not publish the report.

        The last entry in the list of ids, if any, will be assigned to the 'id'
        key of the report before returning, so that clients that only care to
        deal with one id don't have to pick one themselves.

        The whole list of ids will be returned to the caller to allow them
        to handle the case where multiple ids were used for a report.

        If any publisher raises an exception, that will propagate to the caller.

        :return: A list of the allocated ids.
        """
        for report_filter in self.filters:
            if report_filter(report):
                return None
        # XXX: james_w 2012-06-19 bug=1015293: Deprecated code path,
        #       this should be removed once users have had a chance
        #       to migrate. The constructor and docstrings should
        #       also be cleaned up at the same time.
        if self.publishers:
            warnings.warn(
                "Using the oops.Config.publishers attribute is "
                "deprecated. Use the oops.Config.publisher attribute "
                "instead, with an oops.publishers.publish_to_many object "
                "if multiple publishers are needed",
                DeprecationWarning, stacklevel=2)
        old_publishers = map(convert_result_to_list, self.publishers)
        if self.publisher:
            publisher = publish_to_many(self.publisher, *old_publishers)
        else:
            publisher = publish_to_many(*old_publishers)
        ret = publisher(report)
        if ret:
            report['id'] = ret[-1]
        return ret
