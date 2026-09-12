"""ANGLE: OpenGL ES on a machine whose own GL is not ES

ANGLE translates OpenGL ES onto whatever the machine really has -- Direct3D 11
on Windows, and Metal, Vulkan or desktop GL elsewhere. Windows has no EGL of
its own, so ANGLE is how a Windows program gets one, and this platform is how
PyOpenGL reaches it::

    PYOPENGL_PLATFORM=angle

It is never selected by guessing. A Windows machine's OpenGL is WGL's, and a
program that did not ask for ES should go on getting desktop GL from the
driver; asking for this platform is the whole of how it is chosen.

**The libraries it binds are Windows DLLs.** Selecting it anywhere else raises
:exc:`ImportError` naming the machine, since the ``libEGL.dll`` and
``libGLESv2.dll`` this platform loads are not what an ANGLE built for Linux or
macOS installs; a machine that has its own EGL reaches OpenGL ES through the
platform it is guessed into. The module itself imports on any machine, so the
class can be read where it cannot be loaded.

**It supplies OpenGL ES, and nothing else.** ANGLE advertises
``EGL_CLIENT_APIS`` of ``OpenGL_ES``, offers no framebuffer config carrying
``EGL_OPENGL_BIT``, and answers ``eglBindAPI(EGL_OPENGL_API)`` with
``EGL_BAD_PARAMETER``. So :attr:`GL` here is ``None``, which is what
:class:`~OpenGL.platform.baseplatform.BasePlatform` documents for a library a
platform does not have: :mod:`OpenGL.GL` still imports and every entry point in
it reports itself missing when called, naming the function. A platform that
answered ``opengl32`` instead would hand back a desktop context from a binding
that had promised ES, and the mismatch would surface somewhere far from here.

ES 1, 2 and 3 are one library. ``libGLESv2.dll`` carries ``glCreateShader`` and
``glDrawArraysInstanced`` as you would expect, and ``glAlphaFunc`` and
``glMatrixMode`` besides -- ANGLE's ES 1 emulation lives in the same file -- so
all three attributes answer with it.

**Finding it.** ANGLE is not installed system-wide: it travels inside
applications, so a machine may hold several copies and no two the same version.
Name the directory holding ``libEGL.dll`` and ``libGLESv2.dll``::

    PYOPENGL_ANGLE_PATH=C:\\path\\to\\angle

Without that variable the ordinary library search runs, which finds an ANGLE
that has been put on ``PATH`` and nothing otherwise.
"""
import ctypes
import os
import sys

from OpenGL.platform import baseplatform, ctypesloader

__all__ = ['ANGLEPlatform', 'ANGLE_PATH']

#: The environment variable naming the directory ANGLE's DLLs are in.
ANGLE_PATH = 'PYOPENGL_ANGLE_PATH'


class ANGLEPlatform(baseplatform.BasePlatform):
    """PyOpenGL's binding to an ANGLE installation: EGL, and OpenGL ES"""

    #: Stated rather than inherited, because it is the defining property of
    #: this platform rather than an omission. See the module docstring.
    GL = None

    @baseplatform.lazy_property
    def DEFAULT_FUNCTION_TYPE(self):
        """``ctypes.WINFUNCTYPE``: ``GL_APIENTRY`` is ``__stdcall``

        That is nothing on x64, where there is one calling convention, and
        everything on 32-bit. Read when a function is built rather than when
        this module is imported, because ``ctypes`` defines ``WINFUNCTYPE``
        only where there is a ``__stdcall`` to name: the class describes the
        platform on any machine, and only using it needs Windows.
        """
        return ctypes.WINFUNCTYPE

    def _load(self, name):
        """Load one of ANGLE's libraries, or ImportError saying where it looked

        A caller who has ANGLE and has not said where it is gets the same
        message as one who has none, because from here the two are the same
        situation: the fix for both is to name the directory.
        """
        if sys.platform != 'win32':
            raise ImportError(
                'ANGLE is loaded here from libEGL.dll and libGLESv2.dll, '
                'which a %s machine has no way to load. Leave '
                'PYOPENGL_PLATFORM unset for the platform this machine does '
                'have.' % (sys.platform,)
            )
        directory = os.environ.get(ANGLE_PATH)
        if directory:
            path = os.path.join(directory, '%s.dll' % (name,))
            try:
                # So that this library's own dependencies -- ANGLE's D3D
                # compiler, its SwiftShader fallback -- resolve beside it
                # rather than against whatever is on PATH.
                os.add_dll_directory(directory)
                return ctypes.WinDLL(path)
            except OSError as err:
                raise ImportError(
                    '%s names %r, which has no loadable %s.dll: %s'
                    % (ANGLE_PATH, directory, name, err)
                ) from err
        try:
            return ctypesloader.loadLibrary(ctypes.windll, name)
        except OSError as err:
            raise ImportError(
                'Unable to load ANGLE\'s %s.dll. ANGLE ships inside '
                'applications rather than being installed system-wide, so set '
                '%s to the directory holding libEGL.dll and libGLESv2.dll: %s'
                % (name, ANGLE_PATH, err)
            ) from err

    @baseplatform.lazy_property
    def EGL(self):
        return self._load('libEGL')

    @baseplatform.lazy_property
    def GLES2(self):
        return self._load('libGLESv2')

    #: ES 1 and ES 3 are the same library as ES 2; see the module docstring.
    @baseplatform.lazy_property
    def GLES1(self):
        return self.GLES2

    @baseplatform.lazy_property
    def GLES3(self):
        return self.GLES2

    @baseplatform.lazy_property
    def getExtensionProcedure(self):
        function = self.EGL.eglGetProcAddress
        function.argtypes = [ctypes.c_char_p]
        function.restype = ctypes.c_void_p
        return function

    @baseplatform.lazy_property
    def GetCurrentContext(self):
        function = self.EGL.eglGetCurrentContext
        function.argtypes = []
        function.restype = ctypes.c_void_p
        return function

    @baseplatform.lazy_property
    def CurrentContextIsValid(self):
        return self.GetCurrentContext
