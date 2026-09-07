#! /usr/bin/env python3
"""Measure GLU entry-point test coverage for this checkout.

Enumerates the public ``glu*`` callables exported by ``OpenGL.GLU``, scans the
``test_glu_*.py`` tests (plus the shared base class) for the commands they call,
and reports coverage.  Run directly for a summary; ``--uncovered`` lists any
entry points no test touches.
"""

import os
import re
import sys
import coverage_scan

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))  # repo root holding ``OpenGL``
sys.path.insert(0, ROOT)

_CALL = re.compile(r'\b(glu[A-Z][A-Za-z0-9_]*)\b')


def defined_funcs():
    """All public ``glu*`` callables exported from OpenGL.GLU."""
    from OpenGL import GLU

    return {
        name
        for name in dir(GLU)
        if name.startswith('glu') and callable(getattr(GLU, name))
    }


def called_funcs():
    """Commands the suite names, including through the shared base class."""
    return coverage_scan.called(HERE, 'glu')


def main():
    defined = defined_funcs()
    used = called_funcs()
    covered = defined & used
    pct = 100.0 * len(covered) / len(defined) if defined else 0.0
    print('GLU entry points: %d covered / %d total  (%.1f%%)'
          % (len(covered), len(defined), pct))

    if '--uncovered' in sys.argv:
        missing = sorted(defined - covered)
        if missing:
            print('\n# uncovered (%d):' % (len(missing),))
            print(' '.join(missing))
        else:
            print('\n# all entry points covered')


if __name__ == '__main__':
    main()
