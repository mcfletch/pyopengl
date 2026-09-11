"""The module walk passes on a platform with EGL and no gbm library.

That is Windows with ANGLE installed: ``OpenGL.EGL`` imports, so the walk goes
into it, and ``OpenGL.EGL.gbmdevice`` then refuses because ``libgbm`` is Linux
graphics infrastructure.  The refusal is an ImportError naming the library,
which is what the module promises (``test_optional_module_imports``); the walk
has to take it as that rather than as a module nobody can reach.

A machine with gbm installed cannot see this for itself, so the check is what
the platform would do: a child in which importing ``OpenGL.EGL.gbmdevice``
raises the ImportError it raises there, running the same walk.
"""

from childenv import run_in_child

WITHOUT_GBM = r'''
import sys


class NoGBMLibrary:
    """A platform where the gbm library is not installed."""

    def find_spec(self, name, path=None, target=None):
        if name == 'OpenGL.EGL.gbmdevice':
            raise ImportError(
                'OpenGL.EGL.gbmdevice needs the gbm library: '
                'Could not find module gbm'
            )
        return None


sys.meta_path.insert(0, NoGBMLibrary())

import pytest

sys.exit(pytest.main(%r))
'''


def test_the_module_walk_passes():
    completed = run_in_child(
        WITHOUT_GBM % ([
            '-q', '-p', 'no:cacheprovider',
            'tests/bindings/generated/test_every_generated_module_imports.py',
        ],),
        check=False,
    )
    assert completed.returncode == 0, (
        'the module walk failed with no gbm library present:\n%s'
        % (completed.stdout[-3000:] + completed.stderr[-2000:],)
    )
