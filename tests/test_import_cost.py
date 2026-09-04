"""What importing PyOpenGL is allowed to do.

Import is not a small cost for a library this size, and the things that make it
large are the ones easy to add without noticing: a module pulled in for a
feature nobody switched on, work done per entry point that only one caller in a
thousand needs, a question asked of the driver before there is a driver to ask.

These put numbers on it, generously enough that ordinary change does not trip
them and tightly enough that a regression of the kind that has happened does.
"""

import json
import os
import subprocess
import sys

import pytest

from childenv import child_environment

import OpenGL._dispatch as dispatch
from OpenGL import _configflags

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

pytestmark = pytest.mark.skipif(
    not dispatch.AVAILABLE or _configflags.DISPATCH != 'c',
    reason='the C dispatch layer is not the selected implementation',
)


def run(source):
    environment = child_environment()
    completed = subprocess.run(
        [sys.executable, '-c', source],
        capture_output=True,
        text=True,
        cwd=ROOT,
        env=environment,
        timeout=300,
    )
    assert completed.returncode == 0, completed.stderr[-2000:]
    return json.loads(completed.stdout)


CONTEXT_QUERIES = r'''
import json
import OpenGL.platform as platform

calls = []
base = type(platform.PLATFORM).GetCurrentContext
def traced(self, *args, **named):
    calls.append(1)
    return base(self, *args, **named)
type(platform.PLATFORM).GetCurrentContext = traced

import OpenGL.GL  # noqa: F401
print(json.dumps({'queries': len(calls)}))
'''


def test_importing_does_not_interrogate_the_driver_per_entry_point():
    """Asking which context is current costs 97 ns, and at import there is none.

    An entry point resolves when it is called.  Anything that resolves them all
    at import pays for every entry point the program will never use, and does
    it at the one moment the answer cannot be right.
    """
    assert run(CONTEXT_QUERIES)['queries'] < 20


BINDINGS = r'''
import json
import OpenGL.GL  # noqa: F401
from OpenGL._dispatch import support, entry_points
print(json.dumps({
    'ctypes_bindings': len(support._ctypes_bindings),
    'entry_points': len(entry_points),
}))
'''


def test_a_ctypes_binding_is_built_only_where_it_is_needed():
    """The ctypes binding exists for demotion, which almost nothing does.

    Building one for every entry point the C already implements is work whose
    result is discarded on the same line.
    """
    result = run(BINDINGS)
    assert result['ctypes_bindings'] < 100, result
