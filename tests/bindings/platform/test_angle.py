"""ANGLE: OpenGL ES on Windows, and only OpenGL ES.

Windows has no EGL of its own. ANGLE is how a Windows machine gets one, and it
is an OpenGL *ES* implementation -- it advertises ``EGL_CLIENT_APIS`` of
``OpenGL_ES``, offers no config carrying ``EGL_OPENGL_BIT``, and refuses
``eglBindAPI(EGL_OPENGL_API)`` with ``EGL_BAD_PARAMETER``. So this platform
supplies the three ES libraries and no desktop GL at all, which is the thing
most worth pinning: a platform that quietly answered ``opengl32`` for ``GL``
would give a caller a desktop context from a binding that had promised ES.

The cases that need ANGLE itself find it through ``PYOPENGL_ANGLE_PATH`` and
skip without it, so this file runs anywhere. The ones that do not need it --
what the platform declares, and what it says when the libraries are missing --
run everywhere and are the bulk of it. That includes importing the module on a
machine that could never load ANGLE: a platform whose module only imports where
it works is a platform nothing off that machine can check.
"""

import ctypes
import os
import sys

import pytest

from childenv import json_from_child, run_in_child

from OpenGL.platform import angle, baseplatform
from OpenGL.plugins import PlatformPlugin

windows_only = pytest.mark.skipif(
    sys.platform != 'win32',
    reason='ANGLE is reached here through Windows DLLs',
)
not_windows = pytest.mark.skipif(
    sys.platform == 'win32',
    reason='asks what a machine without ANGLE\'s DLLs is told',
)


def _angle_directory():
    """Where this machine's ANGLE lives, or None."""
    directory = os.environ.get('PYOPENGL_ANGLE_PATH')
    if directory and os.path.isfile(os.path.join(directory, 'libEGL.dll')):
        return directory
    return None


needs_angle = pytest.mark.skipif(
    _angle_directory() is None,
    reason='no ANGLE here; set PYOPENGL_ANGLE_PATH to the directory holding '
           'libEGL.dll and libGLESv2.dll',
)


class TestWhatItDeclares:
    """True on every machine, ANGLE present or not."""

    def test_it_is_registered_under_its_own_name(self):
        """``PYOPENGL_PLATFORM=angle`` is how a program asks for it, and
        nothing else selects it: a Windows machine's OpenGL is WGL's, and a
        program that did not ask for ES keeps getting desktop GL."""
        plugin = PlatformPlugin.match(('angle',))
        assert plugin.import_path == 'OpenGL.platform.angle.ANGLEPlatform'

    def test_it_offers_no_desktop_gl(self):
        """The whole point. ANGLE has no desktop GL to give, and ``None`` is
        what BasePlatform documents for a library a platform lacks -- so
        ``OpenGL.GL`` still imports and its entry points report themselves
        missing, rather than binding to something that is not there."""
        assert angle.ANGLEPlatform.GL is None

    def test_it_offers_no_glu_or_glut_either(self):
        """Neither ships with ANGLE, and neither has an ES flavour."""
        platform = angle.ANGLEPlatform()
        assert platform.GLU is None
        assert platform.GLUT is None

    @windows_only
    def test_entry_points_are_stdcall(self):
        """``GL_APIENTRY`` is ``__stdcall`` on Windows. It makes no difference
        on x64, where there is one convention, and it is the whole difference
        on 32-bit. Read from an instance, because ``WINFUNCTYPE`` exists only
        where there is a ``__stdcall`` to name and the class is read on every
        machine."""
        assert angle.ANGLEPlatform().DEFAULT_FUNCTION_TYPE is ctypes.WINFUNCTYPE

    def test_it_is_a_platform(self):
        assert issubclass(angle.ANGLEPlatform, baseplatform.BasePlatform)


@needs_angle
class TestTheEsOnlyPromiseIsEnforced:
    """Declaring ``GL = None`` is one thing; what a caller meets is another.

    This runs the binding layer for real, in a child that has selected the
    platform, because a platform is chosen once per process at import.
    """

    def test_a_desktop_only_call_names_itself_rather_than_crashing(self):
        """``glBegin`` is not in ``libGLESv2.dll`` and has no ES equivalent.
        A caller who reaches for it is told which function is missing, which is
        what ``GL = None`` buys over a platform that had answered
        ``opengl32``: that one would have handed back a desktop entry point
        from a binding that promised ES."""
        found = json_from_child(
            'import json\n'
            'from OpenGL.GL import glBegin, GL_TRIANGLES\n'
            'from OpenGL.error import NullFunctionError\n'
            'try:\n'
            '    glBegin(GL_TRIANGLES)\n'
            '    result = {"raised": None}\n'
            'except NullFunctionError as err:\n'
            '    result = {"raised": "NullFunctionError", "message": str(err)}\n'
            'print(json.dumps(result))\n',
            PYOPENGL_PLATFORM='angle',
            PYOPENGL_ANGLE_PATH=_angle_directory(),
        )
        assert found['raised'] == 'NullFunctionError'
        assert 'glBegin' in found['message']

    def test_the_es_namespaces_import_and_carry_entry_points(self):
        """The ES bindings are the point of the platform."""
        found = json_from_child(
            'import json\n'
            'import OpenGL.GLES1, OpenGL.GLES2, OpenGL.GLES3\n'
            'from OpenGL import platform\n'
            'print(json.dumps({\n'
            '    "platform": type(platform.PLATFORM).__name__,\n'
            '    "creates_shaders": bool(OpenGL.GLES2.glCreateShader),\n'
            '    "instances": bool(OpenGL.GLES3.glDrawArraysInstanced),\n'
            '}))\n',
            PYOPENGL_PLATFORM='angle',
            PYOPENGL_ANGLE_PATH=_angle_directory(),
        )
        assert found['platform'] == 'ANGLEPlatform'
        assert found['creates_shaders'] and found['instances']


class TestSelectingItWithoutIt:
    """Asking for a platform this machine cannot provide.

    ``PYOPENGL_PLATFORM=angle`` is an explicit choice, and a machine with no
    ANGLE cannot honour it at all -- every entry point this platform has comes
    out of the two DLLs. So it says so, once, naming the variable that fixes
    it, rather than importing cleanly and failing later on a null entry point
    that mentions neither ANGLE nor where to put it.
    """

    @windows_only
    def test_it_fails_at_selection_naming_what_to_set(self, tmp_path):
        completed = run_in_child(
            'import OpenGL.GLES2\n',
            check=False,
            PYOPENGL_PLATFORM='angle',
            PYOPENGL_ANGLE_PATH=str(tmp_path),
        )
        assert completed.returncode != 0
        assert 'PYOPENGL_ANGLE_PATH' in completed.stderr
        assert 'libEGL' in completed.stderr


class TestWhenAngleIsNotThere:
    @windows_only
    def test_a_directory_with_no_angle_in_it_says_so(self, tmp_path, monkeypatch):
        """Naming the variable and the file it wanted: ANGLE travels inside
        applications rather than being installed system-wide, so "which
        directory" is the question a caller is actually getting wrong."""
        monkeypatch.setenv('PYOPENGL_ANGLE_PATH', str(tmp_path))
        with pytest.raises(ImportError) as caught:
            # A lazy property: reading it is what does the load.
            _ = angle.ANGLEPlatform().EGL
        message = str(caught.value)
        assert 'PYOPENGL_ANGLE_PATH' in message
        assert 'libEGL' in message


@not_windows
class TestSelectingItOffWindows:
    """What a machine that cannot load a DLL is told.

    The libraries this platform binds are ``libEGL.dll`` and ``libGLESv2.dll``,
    so a Linux or macOS machine gets no further than asking for them. It is
    told that, in the one place that knows it -- an ``ImportError`` out of the
    load, like every other library this platform cannot find, rather than an
    ``AttributeError`` against a ``ctypes`` or ``os`` member that only exists
    on Windows, which names nothing the caller wrote and says nothing about
    ANGLE.
    """

    def test_the_module_imports(self):
        """A platform module that only imports where it runs is one nobody can
        check anywhere else: this file's cases, the type checker and a
        documentation build all read the class on the machine they are on."""
        assert angle.ANGLEPlatform.GL is None

    @pytest.mark.parametrize('name', ['EGL', 'GLES1', 'GLES2', 'GLES3'])
    def test_every_library_says_why_it_cannot_be_loaded(self, name, tmp_path,
                                                        monkeypatch):
        monkeypatch.setenv('PYOPENGL_ANGLE_PATH', str(tmp_path))
        with pytest.raises(ImportError) as caught:
            _ = getattr(angle.ANGLEPlatform(), name)
        message = str(caught.value)
        assert sys.platform in message
        assert 'libEGL.dll' in message
        assert 'PYOPENGL_PLATFORM' in message

    def test_it_says_so_without_the_path_set_too(self, monkeypatch):
        """The machine is the obstacle, not the variable, so naming a
        directory changes nothing about the answer."""
        monkeypatch.delenv('PYOPENGL_ANGLE_PATH', raising=False)
        with pytest.raises(ImportError):
            _ = angle.ANGLEPlatform().EGL


@needs_angle
class TestAgainstRealAngle:
    @pytest.fixture
    def platform(self, monkeypatch):
        monkeypatch.setenv('PYOPENGL_ANGLE_PATH', _angle_directory())
        return angle.ANGLEPlatform()

    def test_it_loads_egl(self, platform):
        assert platform.EGL is not None

    @pytest.mark.parametrize('name', ['GLES1', 'GLES2', 'GLES3'])
    def test_every_es_library_is_the_one_angle_ships(self, platform, name):
        """ANGLE puts ES1, ES2 and ES3 in one library: ``libGLESv2.dll``
        carries ``glCreateShader`` and ``glAlphaFunc`` alike, the latter being
        its ES1 emulation."""
        assert getattr(platform, name) is not None

    def test_the_es_libraries_are_one_library(self, platform):
        assert platform.GLES2 is platform.GLES3
        assert platform.GLES1 is platform.GLES2

    def test_it_resolves_an_entry_point_through_egl(self, platform):
        """``eglGetProcAddress`` is how an extension is found here."""
        address = platform.getExtensionProcedure(b'glDrawArraysInstancedANGLE')
        assert address

    def test_it_knows_no_context_is_current(self, platform):
        """Nothing has been made current on this thread, and the platform says
        so rather than raising: this is what every ``@_lazy`` GL call checks."""
        assert not platform.GetCurrentContext()
