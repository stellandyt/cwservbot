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

"""Read from any known serializer.

Where possible using the specific known serializer is better as it is more
efficient and won't suffer false positives if two serializations happen to pun
with each other (unlikely though that is).

Typical usage:
    >>> fp = file('an-oops', 'rb')
    >>> report = serializer.read(fp)

See the serializer_rfc822 and serializer_bson modules for information about
serializing OOPS reports by hand. Generally just using the DateDirRepo.publish
method is all that is needed.
"""


from __future__ import absolute_import, print_function

__all__ = [
    'read',
    ]

import bz2
from io import BytesIO

from oops_datedir_repo import (
    anybson as bson,
    serializer_bson,
    serializer_rfc822,
    )


def read(fp):
    """Deserialize an OOPS from a bson or rfc822 message.

    The whole file is read regardless of the OOPS format.  It should be
    opened in binary mode.

    :raises IOError: If the file has no content.
    """
    # Deal with no-rewindable file pointers.
    content = fp.read()
    if len(content) == 0:
        # This OOPS has no content
        raise IOError("Empty OOPS Report")
    if content[0:3] == b"BZh":
        content = bz2.decompress(content)
    try:
        return serializer_bson.read(BytesIO(content))
    except (KeyError, ValueError, IndexError, bson.InvalidBSON):
        return serializer_rfc822.read(BytesIO(content))
