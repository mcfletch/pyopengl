#! /usr/bin/env python3
"""Report every name that may be unbound where it is read.

The shape this exists for is an error path that fails while reporting::

    try:
        window = make_window()
    except Exception as err:
        log.warning('could not destroy %s: %s', window, err)

``window`` is bound by the line that raised, so the handler raises
``NameError`` -- and that second error replaces the first, which is how a GLUT
teardown came to leak the window and everything freeglut owned for it.  Nothing
in the suite enters such a handler, by definition, so nothing reports it.

mypy has an error code for it, ``possibly-undefined``, which is off by default
and needs none of the annotation work a full typecheck would.  What it does
need is to be the *only* code in the gate: the package's own source reports
around 240 findings under a whole run, overwhelmingly mypy failing to model the
dynamic dispatch layer, and `[tool.mypy]` in pyproject.toml says why that is
not a gate anybody could pass.  mypy has no "only this code" switch, and a list
of the codes to disable goes stale the next time mypy grows one -- so the run
is unrestricted and its output is filtered here.

Run it directly, or through ``tox -e possiblyundefined``::

    python src/check_possibly_undefined.py [paths...]
"""

from __future__ import annotations

import os
import subprocess
import sys

#: The error code this gate is about.  A line mypy tags with anything else is
#: not this gate's business and is dropped.
CODE = '[possibly-undefined]'

#: Read rather than followed: `--follow-imports=skip` keeps the run to the
#: files named, which is what makes it finish in a minute over 1,680 modules,
#: and this question is answered inside one function body at a time.
ARGUMENTS = [
    '--no-incremental',
    '--follow-imports=skip',
    '--ignore-missing-imports',
    '--enable-error-code',
    'possibly-undefined',
    '--no-error-summary',
    '--no-color-output',
]

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

#: What a bare run checks: the shipped package.  The suite and the generator
#: are not in it -- a `NameError` there is a failing test rather than a user's
#: program losing its window.
DEFAULT_PATHS = ['OpenGL']


def findings(paths):
    """The `possibly-undefined` lines mypy reports for `paths`."""
    completed = subprocess.run(
        [sys.executable, '-m', 'mypy'] + ARGUMENTS + list(paths),
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    lines = completed.stdout.splitlines()
    reported = [line for line in lines if line.endswith(CODE)]
    if not reported and completed.returncode not in (0, 1):
        # mypy could not run at all -- a missing interpreter, a bad argument.
        # Silence here would be a gate reporting green having checked nothing.
        raise SystemExit(
            'mypy exited %s and reported no findings:\n%s'
            % (completed.returncode, completed.stdout)
        )
    return reported


def main(argv=None):
    paths = list(argv if argv is not None else sys.argv[1:]) or DEFAULT_PATHS
    reported = findings(paths)
    for line in reported:
        print(line)
    if reported:
        print(
            '\n%d name(s) may be unbound where they are read.  Each is a '
            'branch that raises NameError instead of doing what it says, and '
            'the usual place for one is an error path nothing has entered.'
            % len(reported),
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
