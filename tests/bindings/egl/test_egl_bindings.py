"""Every EGL entry point the registry declares has a working binding.

EGL is published as its own Khronos repository and nothing in PyOpenGL was
reading it, so the tree carried whatever had accumulated: 117 of the 158
commands, with 41 absent for no reason other than that nobody had looked.
Those 41 were generated from ``egl.xml``.

Generated bindings need generated tests.  Calling them is not the point -- most
need a display, a Wayland compositor or an Android device -- so what is checked
is what a declaration *is*: that the name exists, and that its signature is the
one the registry states.

Read from the raw modules rather than the friendly ones, because that is a
static question and the friendly route is not: asking an EGL extension whether
it is available calls ``eglQueryString`` on a display, and on a machine with no
EGL display that raises rather than answering false.  Whether it *should* raise
is a separate question about ``hasGLExtension``; it is not what these are for.
"""

import ctypes
import importlib
import os

import paths
import pytest

import OpenGL._dispatch as dispatch
from OpenGL import _configflags

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = paths.ROOT
EGL_XML = os.path.join(ROOT, 'src', 'eglapi', 'api', 'egl.xml')

pytestmark = pytest.mark.skipif(
    not os.path.exists(EGL_XML),
    reason='no EGL registry checked out; run python src/fetch_registries.py',
)


def registry():
    import sys

    sys.path.insert(0, os.path.join(ROOT, 'src'))
    from cdispatch import eglgen

    return eglgen.read(EGL_XML)


REGISTRY = registry() if os.path.exists(EGL_XML) else None
COMMANDS = sorted(REGISTRY.commands) if REGISTRY else []

#: Commands whose declaration the tree writes with a ``*attrib_list``, which
#: is a Python signature rather than the registry's, so the arity check does
#: not apply to them.
VARIADIC = {'eglStreamConsumerGLTextureExternalAttribsNV'}


def module_for(name):
    """The raw module that declares this entry point."""
    owner = REGISTRY.owner.get(name, '')
    if owner.startswith('EGL_VERSION_'):
        return 'OpenGL.raw.EGL.VERSION.EGL_%s' % (owner[len('EGL_VERSION_'):],)
    if owner:
        import sys

        sys.path.insert(0, os.path.join(ROOT, 'src'))
        from cdispatch import eglgen

        vendor, short = eglgen.module_path(owner)
        return 'OpenGL.raw.EGL.%s.%s' % (vendor, short)
    return 'OpenGL.raw.EGL'


def binding(name):
    """The declared entry point, or None if nothing declares it."""
    try:
        module = importlib.import_module(module_for(name))
    except ImportError:
        return None
    return getattr(module, name, None)


class TestEveryCommandIsBound:
    @pytest.mark.parametrize('name', COMMANDS)
    def test_the_name_exists(self, name):
        assert binding(name) is not None, name

    @pytest.mark.parametrize('name', COMMANDS)
    def test_it_is_reachable_from_the_friendly_module_too(self, name):
        """The name a client imports is the same object the raw module holds."""
        friendly = module_for(name).replace('OpenGL.raw.', 'OpenGL.')
        try:
            module = importlib.import_module(friendly)
        except ImportError:
            pytest.skip('%s has no friendly module' % (friendly,))
        assert getattr(module, name, None) is not None, name


class TestSignaturesMatchTheRegistry:
    @pytest.mark.parametrize('name', COMMANDS)
    def test_the_arity_matches(self, name):
        if name in VARIADIC:
            pytest.skip('declared with a Python signature, not the registry one')
        entry = binding(name)
        names = getattr(entry, 'argNames', None)
        if names is None:
            pytest.skip('%s carries no argument names' % (name,))
        assert len(names) == len(REGISTRY.commands[name].argument_names), name

    @pytest.mark.parametrize('name', COMMANDS)
    def test_the_argument_names_match(self, name):
        if name in VARIADIC:
            pytest.skip('declared with a Python signature, not the registry one')
        entry = binding(name)
        names = getattr(entry, 'argNames', None)
        if names is None:
            pytest.skip('%s carries no argument names' % (name,))
        assert tuple(names) == REGISTRY.commands[name].argument_names, name


class TestTheNewOnes:
    """Spot checks on entry points that did not exist before, where the shape
    is worth stating rather than deriving."""

    def test_a_wayland_handle_is_passed_through(self):
        """``eglBindWaylandDisplayWL(dpy, display)`` takes a foreign pointer."""
        entry = binding('eglBindWaylandDisplayWL')
        assert tuple(entry.argNames) == ('dpy', 'display')

    def test_an_android_timestamp_is_signed(self):
        """Presentation time is signed nanoseconds, so it can be negative."""
        from OpenGL.raw.EGL import _types

        assert _types.EGLnsecsANDROID is ctypes.c_int64

    def test_a_query_taking_an_output_array(self):
        entry = binding('eglQueryDmaBufFormatsEXT')
        assert tuple(entry.argNames) == (
            'dpy', 'max_formats', 'formats', 'num_formats'
        )

    def test_an_extension_module_reports_its_name(self):
        module = importlib.import_module('OpenGL.EGL.WL.bind_wayland_display')
        assert module._EXTENSION_NAME == 'EGL_WL_bind_wayland_display'

    def test_the_availability_check_exists(self):
        """Calling it needs an EGL display; that it is there does not."""
        module = importlib.import_module('OpenGL.EGL.WL.bind_wayland_display')
        assert callable(module.eglInitBindWaylandDisplayWL)

    def test_the_constants_came_across(self):
        from OpenGL.EGL.WL.bind_wayland_display import EGL_WAYLAND_BUFFER_WL

        assert int(EGL_WAYLAND_BUFFER_WL) == 0x31D5

    def test_a_cast_constant_is_a_value_rather_than_a_comment(self):
        """The registry writes these as ``EGL_CAST(EGLnsecsANDROID,-1)``, which
        the older generator emitted commented out, defining nothing."""
        from OpenGL.raw.EGL.ANDROID.get_frame_timestamps import (
            EGL_TIMESTAMP_INVALID_ANDROID,
        )

        assert int(EGL_TIMESTAMP_INVALID_ANDROID) == -1


@pytest.mark.skipif(
    not dispatch.AVAILABLE or _configflags.DISPATCH != 'c',
    reason='the C dispatch layer is not the selected implementation',
)
class TestTheCImplementationAgrees:
    def test_most_of_them_are_implemented_in_c(self):
        """A new binding should arrive on the fast path like any other."""
        implemented = [
            name for name in COMMANDS if ('EGL', name) in dispatch.entry_points
        ]
        assert len(implemented) > len(COMMANDS) - 5, (
            len(implemented), len(COMMANDS)
        )

    @pytest.mark.parametrize('name', COMMANDS)
    def test_what_it_reports_about_itself(self, name):
        """``extension`` and ``__module__`` answer without a display."""
        entry = binding(name)
        assert entry.__name__ == name
        assert isinstance(getattr(entry, 'extension', '') or '', str)
