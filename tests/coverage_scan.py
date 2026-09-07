#! /usr/bin/env python3
"""What a suite calls, read out of its source.

The three coverage reports -- ``gl/gl_coverage.py``, ``gles/es_coverage.py``,
``glu/glu_coverage.py`` -- enumerate their command universes very differently,
because the three APIs record theirs differently.  What they have in common is
this: scan the suite's own files for the entry points they name, and treat that
as what is covered.

They each grew their own version of it, and the three diverged.  One scanned
``test_*.py``, one ``test_es*.py`` *and* ``test_ext*.py``, one
``test_glu_*.py`` -- so a file whose name did not match the pattern was
silently absent from the report, and the number came out flattering rather than
wrong.  ``tests/gles/test_array_int64.py`` was one such file.

One scanner, and it takes every ``.py`` in the directory, so a new file counts
by existing.
"""

import glob
import os
import re


def called(directory, prefix, extra=()):
    """Every ``<prefix>*`` name mentioned in the ``.py`` files in `directory`.

    `extra` names further files -- the shared framework a suite calls through,
    which lives above it and would otherwise read as uncovered.

    Every file rather than a pattern: what is wanted is what the suite calls,
    and a suite is what is in its directory.  A helper module is as much a
    caller as a test is, which is why the old patterns had to list the base
    case by hand.
    """
    pattern = re.compile(r'\b(%s[A-Z][A-Za-z0-9_]*)\b' % (re.escape(prefix),))
    used = set()
    paths = sorted(glob.glob(os.path.join(directory, '*.py')))
    paths += [path for path in extra if os.path.exists(path)]
    for path in paths:
        if os.path.basename(path).endswith('_coverage.py'):
            continue        # the report is not a caller
        with open(path, encoding='utf-8') as handle:
            used.update(pattern.findall(handle.read()))
    return used
