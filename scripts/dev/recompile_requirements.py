#!/usr/bin/env python3
# vim: ft=python fileencoding=utf-8 sts=4 sw=4 et:

# Copyright 2016 Florian Bruhin (The Compiler) <mail@qutebrowser.org>
#
# This file is part of qutebrowser.
#
# qutebrowser is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# qutebrowser is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with qutebrowser.  If not, see <http://www.gnu.org/licenses/>.

"""Script to regenerate requirements files in misc/requirements."""

import re
import sys
import os.path
import glob
import subprocess
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir,
                                os.pardir))

from scripts import utils

REQ_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       '..', '..',  # /scripts/dev -> /scripts -> /
                       'misc', 'requirements')


def convert_line(line, comments):
    replacements = {
        (r'@.*#', '#'),  # remove @commit-id for scm installs
        (r'qute-pylint==.*', './scripts/dev/pylint_checkers'),
    }
    for pattern, repl in replacements:
        line = re.sub(pattern, repl, line)

    pkgname = line.split('=')[0]
    ignored = comments.get('ignore', '').split(',')

    if pkgname in ignored:
        return None

    if pkgname in comments:
        line += '  # ' + comments[pkgname]

    return line


def read_comments(fobj):
    comments = {}
    for line in fobj:
        if line.startswith('#') and ':' in line:
            pkg, comment = line.split(':', maxsplit=1)
            pkg = pkg.lstrip('# ')
            comment = comment.strip()
            comments[pkg] = comment
    return comments


def get_all_names():
    for filename in glob.glob(os.path.join(REQ_DIR, 'requirements-*-raw.txt')):
        basename = os.path.basename(filename)
        yield basename[len('requirements-'):-len('-raw.txt')]


def main():
    names = sys.argv[1:] if len(sys.argv) > 1 else get_all_names()

    for name in names:
        utils.print_title(name)
        filename = os.path.join(REQ_DIR,
                                'requirements-{}-raw.txt'.format(name))
        outfile = os.path.join(REQ_DIR, 'requirements-{}.txt'.format(name))

        with tempfile.TemporaryDirectory() as tmpdir:
            pip_bin = os.path.join(tmpdir, 'bin', 'pip')
            subprocess.check_call(['virtualenv', tmpdir])
            subprocess.check_call([pip_bin, 'install', '-r', filename])
            reqs = subprocess.check_output([pip_bin, 'freeze']).decode('utf-8')

        with open(filename, 'r', encoding='utf-8') as f:
            comments = read_comments(f)

        with open(outfile, 'w', encoding='utf-8') as f:
            f.write("# This file is automatically generated by "
                    "scripts/dev/recompile_requirements.py\n\n")
            for line in reqs.splitlines():
                converted = convert_line(line, comments)
                if converted is not None:
                    f.write(converted + '\n')


if __name__ == '__main__':
    main()
