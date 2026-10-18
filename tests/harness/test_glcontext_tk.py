"""The Tk backend of the suite leaves nothing for the garbage collector to find.

Tcl requires an interpreter to be deleted by the thread that created it, and the
interpreter goes when the last reference to its ``tkinter.Tk`` does.  A widget's
bindings close over the widget, so a destroyed root is held by a cycle until a
collection finds it -- on whichever thread triggers one.  Under
``pytest-timeout``'s thread method that can be the timer's thread, and Tcl
answers with ``Tcl_AsyncDelete: async handler deleted by the wrong thread`` and
aborts the run.  So ``_destroy_context`` collects, on the thread that made the
root, before the next case starts.
"""

import gc
import weakref

import pytest

from backends import has_window_server

pytest.importorskip('tkinter')

pytestmark = pytest.mark.skipif(
    not has_window_server(), reason='no window server to open a Tk window on')


class Case(object):
    """What `TkBackend` reads of a `ContextTestCase`, without the test case"""

    api = 'gl'
    profile = 'core'
    gl_version = (3, 3)
    red_size = green_size = blue_size = 8
    alpha_size = 0
    depth_size = 24
    stencil_size = 0
    width, height = 64, 64
    visible = False

    def skipTest(self, reason):
        pytest.skip(reason)


def backend():
    from glcontext_tk import TkBackend

    class Backend(TkBackend, Case):
        pass

    return Backend()


def test_the_root_is_gone_once_the_context_is_destroyed():
    gc.collect()
    enabled = gc.isenabled()
    gc.disable()
    try:
        case = backend()
        case._create_context()
        references = weakref.ref(case._root), weakref.ref(case._frame)
        case._destroy_context()
        assert [reference() is None for reference in references] == [True, True]
    finally:
        if enabled:
            gc.enable()


def test_a_cycle_through_the_widget_does_not_keep_the_root():
    """What a callback closing over the widget leaves: nothing refers to the
    widget from outside, and reference counting alone never frees it."""
    gc.collect()
    enabled = gc.isenabled()
    gc.disable()
    try:
        case = backend()
        case._create_context()
        case._frame.callback = case._frame.makeCurrent
        references = weakref.ref(case._root), weakref.ref(case._frame)
        case._destroy_context()
        assert [reference() is None for reference in references] == [True, True]
    finally:
        if enabled:
            gc.enable()
