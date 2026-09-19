#! /usr/bin/env python3
"""Switching an OSMesa context has to tell the dispatch layer it happened.

The compiled layer keeps a table of resolved entry points per context and reads
which context is current only on the *resolution* slow path -- once per entry
point per context, because asking the platform costs a Python call and the
answer is stable in between.  So the application says when it switches, and
:func:`OpenGL.dispatch.make_current` is how.

``OpenGL.WGL.offscreen`` and ``OpenGL.Tk.context`` already do.
:class:`OpenGL.osmesa.offscreen.OffscreenContext` is the third that changes the
current context inside PyOpenGL, and until it did, a program that made a second
OSMesa context went on dispatching through the first one's table: every entry
point already resolved kept the slot -- and the flag saying whether the context
had that command at all -- that it was given under a context it had left.

Two contexts of different versions is where that reaches the driver.  A command
gated in under a 3.3 core context and called under a 2.1 compatibility one is a
dispatch slot the current context never filled, and Mesa faults in
``glClear``, ``glFinish`` or ``OSMesaDestroyContext`` some calls later -- which
is how it was found: worker crashes on the OSMesa CI row, landing on a
different case each run.  See ``plans/OSMESA-PARALLEL-CRASH.md``.

In a child, because ``PYOPENGL_PLATFORM`` is settled at the first import.
"""

import ctypes.util
import textwrap

import pytest

from childenv import json_from_child

pytestmark = pytest.mark.skipif(
    ctypes.util.find_library('OSMesa') is None,
    reason='no libOSMesa installed (libosmesa6 on Debian and Ubuntu)',
)

#: Make two contexts of different versions, use each, and report what the
#: platform and the dispatch layer each think is current.
PROBE = '''
import ctypes, json
from OpenGL.osmesa import offscreen
from OpenGL.platform import PLATFORM
import OpenGL._dispatch as dispatch
import OpenGL.GL as GL

report = {'active': bool(dispatch.ACTIVE)}


def handles(label):
    """What the driver says, and what the layer is dispatching through."""
    GL.glGetString(GL.GL_VERSION)          # resolves a slot, so a table exists
    report[label] = {
        'platform': ctypes.cast(
            PLATFORM.GetCurrentContext(), ctypes.c_void_p).value,
        'layer': dispatch._c.current_handle() if dispatch.ACTIVE else None,
        'tables': dispatch._c.context_count() if dispatch.ACTIVE else None,
    }


first = offscreen.OffscreenContext(
    width=64, height=64, profile='compatibility', version=(2, 1))
handles('first')
second = offscreen.OffscreenContext(
    width=64, height=64, profile='core', version=(3, 3))
handles('second')
first.make_current()
handles('back to first')
second.release()
first.release()
print(json.dumps(report))
'''


@pytest.fixture(scope='module')
def report():
    answer = json_from_child(textwrap.dedent(PROBE), PYOPENGL_PLATFORM='osmesa')
    if not answer.get('active'):
        pytest.skip('this run dispatches through ctypes, which asks every call')
    return answer


@pytest.mark.parametrize('when', ['first', 'second', 'back to first'])
def test_the_layer_dispatches_through_the_current_context(report, when):
    seen = report[when]
    assert seen['layer'] == seen['platform'], (
        'the driver is on %s and the layer is dispatching through %s'
        % (hex(seen['platform'] or 0), hex(seen['layer'] or 0))
    )


def test_each_context_gets_a_table_of_its_own(report):
    """One table for two contexts is the same fault read from the other end:
    it means the second context was never noticed."""
    assert report['second']['tables'] >= 2, report
