#! /usr/bin/env python3
"""An installation that cannot say what it is says so.

A directory named ``OpenGL`` with no ``__init__.py`` in it, on ``sys.path``,
is imported as a namespace package.  The finder that does that runs ahead of
the one an editable install adds, so an empty directory wins over the real
installation -- and the submodules still load, because the editable install's
finder answers for those by name.  The result is a package whose own module
never ran, holding none of the configuration flags, with every submodule
present and correct.  What that looks like is an ``ImportError`` from
``OpenGL._configflags``, four frames inside a friendly module's import.

Two ordinary things leave such a directory: an install that replaced a wheel
with an editable install of the same project and left the emptied directory
behind, and a directory of that name in whatever directory a script was run
from.

Only an installation reached through a finder can be shadowed this way.  A
namespace portion is used when *nothing* on ``sys.path`` is a package, so a
copy in site-packages answers first and there is nothing to shadow -- and the
cases here say so rather than passing for that reason.
"""

import os
import subprocess
import sys

import pytest


def run(where, source):
    """`source` in a child run from ``where``, which is its ``sys.path[0]``."""
    return subprocess.run(
        [sys.executable, '-c', source],
        capture_output=True, text=True, cwd=where, timeout=300,
    )


@pytest.fixture
def husk(tmp_path):
    """A directory holding nothing but the name, run from.

    Skipped where this installation is not one an empty directory can get in
    front of.
    """
    (tmp_path / 'OpenGL').mkdir()
    where = str(tmp_path)
    settled = run(where, 'import OpenGL; print(getattr(OpenGL, "__file__", None))')
    if settled.returncode == 0 and settled.stdout.strip() not in ('None', ''):
        pytest.skip(
            'this installation answers from sys.path (%s), so nothing shadows it'
            % (settled.stdout.strip(),)
        )
    return where


class TestTheFailureNamesItself:
    def test_it_says_what_was_imported_instead(self, husk):
        completed = run(husk, 'from OpenGL.WGL import offscreen')
        assert completed.returncode != 0, completed.stdout
        assert 'namespace package' in completed.stderr, completed.stderr

    def test_and_where_the_directory_is(self, husk):
        """The one thing a reader has to have: somewhere to go and look.

        The directory is empty, so nothing else in the failure points at it.
        """
        completed = run(husk, 'import OpenGL._configflags')
        assert os.path.join(husk, 'OpenGL') in completed.stderr, completed.stderr

    def test_a_sound_installation_is_untouched(self, tmp_path):
        """The guard costs an ordinary import nothing but the question."""
        completed = run(
            str(tmp_path),
            'import OpenGL._configflags as c; print(c.ERROR_CHECKING)',
        )
        assert completed.returncode == 0, completed.stderr
        assert completed.stdout.strip() in ('True', 'False'), completed.stdout
