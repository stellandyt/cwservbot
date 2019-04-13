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

from __future__ import absolute_import, print_function

__all__ = [
    'dumps',
    'loads',
    ]


try:
    from bson import dumps, loads

    # Create the exception that won't be raised by this version of
    # bson
    class InvalidBSON(Exception):
        pass
except ImportError:
    from bson import BSON, InvalidBSON

    def dumps(obj):
        return BSON.encode(obj)

    def loads(data):
        return BSON(data).decode(tz_aware=True)
