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

#: A budget in seconds and in module count is as much a measurement of the
#: machine as of the library, so it is deselectable on one that is busy.
pytestmark = [
    pytest.mark.resources,
    pytest.mark.skipif(
        not dispatch.AVAILABLE or _configflags.DISPATCH != 'c',
        reason='the C dispatch layer is not the selected implementation',
    ),
]


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

# Wrapped on the instance rather than the class, because what
# GetCurrentContext *is* differs by platform: a method on Linux, and on macOS
# and Windows a lazy_property whose value is the driver's own ctypes function.
# An instance attribute shadows either -- which is how the lazy one caches
# itself -- so reading it here and putting the wrapper back gives one shape to
# call whichever platform this is.
calls = []
base = platform.PLATFORM.GetCurrentContext
def traced(*args, **named):
    calls.append(1)
    return base(*args, **named)
platform.PLATFORM.GetCurrentContext = traced

import OpenGL.GL  # noqa: F401
during_import = len(calls)

# What a count of zero means depends on the wrapper having been reached at all,
# and a hook that stopped intercepting reports the same zero as an import that
# asks nothing.  So say which it was.
platform.PLATFORM.GetCurrentContext()
print(json.dumps({
    'queries': during_import,
    'hook_reached': len(calls) > during_import,
}))
'''


def test_importing_does_not_interrogate_the_driver_per_entry_point():
    """Asking which context is current costs 97 ns, and at import there is none.

    An entry point resolves when it is called.  Anything that resolves them all
    at import pays for every entry point the program will never use, and does
    it at the one moment the answer cannot be right.
    """
    measured = run(CONTEXT_QUERIES)
    assert measured['hook_reached'], 'counted nothing because nothing was counting'
    assert measured['queries'] < 20


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
