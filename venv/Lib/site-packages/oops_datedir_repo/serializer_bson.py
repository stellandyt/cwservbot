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

"""Read / Write an OOPS dict as a bson dict.

This style of OOPS format is very extensible and maintains compatability with
older rfc822 oops code: the previously mandatory keys are populated on read.

Use of bson serializing is recommended.

The reports this serializer handles always have the following variables (See
the python-oops api docs for more information about these variables):

* id: The name of this error report.
* type: The type of the exception that occurred.
* value: The value of the exception that occurred.
* time: The time at which the exception occurred.
* reporter: The reporting program.
* topic: The identifier for the template/script that oopsed.
* branch_nick: The branch nickname.
* revno: The revision number of the branch.
* tb_text: A text version of the traceback.
* username: The user associated with the request.
* url: The URL for the failed request.
* req_vars: The request variables. Either a list of 2-tuples or a dict.
* branch_nick: A name for the branch of code that was running when the report
  was triggered.
* revno: The revision that the branch was at.
"""


from __future__ import absolute_import, print_function

__all__ = [
    'dumps',
    'read',
    'write',
    ]

__metaclass__ = type

from oops_datedir_repo import anybson as bson


def read(fp):
    """Deserialize an OOPS from a bson message."""
    report = bson.loads(fp.read())
    for key in (
            'branch_nick', 'revno', 'type', 'value', 'time', 'topic',
            'username', 'url'):
        report.setdefault(key, None)
    report.setdefault('duration', -1)
    report.setdefault('req_vars', {})
    report.setdefault('tb_text', '')
    report.setdefault('timeline', [])
    return report


def dumps(report):
    """Return a binary string representing report."""
    return bson.dumps(report)


def write(report, fp):
    """Write report to fp."""
    return fp.write(dumps(report))
