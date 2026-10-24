"""ANGLE platform: OpenGL ES and EGL on Windows

ANGLE is an implementation of OpenGL ES and EGL that translates ES calls to the
machine's native API: Direct3D 11 on Windows, and Metal, Vulkan or desktop GL
elsewhere.  Windows has no native EGL, so a Windows program uses ANGLE to get
one.  Select this platform with::

    PYOPENGL_PLATFORM=angle

This platform is used only when named.  It is never selected automatically,
because a Windows program that did not request ES should get desktop GL from
the WGL driver.

This platform loads Windows DLLs (``libEGL.dll`` and ``libGLESv2.dll``).
Selecting it on another operating system raises :exc:`ImportError` naming the
platform.  ANGLE builds for Linux and macOS install differently named
libraries, and those machines reach OpenGL ES through their default platform.
The module itself imports on any machine, so the class can be inspected where
it cannot be loaded.

ANGLE provides only OpenGL ES.  It reports ``EGL_CLIENT_APIS`` as
``OpenGL_ES``, has no framebuffer config with ``EGL_OPENGL_BIT``, and returns
``EGL_BAD_PARAMETER`` from ``eglBindAPI(EGL_OPENGL_API)``.  :attr:`GL` is
therefore ``None``, which
:class:`~OpenGL.platform.baseplatform.BasePlatform` documents for a library a
platform does not have.  :mod:`OpenGL.GL` still imports, and each of its entry
points raises an error naming the function when called.  Loading
``opengl32`` instead would return desktop GL contexts from a platform that
selected ES.

ES 1, 2 and 3 share one library.  ``libGLESv2.dll`` contains ``glCreateShader``
and ``glDrawArraysInstanced``.  It also contains ``glAlphaFunc`` and
``glMatrixMode``, because ANGLE's ES 1 emulation is in the same file.  All
three attributes therefore return that library.

ANGLE is not installed system-wide.  Applications ship their own copies, so a
machine may have several copies of different versions.  Set the directory
holding ``libEGL.dll`` and ``libGLESv2.dll`` with::

    PYOPENGL_ANGLE_PATH=C:\\path\\to\\angle

Without that variable the ordinary library search runs, which only finds an
ANGLE whose directory is on ``PATH``.
"""
import ctypes
import os
import sys

from OpenGL.platform import baseplatform, ctypesloader

__all__ = ['ANGLEPlatform', 'ANGLE_PATH']

#: The environment variable naming the directory ANGLE's DLLs are in.
ANGLE_PATH = 'PYOPENGL_ANGLE_PATH'


class ANGLEPlatform(baseplatform.BasePlatform):
    """PyOpenGL platform for an ANGLE installation's EGL and OpenGL ES"""

    #: Set explicitly because ANGLE has no desktop GL library.  See the module
    #: docstring.
    GL = None

    @baseplatform.lazy_property
    def DEFAULT_FUNCTION_TYPE(self):
        """``ctypes.WINFUNCTYPE``: ``GL_APIENTRY`` is ``__stdcall``

        The difference matters only on 32-bit Windows.  x64 has a single
        calling convention.  The value is read when a function is built rather
        than at import, because ``ctypes`` defines ``WINFUNCTYPE`` only on
        Windows.  The class can then be imported on any machine.
        """
        return ctypes.WINFUNCTYPE

    def _load(self, name):
        """One of ANGLE's libraries; raises ImportError naming where it looked

        A machine with ANGLE in an unnamed directory and a machine without
        ANGLE get the same message.  In both cases the fix is to set
        ``PYOPENGL_ANGLE_PATH``.
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
                # The library's own dependencies (ANGLE's D3D compiler and its
                # SwiftShader fallback) then load from the same directory
                # instead of from PATH.
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
