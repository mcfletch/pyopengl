"""The suite's own support modules import without disturbing the run.

These are the modules the test cases build on -- ``basetestcase``,
``glcontext_es`` and friends.  Under pytest none of them is the first thing to
touch ``OpenGL``, and none of them is imported in isolation: collection imports
every one of them into a single process, in whatever order the directories
happen to sort.  A support module that only works when it gets there first, or
that reaches out and changes the process while being imported, breaks tests it
has no visible connection to -- and each of those tests still passes when run
on its own, which is the shape that hides the breakage.
"""

import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def _run(body):
    """Run ``body`` in a fresh interpreter with tests/ importable."""
    script = 'import sys\nsys.path.insert(0, %r)\n%s' % (HERE, body)
    return subprocess.run(
        [sys.executable, '-c', script],
        capture_output=True,
        text=True,
        cwd=ROOT,
        timeout=300,
    )


def test_basetestcase_imports_after_opengl_gl():
    """Importing OpenGL.GL first is the normal case, not a special one.

    The sub-suites collected ahead of the windowed tests have already imported
    OpenGL.GL, which builds the entry points and fixes the configuration they
    were built with.
    """
    completed = _run('import OpenGL.GL\nimport basetestcase\nprint("ok")\n')
    if 'Failed to initialise GLFW' in completed.stderr:
        pytest.skip('no windowing system available to initialise')
    assert completed.returncode == 0, completed.stderr[-2000:]
    assert completed.stdout.strip().endswith('ok'), completed.stdout


def test_importing_the_es_framework_leaves_the_environment_alone():
    """PYOPENGL_PLATFORM belongs to the run, not to one support module.

    Setting it while being imported changes the platform for every subprocess
    the run starts afterwards, which is most of tests/test_checks.py.  The
    place that legitimately decides it is tests/conftest.py, before any test
    module is imported at all.
    """
    completed = _run(
        'import os\n'
        'before = os.environ.get("PYOPENGL_PLATFORM")\n'
        'import glcontext_es\n'
        'print(before == os.environ.get("PYOPENGL_PLATFORM"))\n'
    )
    assert completed.returncode == 0, completed.stderr[-2000:]
    assert completed.stdout.strip().endswith('True'), (
        'importing glcontext_es changed PYOPENGL_PLATFORM: %s' % (completed.stdout,)
    )
