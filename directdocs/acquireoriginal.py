#! /usr/bin/env python3
"""Fetches the Khronos reference-page sources the manual is generated from.

The pages are DocBook in a repository of their own.  They land in
``directdocs/OpenGL-Refpages``, which is not in version control: it is somebody
else's repository, and a copy of it checked in here would be a snapshot going
stale in the diff.

``build-docs.py`` calls this before generating, so a checkout needs no separate
step; running it directly updates the sources without building anything.
"""

from __future__ import annotations

import argparse
import logging
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

log = logging.getLogger('acquireoriginal')

#: Where the DocBook sources come from and what they are checked out as.
MAN_SOURCES = [
    ('https://github.com/KhronosGroup/OpenGL-Refpages', 'OpenGL-Refpages'),
]

#: The history is of no use here and the checkout is large, so only the tip is
#: fetched.  A shallow checkout still updates with ``git pull``.
CLONE_ARGS = ['--depth', '1']


def ensure_sources(directory: str = HERE, update: bool = True) -> list[str]:
    """Make sure the sources are present, and return where each one is."""
    paths = []
    for source, name in MAN_SOURCES:
        target = os.path.join(directory, name)
        if not os.path.exists(target):
            log.info('cloning %s into %s', source, target)
            subprocess.check_call(['git', 'clone'] + CLONE_ARGS + [source, target])
        elif update:
            log.info('updating %s', target)
            subprocess.check_call(
                ['git', 'pull', '--ff-only', '--depth', '1'], cwd=target
            )
        paths.append(target)
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument(
        '--no-update',
        action='store_true',
        help='leave an existing checkout as it is rather than pulling',
    )
    options = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO)
    for path in ensure_sources(update=not options.no_update):
        print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
