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

"""Print a BSON document for easier human inspection.

This can be used for oopses, which are commonly (though not necessarily)
stored as BSON.

usage: bsondump FILE
"""

from __future__ import absolute_import, print_function

from pprint import pprint
import sys

from oops_datedir_repo import anybson as bson


def main(argv=None):
    if argv is None:
        argv = sys.argv
    if len(argv) != 2:
        print __doc__
        sys.exit(1)
    # I'd like to use json here, but not everything serializable in bson is
    # easily representable in json - even before getting in to the weird parts,
    # oopses commonly have datetime objects. -- mbp 2011-12-20
    pprint(bson.loads(file(argv[1]).read()))
