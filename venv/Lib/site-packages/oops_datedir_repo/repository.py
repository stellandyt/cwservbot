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

"""The primary interface to oopses stored on disk - the DateDirRepo."""

from __future__ import absolute_import, print_function

__metaclass__ = type

__all__ = [
    'DateDirRepo',
    ]

import datetime
import errno
from functools  import partial
from hashlib import md5
import os.path
import stat

from pytz import utc

from oops_datedir_repo import (
    anybson as bson,
    serializer,
    serializer_bson,
    )


class DateDirRepo:
    """Publish oopses to a date-dir repository.

    A date-dir repository is a directory containing:

    * Zero or one directories called 'metadata'. If it exists this directory
      contains any housekeeping material needed (such as a metadata.conf ini
      file).

    * Zero or more directories named like YYYY-MM-DD, which contain zero or
      more OOPS reports. OOPS file names can take various forms, but must not
      end in .tmp - those are considered to be OOPS reports that are currently
      being written.

    * The behaviour of this class is to assign OOPS file names by hashing the
      serialized OOPS to get a unique file name. Other naming schemes are
      valid - the code doesn't assume anything other than the .tmp limitation
      above.
    """

    def __init__(self, error_dir, serializer=None, inherit_id=False,
        stash_path=False):
        """Create a DateDirRepo.

        :param error_dir: The base directory to write OOPSes into. OOPSes are
            written into a subdirectory this named after the date (e.g.
            2011-12-30).
        :param serializer: If supplied should be the module (e.g.
            oops_datedir_repo.serializer_rfc822) to use to serialize OOPSes.
            Defaults to using serializer_bson.
        :param inherit_id: If True, use the oops ID (if present) supplied in
            the report, rather than always assigning a new one.
        :param stash_path: If True, the filename that the OOPS was written to
            is stored in the OOPS report under the key 'datedir_repo_filepath'.
            It is not stored in the OOPS written to disk, only the in-memory
            model.
        """
        self.root = error_dir
        if serializer is None:
            serializer = serializer_bson
        self.serializer = serializer
        self.inherit_id = inherit_id
        self.stash_path = stash_path
        self.metadatadir = os.path.join(self.root, 'metadata')
        self.config_path = os.path.join(self.metadatadir, 'config.bson')

    def publish(self, report, now=None):
        """Write the report to disk.

        The report is written to a temporary file, and then renamed to its
        final location. Programs concurrently reading from a DateDirRepo
        should ignore files ending in .tmp.

        :param now: The datetime to use as the current time.  Will be
            determined if not supplied.  Useful for testing.
        """
        # We set file permission to: rw-r--r-- (so that reports from
        # umask-restricted services can be gathered by a tool running as
        # another user).
        wanted_file_permission = (
            stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
        if now is not None:
            now = now.astimezone(utc)
        else:
            now = datetime.datetime.now(utc)
        # Don't mess with the original report when changing ids etc.
        original_report = report
        report = dict(report)
        md5hash = md5(serializer_bson.dumps(report)).hexdigest()
        oopsid = 'OOPS-%s' % md5hash
        prefix = os.path.join(self.root, now.strftime('%Y-%m-%d'))
        if not os.path.isdir(prefix):
            try:
                os.makedirs(prefix)
            except OSError as err:
                # EEXIST - dir created by another, concurrent process
                if err.errno != errno.EEXIST:
                    raise
            # For directories we need to set the x bits too.
            os.chmod(
                prefix, wanted_file_permission | stat.S_IXUSR | stat.S_IXGRP |
                stat.S_IXOTH)
        filename = os.path.join(prefix, oopsid)
        if self.inherit_id:
            oopsid = report.get('id') or oopsid
        report['id'] = oopsid
        with open(filename + '.tmp', 'wb') as f:
            self.serializer.write(report, f)
        os.rename(filename + '.tmp', filename)
        if self.stash_path:
            original_report['datedir_repo_filepath'] = filename
        os.chmod(filename, wanted_file_permission)
        return [report['id']]

    def republish(self, publisher):
        """Republish the contents of the DateDirRepo to another publisher.

        This makes it easy to treat a DateDirRepo as a backing store in message
        queue environments: if the message queue is down, flush to the
        DateDirRepo, then later pick the OOPSes up and send them to the message
        queue environment.

        For instance:

          >>> repo = DateDirRepo('.')
          >>> repo.publish({'some':'report'})
          >>> queue = []
          >>> def queue_publisher(report):
          ...     queue.append(report)
          ...     return report['id']
          >>> repo.republish(queue_publisher)

        Will scan the disk and send the single found report to queue_publisher,
        deleting the report afterwards.

        Empty datedir directories are automatically cleaned up, as are stale
        .tmp files.

        If the publisher returns None, signalling that it did not publish the
        report, then the report is not deleted from disk.
        """
        two_days = datetime.timedelta(2)
        now = datetime.date.today()
        old = now - two_days
        for dirname, (y,m,d) in self._datedirs():
            date = datetime.date(y, m, d)
            prune = date < old
            dirpath = os.path.join(self.root, dirname)
            files = os.listdir(dirpath)
            if not files and prune:
                # Cleanup no longer needed directory.
                os.rmdir(dirpath)
            for candidate in map(partial(os.path.join, dirpath), files):
                if candidate.endswith('.tmp'):
                    if prune:
                        os.unlink(candidate)
                    continue
                with open(candidate, 'rb') as report_file:
                    try:
                        report = serializer.read(report_file)
                    except IOError as e:
                        if e.args[0] == 'Empty OOPS Report':
                            report = None
                        else:
                            raise
                if report is not None:
                    oopsid = publisher(report)
                if (report is None and prune) or (report is not None and oopsid):
                    os.unlink(candidate)

    def _datedirs(self):
        """Yield each subdir which looks like a datedir."""
        for dirname in os.listdir(self.root):
            try:
                y, m, d = dirname.split('-')
                y = int(y)
                m = int(m)
                d = int(d)
            except ValueError:
                # Not a datedir
                continue
            yield dirname, (y, m, d)

    def _read_config(self):
        """Return the current config document from disk."""
        try:
            with open(self.config_path, 'rb') as config_file:
                return bson.loads(config_file.read())
        except IOError as e:
            if e.errno != errno.ENOENT:
                raise
            return {}

    def get_config(self, key):
        """Return a key from the repository config.

        :param key: A key to read from the config.
        """
        return self._read_config()[key]

    def set_config(self, key, value):
        """Set config option key to value.

        This is written to the bson document root/metadata/config.bson

        :param key: The key to set - anything that can be a key in a bson
            document.
        :param value: The value to set - anything that can be a value in a
            bson document.
        """
        config = self._read_config()
        config[key] = value
        try:
            with open(self.config_path + '.tmp', 'wb') as config_file:
                config_file.write(bson.dumps(config))
        except IOError as e:
            if e.errno != errno.ENOENT:
                raise
            os.mkdir(self.metadatadir)
            with open(self.config_path + '.tmp', 'wb') as config_file:
                config_file.write(bson.dumps(config))
        os.rename(self.config_path + '.tmp', self.config_path)

    def oldest_date(self):
        """Return the date of the oldest datedir in the repository.

        If pruning / resubmission is working this should also be the date of
        the oldest oops in the repository.
        """
        dirs = list(self._datedirs())
        if not dirs:
            raise ValueError("No OOPSes in repository.")
        return datetime.date(*sorted(dirs)[0][1])

    def prune_unreferenced(self, start_time, stop_time, references):
        """Delete OOPS reports filed between start_time and stop_time.

        A report is deleted if all of the following are true:

        * it is in a datedir covered by [start_time, stop_time] inclusive of
          the end points.

        * It is not in the set references.

        * Its timestamp falls between start_time and stop_time inclusively or
          it's timestamp is outside the datedir it is in or there is no
          timestamp on the report.

        :param start_time: The lower bound to prune within.
        :param stop_time: The upper bound to prune within.
        :param references: An iterable of OOPS ids to keep.
        """
        start_date = start_time.date()
        stop_date = stop_time.date()
        midnight = datetime.time(tzinfo=utc)
        for dirname, (y,m,d) in self._datedirs():
            dirdate = datetime.date(y, m, d)
            if dirdate < start_date or dirdate > stop_date:
                continue
            dirpath = os.path.join(self.root, dirname)
            files = os.listdir(dirpath)
            deleted = 0
            for candidate in map(partial(os.path.join, dirpath), files):
                if candidate.endswith('.tmp'):
                    # Old half-written oops: just remove.
                    os.unlink(candidate)
                    deleted += 1
                    continue
                with open(candidate, 'rb') as report_file:
                    report = serializer.read(report_file)
                    report_time = report.get('time', None)
                    if (report_time is None or
                        getattr(report_time, 'date', None) is None or
                        report_time.date() < dirdate or
                        report_time.date() > dirdate):
                        # The report is oddly filed or missing a precise
                        # datestamp. Treat it like midnight on the day of the
                        # directory it was placed in - this is a lower bound on
                        # when it was actually created.
                        report_time = datetime.datetime.combine(
                            dirdate, midnight)
                    if (report_time >= start_time and
                        report_time <= stop_time and
                        report['id'] not in references):
                        # Unreferenced and prunable
                        os.unlink(candidate)
                        deleted += 1
            if deleted == len(files):
                # Everything in the directory was deleted.
                os.rmdir(dirpath)
