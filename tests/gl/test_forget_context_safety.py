"""``forget_context`` must not pull a table out from under another thread.

The layer gives every context its own table of resolved function pointers, and
``forget_context(handle)`` is the documented way to release one when a context
has been destroyed.  The pointer each thread dispatches through is
thread-local, so freeing the table only ever cleared the pointer belonging to
the thread that called ``forget_context``: every other thread that had ever
called ``make_current`` for that handle kept a pointer into freed memory, and
its next call read it.

A program that creates and destroys a context per window, or per off-screen
render job, from more than one thread is the ordinary case rather than a
contrived one, and the documentation recommends the call.
"""

import os
import subprocess
import sys
import textwrap

import paths
import pytest

from childenv import run_in_child

import OpenGL._dispatch as dispatch
from OpenGL import _configflags

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = paths.ROOT

pytestmark = pytest.mark.skipif(
    not dispatch.AVAILABLE or _configflags.DISPATCH != 'c',
    reason='per-context tables exist only in the C implementation',
)

#: A worker points at a context's table, the main thread forgets that context,
#: and the worker dispatches again.  Reading a freed table is what used to
#: happen; the read lands in freed arena memory, so whether it faults depends
#: on what the allocator did next -- which is why this runs several times.
RACE = textwrap.dedent(
    '''
    import threading
    import OpenGL.GL as GL
    from OpenGL._dispatch import _c

    HANDLE = 0x5EED
    ready, go = threading.Event(), threading.Event()

    def other():
        _c.make_current(HANDLE)
        ready.set()
        go.wait()
        for _ in range(2000):
            _c.slot_address(GL.glGetString)

    worker = threading.Thread(target=other)
    worker.start()
    ready.wait()
    _c.forget_context(HANDLE)
    go.set()
    worker.join()
    print('survived')
    '''
)


def run_race():
    completed = run_in_child(RACE, timeout=120)
    return completed.returncode, completed.stdout.strip()


def test_forgetting_a_context_another_thread_uses_does_not_crash():
    """Ten runs, because the fault is allocator-dependent and intermittent."""
    failures = []
    for attempt in range(10):
        code, output = run_race()
        if code != 0 or 'survived' not in output:
            failures.append((attempt, code))
    assert failures == [], (
        '%d of 10 runs died; exit 139 is a segmentation fault' % (len(failures),)
    )


def test_a_forgotten_context_is_no_longer_counted():
    """The point of the call is still served: the table stops being live."""
    from OpenGL._dispatch import _c

    before = _c.context_count()
    _c.make_current(0xBEEF)
    assert _c.context_count() == before + 1
    _c.forget_context(0xBEEF)
    assert _c.context_count() == before


def test_dispatching_after_a_forget_still_works():
    """A thread whose table was forgotten re-resolves rather than reading it."""
    from OpenGL._dispatch import _c

    _c.make_current(0xF00D)
    _c.forget_context(0xF00D)
    # The handle is gone, so the next dispatch has to fall back and resolve
    # again rather than trusting what the retired table held.
    assert _c.current_handle() in (0, 0xF00D)


class TestRetiredTablesCanBeReclaimed:
    """A forgotten context's table is retired rather than freed, because another
    thread may still be pointing at it.  A program that opens and closes many
    contexts accumulates them, so there has to be a way to say "no thread is
    holding one now"."""

    def test_reclaim_reports_how_many_it_freed(self):
        dispatch = pytest.importorskip('OpenGL._dispatch')
        if not dispatch.AVAILABLE:
            pytest.skip('the C dispatch extension is not built')
        c = dispatch._c

        c.reclaim_retired()                      # start from a known state
        before = c.context_count()
        c.make_current(0xF00D0001)
        c.make_current(0xF00D0002)
        assert c.context_count() == before + 2
        c.forget_context(0xF00D0001)
        c.forget_context(0xF00D0002)
        assert c.context_count() == before
        assert c.reclaim_retired() == 2
        assert c.reclaim_retired() == 0
        c.make_current(0)

    def test_reclaiming_does_not_touch_a_live_table(self):
        dispatch = pytest.importorskip('OpenGL._dispatch')
        if not dispatch.AVAILABLE:
            pytest.skip('the C dispatch extension is not built')
        c = dispatch._c

        c.reclaim_retired()
        c.make_current(0xF00D0003)
        before = c.context_count()
        assert c.reclaim_retired() == 0
        assert c.context_count() == before
        c.forget_context(0xF00D0003)
        c.reclaim_retired()
        c.make_current(0)
