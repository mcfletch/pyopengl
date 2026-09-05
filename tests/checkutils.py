"""Helpers for the stand-alone check scripts run by ``test_checks.py``.

The check runner launches each script as a subprocess and inspects its
output/return code.  These helpers let a script bow out cleanly when an
optional dependency is missing and report success in the form the runner
understands.
"""

from __future__ import print_function
import importlib
import sys
import unittest

# Autotools-style "skipped" exit code; ``test_checks.py`` maps it to
# ``pytest.skip`` so a missing optional dependency is a skip, not a failure.
SKIP_EXIT_CODE = 77


def skip(reason):
    """Report ``reason`` and exit with the runner's skip return code."""
    print('SKIP: %s' % (reason,))
    raise SystemExit(SKIP_EXIT_CODE)


def run_check(function, *args, **named):
    """Call ``function``, turning a skip into the runner's skip return code.

    A script reaches its context through the same fixture the test cases use,
    and that fixture skips -- there is no display, the driver will not give the
    profile asked for -- by raising :exc:`unittest.SkipTest`.  Uncaught in a
    script, that is a traceback and an empty stdout, which the runner reads as
    a failure.  Anything else the script raises is its own defect and is left
    to propagate.
    """
    try:
        return function(*args, **named)
    except unittest.SkipTest as err:
        skip(err)


def require(module_name):
    """Return ``module_name`` if importable, otherwise skip the check."""
    try:
        return importlib.import_module(module_name)
    except ImportError as err:
        skip('%s not installed (%s)' % (module_name, err))


def run(**named):
    """Run the script's ``unittest`` cases, emitting ``OK`` to stdout on success.

    ``unittest`` writes its own report to stderr; the runner only reads stdout,
    so we print the ``OK`` it looks for and propagate a failing return code.
    """
    result = unittest.main(exit=False, **named).result
    if result.wasSuccessful():
        print('OK')
        raise SystemExit(0)
    raise SystemExit(1)
