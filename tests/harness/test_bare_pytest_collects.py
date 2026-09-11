"""A bare ``pytest`` collects what ``python -m pytest`` collects.

The two differ in one thing: ``python -m`` puts the current directory on
``sys.path``, and the console script does not.  A test importing a package that
lives at the checkout's root -- ``directdocs``, whose tests are in
``tests/directdocs`` -- finds the root package under one and, under the other,
only the test directory of the same name, which is a namespace-package portion
with nothing in it to import.  ``pythonpath`` in pyproject.toml names the root so
that both find the same thing.

The check is what the console script would do: a child that takes the current
directory off its path before collecting.
"""

from childenv import run_in_child

BARE = r'''
import os
import sys

here = os.getcwd()
sys.path[:] = [entry for entry in sys.path
               if entry not in ('', '.') and os.path.abspath(entry) != here]

import pytest

sys.exit(pytest.main(['--collect-only', '-q', '-p', 'no:cacheprovider']))
'''


def test_the_suite_collects_without_the_current_directory_on_the_path():
    completed = run_in_child(BARE, check=False)
    assert completed.returncode == 0, (
        'collection failed as a bare `pytest` runs it:\n%s'
        % (completed.stdout[-3000:] + completed.stderr[-2000:],)
    )
