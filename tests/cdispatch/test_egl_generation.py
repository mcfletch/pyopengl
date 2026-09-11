"""Generating the EGL bindings from the EGL registry.

EGL is published as its own Khronos repository, and nothing here was reading
it, so the shipped tree carried whatever it had accumulated: 116 of the 158
commands the registry declares.  The 41 that were missing were not missing
for a reason -- they were missing because nothing was looking.

These describe what the generator has to produce for them: the declaration a
raw module states, the friendly module that takes it, and the handful of types
the registry names that ``EGL/_types.py`` did not define.
"""

import os

import paths
import pytest

from cdispatch import eglgen

PACKAGE = paths.PACKAGE
EGL_XML = os.path.join(paths.ROOT, 'src', 'eglapi', 'api', 'egl.xml')

pytestmark = pytest.mark.skipif(
    not os.path.exists(EGL_XML),
    reason='no EGL registry checked out; run python src/fetch_registries.py',
)


@pytest.fixture(scope='module')
def registry():
    return eglgen.read(EGL_XML)


class TestReadingTheRegistry:
    def test_it_finds_every_command(self, registry):
        assert len(registry.commands) == 158

    def test_a_command_carries_its_signature(self, registry):
        command = registry.commands['eglCreateSyncKHR']
        assert command.result == 'EGLSyncKHR'
        assert command.argument_names == ('dpy', 'type', 'attrib_list')

    def test_a_command_knows_which_extension_declares_it(self, registry):
        assert registry.owner['eglBindWaylandDisplayWL'] == 'EGL_WL_bind_wayland_display'

    def test_an_extension_carries_its_constants(self, registry):
        constants = registry.constants['EGL_WL_bind_wayland_display']
        assert 'EGL_WAYLAND_BUFFER_WL' in constants


class TestTypeMapping:
    """What each C type in the registry is written as in a declaration."""

    def test_a_scalar_is_the_typedef(self):
        assert eglgen.ctypes_for('EGLDisplay') == '_cs.EGLDisplay'

    def test_a_pointer_to_a_scalar_is_an_array(self):
        assert eglgen.ctypes_for('EGLint *') == 'arrays.GLintArray'
        assert eglgen.ctypes_for('const  EGLint *') == 'arrays.GLintArray'

    def test_a_char_pointer_is_a_string(self):
        assert eglgen.ctypes_for('const char *') == 'ctypes.c_char_p'

    def test_void_is_none(self):
        assert eglgen.ctypes_for('void') == 'None'

    def test_a_void_pointer_is_a_void_pointer(self):
        assert eglgen.ctypes_for('void *') == 'ctypes.c_void_p'

    def test_a_pointer_to_an_opaque_handle_is_an_array_of_them(self):
        """``EGLDeviceEXT *`` is an out-parameter the caller receives."""
        assert eglgen.ctypes_for('EGLDeviceEXT *') == 'arrays.GLvoidpArray'

    def test_a_foreign_struct_pointer_is_a_void_pointer(self):
        """``struct wl_display *`` belongs to Wayland; we pass it through."""
        assert eglgen.ctypes_for('struct  wl_display *') == 'ctypes.c_void_p'


class TestTheTreeCoversTheRegistry:
    """What was a measurement of the gap is now the guard against it.

    41 commands were absent when the EGL registry was first read.  They have
    been generated; what these assert from here is that the registry has not
    since declared something nobody noticed.
    """

    def test_nothing_the_registry_declares_is_missing(self, registry):
        missing = eglgen.missing_commands(registry, PACKAGE)
        assert missing == [], (
            '%d EGL commands have no binding; regenerate with '
            'python src/generate_egl.py' % (len(missing),)
        )

    def test_a_binding_that_exists_is_not_reported_missing(self, registry):
        """``eglStreamConsumerGLTextureExternalAttribsNV`` is declared with a
        ``*attrib_list``, which the annotation extractor skips -- so it is
        absent from the command records while being perfectly present as a
        binding.  What counts here is the binding.
        """
        missing = eglgen.missing_commands(registry, PACKAGE)
        assert 'eglStreamConsumerGLTextureExternalAttribsNV' not in missing

    def test_grouping_puts_a_command_under_the_extension_that_declares_it(
        self, registry
    ):
        groups = eglgen.by_extension(
            registry, ['eglBindWaylandDisplayWL', 'eglUnbindWaylandDisplayWL']
        )
        assert groups == {
            'EGL_WL_bind_wayland_display': [
                'eglBindWaylandDisplayWL',
                'eglUnbindWaylandDisplayWL',
            ]
        }

    def test_every_type_the_registry_names_is_defined(self, registry):
        """The generator reports what it cannot express rather than guessing;
        nothing should be left for it to report."""
        assert eglgen.undefined_types(registry, PACKAGE) == set()

    def test_a_command_the_tree_lacks_would_be_reported(self, registry):
        """The guard has to be able to fail, so check it against a tree that
        genuinely lacks something."""
        import tempfile

        with tempfile.TemporaryDirectory() as empty:
            os.makedirs(os.path.join(empty, 'raw', 'EGL'))
            assert len(eglgen.missing_commands(registry, empty)) == 158


class TestEmission:
    def test_a_raw_module_declares_its_commands(self, registry):
        text = eglgen.emit_raw(registry, 'EGL_WL_bind_wayland_display')
        assert "_EXTENSION_NAME = 'EGL_WL_bind_wayland_display'" in text
        assert 'def eglBindWaylandDisplayWL(dpy,display):pass' in text
        assert '@_p.types(_cs.EGLBoolean,_cs.EGLDisplay,ctypes.c_void_p)' in text

    def test_a_raw_module_declares_its_constants(self, registry):
        text = eglgen.emit_raw(registry, 'EGL_WL_bind_wayland_display')
        assert "EGL_WAYLAND_BUFFER_WL=_C('EGL_WAYLAND_BUFFER_WL'," in text

    def test_a_friendly_module_takes_the_definitions(self, registry):
        text = eglgen.emit_friendly(registry, 'EGL_WL_bind_wayland_display')
        assert 'from OpenGL._declarations import define as _define' in text
        assert (
            "_EXTENSION_NAME = _define(globals(), "
            "'OpenGL.raw.EGL.WL.bind_wayland_display')" in text
        )
        assert 'def eglInitBindWaylandDisplayWL():' in text

    def test_the_module_path_follows_the_extension_name(self, registry):
        assert eglgen.module_path('EGL_WL_bind_wayland_display') == (
            'WL', 'bind_wayland_display'
        )
        assert eglgen.module_path('EGL_ANDROID_get_frame_timestamps') == (
            'ANDROID', 'get_frame_timestamps'
        )

    def test_every_missing_extension_emits_without_raising(self, registry):
        """The point: none of them needs a person to write it."""
        groups = eglgen.by_extension(registry, eglgen.missing_commands(registry, PACKAGE))
        for extension in groups:
            assert eglgen.emit_raw(registry, extension)
            assert eglgen.emit_friendly(registry, extension)
