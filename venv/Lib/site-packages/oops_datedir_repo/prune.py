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

"""Delete OOPSes that are not referenced in the bugtracker.

Currently only has support for the Launchpad bug tracker.
"""

from __future__ import absolute_import, print_function

__metaclass__ = type

import datetime
import logging
import optparse
from textwrap import dedent
import sys

from launchpadlib.launchpad import Launchpad
from launchpadlib.uris import lookup_service_root
from pytz import utc

import oops_datedir_repo

__all__ = [
    'main',
    ]


class LaunchpadTracker:
    """Abstracted bug tracker/forums etc - permits testing of main()."""

    def __init__(self, options):
        self.lp = Launchpad.login_anonymously(
            'oops-prune', options.lpinstance, version='devel')

    def find_oops_references(self, start_time, end_time, project=None,
        projectgroup=None):
        """Find oops references from start_time to end_time.

        :param project: Either None or a project name, or a list of projects.
        :param projectgroup: Either None or a project group name or a list
            of project group names.
        """
        projects = set([])
        if project is not None:
            if type(project) is not list:
                project = [project]
            projects.update(project)
        if projectgroup is not None:
            if type(projectgroup) is not list:
                projectgroup = [projectgroup]
            for group in projectgroup:
                [projects.add(lp_proj.name)
                    for lp_proj in self.lp.project_groups[group].projects]
        result = set()
        lp_projects = self.lp.projects
        one_week = datetime.timedelta(weeks=1)
        for project in projects:
            lp_project = lp_projects[project]
            current_start = start_time
            while current_start < end_time:
                current_end = current_start + one_week
                if current_end > end_time:
                    current_end = end_time
                logging.info(
                    "Querying OOPS references on %s from %s to %s", 
                    project, current_start, current_end)
                result.update(lp_project.findReferencedOOPS(
                    start_date=current_start, end_date=current_end))
                current_start = current_end
        return result


def main(argv=None, tracker=LaunchpadTracker, logging=logging):
    """Console script entry point."""
    if argv is None:
        argv = sys.argv
    usage = dedent("""\
        %prog [options]

        The following options must be supplied:
         --repo

         And at least one of either
         --project
         or
         --projectgroup

        e.g.
        %prog --repo . --projectgroup launchpad-project

        Will process every member project of launchpad-project.

        --project and --projectgroup can be supplied multiple times.

        When run this program will ask Launchpad for OOPS references made since
        the last date it pruned up to, with an upper limit of one week from
        today. It then looks in the repository for all oopses created during
        that date range, and if they are not in the set returned by Launchpad,
        deletes them. If the repository has never been pruned before, it will
        pick the earliest datedir present in the repository as the start date.
        """)
    description = \
        "Delete OOPS reports that are not referenced in a bug tracker."
    parser = optparse.OptionParser(
        description=description, usage=usage)
    parser.add_option('--project', action="append",
        help="Launchpad project to find references in.")
    parser.add_option('--projectgroup', action="append",
        help="Launchpad project group to find references in.")
    parser.add_option('--repo', help="Path to the repository to read from.")
    parser.add_option(
        '--lpinstance', help="Launchpad instance to use", default="production")
    options, args = parser.parse_args(argv[1:])
    def needed(*optnames):
        present = set()
        for optname in optnames:
            if getattr(options, optname, None) is not None:
                present.add(optname)
        if not present:
            if len(optnames) == 1:
                raise ValueError('Option "%s" must be supplied' % optname)
            else:
                raise ValueError(
                    'One of options %s must be supplied' % (optnames,))
    needed('repo')
    needed('project', 'projectgroup')
    logging.basicConfig(
        filename='prune.log', filemode='w', level=logging.DEBUG)
    repo = oops_datedir_repo.DateDirRepo(options.repo)
    one_week = datetime.timedelta(weeks=1)
    one_day = datetime.timedelta(days=1)
    # Only prune OOPS reports more than one week old.
    prune_until = datetime.datetime.now(utc) - one_week
    # Ignore OOPS reports we already found references for - older than the last
    # prune date.
    try:
        prune_from = repo.get_config('pruned-until')
    except KeyError:
        try:
            oldest_oops = repo.oldest_date()
        except ValueError:
            logging.info("No OOPSes in repo, nothing to do.")
            return 0
        midnight_utc = datetime.time(tzinfo=utc)
        prune_from = datetime.datetime.combine(oldest_oops, midnight_utc)
    # The tracker finds all the references for the selected dates.
    finder = tracker(options)
    references = finder.find_oops_references(
        prune_from, datetime.datetime.now(utc), options.project,
        options.projectgroup)
    # Then we can delete the unreferenced oopses.
    repo.prune_unreferenced(prune_from, prune_until, references)
    # And finally save the fact we have scanned up to the selected date.
    repo.set_config('pruned-until', prune_until)
    return 0
