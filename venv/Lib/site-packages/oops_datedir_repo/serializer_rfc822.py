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

"""Read / Write an OOPS dict as an rfc822 formatted message.

This style of OOPS format is very web server specific, not extensible - it
should be considered deprecated.

The reports this serializer handles always have the following variables (See
the python-oops api docs for more information about these variables):

* id: The name of this error report.
* type: The type of the exception that occurred.
* value: The value of the exception that occurred.
* time: The time at which the exception occurred.
* reporter: The reporting program.
* topic: The identifier for the template/script that oopsed.
  [this is written as Page-Id for compatibility with as yet unported tools.]
* branch_nick: The branch nickname.
* revno: The revision number of the branch.
* tb_text: A text version of the traceback.
* username: The user associated with the request.
* url: The URL for the failed request.
* req_vars: The request variables. Either a list of 2-tuples or a dict.
* branch_nick: A name for the branch of code that was running when the report
  was triggered.
* revno: The revision that the branch was at.
* Informational: A flag, True if the error wasn't fatal- if it was
  'informational'.
  [Deprecated - this is no longer part of the oops report conventions. Existing
   reports with it set are still read, but the key is only present if it was
   truely in the report.]
"""


from __future__ import absolute_import, print_function

__all__ = [
    'read',
    'write',
    ]

__metaclass__ = type

try:
    from email.parser import BytesParser
except ImportError:
    # On Python 2, email.parser.Parser will do well enough, since
    # bytes == str.
    from email.parser import Parser as BytesParser
import logging
import re
import urllib

import iso8601
import six
from six.moves import intern
from six.moves.urllib_parse import (
    quote,
    unquote,
    )


def read(fp):
    """Deserialize an OOPS from an RFC822 format message."""
    msg = BytesParser().parse(fp, headersonly=True)
    id = msg.get('oops-id')
    exc_type = msg.get('exception-type')
    exc_value = msg.get('exception-value')
    datestr = msg.get('date')
    if datestr is not None:
        date = iso8601.parse_date(msg.get('date'))
    else:
        date = None
    topic = msg.get('topic')
    if topic is None:
        topic = msg.get('page-id')
    username = msg.get('user')
    url = msg.get('url')
    try:
        duration = float(msg.get('duration', '-1'))
    except ValueError:
        duration = float(-1)
    informational = msg.get('informational')
    branch_nick = msg.get('branch')
    revno = msg.get('revision')
    reporter = msg.get('oops-reporter')

    # Explicitly use an iterator so we can process the file sequentially.
    lines = iter(msg.get_payload().splitlines(True))

    statement_pat = re.compile(r'^(\d+)-(\d+)(?:@([\w-]+))?\s+(.*)')

    def is_req_var(line):
        return "=" in line and not statement_pat.match(line)

    def is_traceback(line):
        return line.lower().startswith('traceback') or line.startswith(
            '== EXTRA DATA ==')

    req_vars = []
    statements = []
    first_tb_line = ''
    for line in lines:
        first_tb_line = line
        line = line.strip()
        if line == '':
            continue
        else:
            match = statement_pat.match(line)
            if match is not None:
                start, end, db_id, statement = match.groups()
                if db_id is not None:
                    db_id = intern(db_id)  # This string is repeated lots.
                statements.append(
                    [int(start), int(end), db_id, statement])
            elif is_req_var(line):
                key, value = line.split('=', 1)
                req_vars.append([unquote(key), unquote(value)])
            elif is_traceback(line):
                break
    req_vars = dict(req_vars)

    # The rest is traceback.
    tb_text = ''.join([first_tb_line] + list(lines))

    result = dict(id=id, type=exc_type, value=exc_value, time=date,
            topic=topic, tb_text=tb_text, username=username, url=url,
            duration=duration, req_vars=req_vars, timeline=statements,
            branch_nick=branch_nick, revno=revno)
    if informational is not None:
        result['informational'] = informational
    if reporter is not None:
        result['reporter'] = reporter
    return result


def _normalise_whitespace(s):
    """Normalise the whitespace in a bytestring to spaces."""
    if s is None:
        return None # (used by the cast to %s to get 'None')
    return b' '.join(s.split())


def _safestr(obj):
    if isinstance(obj, six.text_type):
        return obj.replace('\\', '\\\\').encode('ASCII',
                                                'backslashreplace')
    # A call to str(obj) could raise anything at all.
    # We'll ignore these errors, and print something
    # useful instead, but also log the error.
    # We disable the pylint warning for the blank except.
    if isinstance(obj, six.binary_type):
        value = obj
    else:
        try:
            value = str(obj)
        except:
            logging.getLogger('oops_datedir_repo.serializer_rfc822').exception(
                'Error while getting a str '
                'representation of an object')
            value = '<unprintable %s object>' % (
                str(type(obj).__name__))
        # Some str() calls return unicode objects.
        if isinstance(value, six.text_type):
            return _safestr(value)
    # encode non-ASCII characters
    value = value.replace(b'\\', b'\\\\')
    value = re.sub(
        br'[\x80-\xff]',
        lambda match: ('\\x%02x' % ord(match.group(0))).encode('UTF-8'), value)
    return value


def to_chunks(report):
    """Returns a list of bytestrings making up the serialized oops."""
    chunks = []
    def header(label, key, optional=True):
        if optional and key not in report:
            return
        value = _safestr(report[key])
        value = _normalise_whitespace(value)
        chunks.append(label.encode('UTF-8') + b': ' + value + b'\n')
    header('Oops-Id', 'id', optional=False)
    header('Exception-Type', 'type')
    header('Exception-Value', 'value')
    if 'time' in report:
        chunks.append(
            ('Date: %s\n' % report['time'].isoformat()).encode('UTF-8'))
    header('Page-Id', 'topic')
    header('Branch', 'branch_nick')
    header('Revision', 'revno')
    header('User', 'username')
    header('URL', 'url')
    header('Duration', 'duration')
    header('Informational', 'informational')
    header('Oops-Reporter', 'reporter')
    chunks.append(b'\n')
    safe_chars = ';/\\?:@&+$, ()*!'
    if 'req_vars' in report:
        try:
            items = sorted(report['req_vars'].items())
        except AttributeError:
            items = report['req_vars']
        for key, value in items:
            chunk = '%s=%s\n' % (
                quote(_safestr(key), safe_chars),
                quote(_safestr(value), safe_chars))
            chunks.append(chunk.encode('UTF-8'))
        chunks.append(b'\n')
    if 'timeline' in report:
        for row in report['timeline']:
            (start, end, category, statement) = row[:4]
            chunks.append(
                ('%05d-%05d@' % (start, end)).encode('UTF-8') +
                _safestr(category) + b' ' +
                _normalise_whitespace(_safestr(statement)) + b'\n')
        chunks.append(b'\n')
    if 'tb_text' in report:
        chunks.append(_safestr(report['tb_text']))
    return chunks


def write(report, output):
    """Write a report to a file."""
    output.writelines(to_chunks(report))
