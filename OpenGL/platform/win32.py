"""Windows-specific platform features"""
import ctypes
import platform
from OpenGL.platform import ctypesloader, baseplatform
import sys
from typing import ClassVar

if sys.hexversion < 0x2070000:
    vc = 'vc7'
elif sys.hexversion >= 0x3050000:
    vc = 'vc14'
elif sys.hexversion >= 0x3030000:
    vc = 'vc10'
else:
    vc = 'vc9'

def _size():
    return platform.architecture()[0].strip( 'bits' )
size = _size()

class Win32Platform( baseplatform.SplitEntryPointPlatform ):
    """Win32-specific platform implementation"""

    GLUT_GUARD_CALLBACKS = True
    @baseplatform.lazy_property
    def GL(self):
        try:
            return ctypesloader.loadLibrary(
                ctypes.windll, 'opengl32', mode = ctypes.RTLD_GLOBAL
            ) 
        except OSError as err:
            raise ImportError("Unable to load OpenGL library", *err.args) from err
    @baseplatform.lazy_property
    def GLU(self):
        try:
            return ctypesloader.loadLibrary(
                ctypes.windll, 'glu32', mode = ctypes.RTLD_GLOBAL
            )
        except OSError:
            return None
    #: The GLUT libraries to try, in order.
    #:
    #: The plain names come first, so a GLUT the user installed takes
    #: precedence over the bundled builds.  The official freeglut Windows
    #: binaries, MSYS2 and vcpkg all install ``freeglut.dll``.  The original
    #: GLUT is ``glut32.dll`` on 64-bit machines too, because the 32 refers to
    #: the Win32 API rather than the word size.
    #:
    #: The vc-tagged names are the builds in ``PyOpenGL-glut-binaries``.  Only
    #: that package uses those names.  A freeglut on ``PATH`` under its usual
    #: name is still found through the plain names.
    #:
    #: Each freeglut name comes before the matching GLUT name, because freeglut
    #: is maintained and the bundled builds are also freeglut.
    #:
    #: https://github.com/mcfletch/pyopengl/issues/76
    #: https://github.com/mcfletch/pyopengl/issues/125
    GLUT_LIBRARY_NAMES = (
        'freeglut',
        'freeglut%s.%s'%(size,vc,),
        'glut32',
        'glut',
        'glut%s.%s'%(size,vc,),
    )

    @baseplatform.lazy_property
    def GLUT( self ):
        for possible in self.GLUT_LIBRARY_NAMES:
            try:
                return ctypesloader.loadLibrary(
                    ctypes.windll, possible, mode = ctypes.RTLD_GLOBAL
                )
            except OSError:
                # The wrong architecture, a missing dependency, or no such
                # library.  Try the next name.
                pass
        return None
    @baseplatform.lazy_property
    def GLE( self ):
        for libName in ('gle%s.%s'%(size,vc,), 'opengle%s.%s'%(size,vc,)):
            try:
                GLE = ctypesloader.loadLibrary( ctypes.cdll, libName )
                GLE.FunctionType = ctypes.CFUNCTYPE
                return GLE
            except OSError:
                pass
        return None

    def _optional_library( self, *names ):
        """The first library in ``names`` that loads, or None

        The ES and EGL libraries are not part of Windows.  They are installed
        by applications that ship ANGLE, so most machines lack them.
        """
        for name in names:
            try:
                return ctypesloader.loadLibrary(
                    ctypes.windll, name, mode = ctypes.RTLD_GLOBAL
                )
            except OSError:
                continue
        return None

    # On Windows, OpenGL ES and EGL come from ANGLE.  Applications that ship
    # ANGLE (Chromium, Qt and Electron) install it beside the application under
    # the lib-prefixed names below.  SDKs and driver vendors use the bare names.
    @baseplatform.lazy_property
    def GLES1( self ):
        return self._optional_library( 'libGLESv1_CM', 'GLESv1_CM' )
    @baseplatform.lazy_property
    def GLES2( self ):
        return self._optional_library( 'libGLESv2', 'GLESv2' )
    @baseplatform.lazy_property
    def GLES3( self ):
        # The implementer's guide says to ship ES3 in the ES2 library.
        return self.GLES2
    @baseplatform.lazy_property
    def EGL( self ):
        return self._optional_library( 'libEGL', 'EGL' )

    DEFAULT_FUNCTION_TYPE = staticmethod( ctypes.WINFUNCTYPE )
    # Win32 GLUT uses different types for callbacks and functions...
    GLUT_CALLBACK_TYPE = staticmethod( ctypes.CFUNCTYPE )
    GDI32 = ctypes.windll.gdi32

    def secondaryLibraries(self):
        """gdi32, which exports the pixel-format calls and SwapBuffers.

        OpenGL.WGL declares ChoosePixelFormat, DescribePixelFormat,
        GetPixelFormat, SetPixelFormat and SwapBuffers.  They are GDI entry
        points, and opengl32 does not export them.  wglGetProcAddress returns
        only extension entry points, so it returns NULL for them too.  The
        lookup must search gdi32 to find them.
        """
        return (self.GDI32,)
    @baseplatform.lazy_property
    def WGL( self ):
        return self.OpenGL
    @baseplatform.lazy_property
    def getExtensionProcedure( self ):
        wglGetProcAddress = self.OpenGL.wglGetProcAddress
        wglGetProcAddress.restype = ctypes.c_void_p

        def getExtensionProcedure( name ):
            """The address of ``name``, recording a lookup inside a glBegin block

            Every entry point above GL 1.1 is resolved here, so the first call
            to one inside a glBegin block triggers a lookup.
            wglGetProcAddress records GL_INVALID_OPERATION when called inside
            the block.  glGetError returns 0 until the block ends, so the error
            would be reported by glEnd, for a call the caller did not make.
            """
            from OpenGL import error

            if error.inside_begin_block():
                error.note_lookup_inside_block()
            return wglGetProcAddress( name )

        return getExtensionProcedure

    GLUT_FONT_CONSTANTS: ClassVar[dict] = {
        'GLUT_STROKE_ROMAN': ctypes.c_void_p( 0),
        'GLUT_STROKE_MONO_ROMAN': ctypes.c_void_p( 1),
        'GLUT_BITMAP_9_BY_15': ctypes.c_void_p( 2),
        'GLUT_BITMAP_8_BY_13': ctypes.c_void_p( 3),
        'GLUT_BITMAP_TIMES_ROMAN_10': ctypes.c_void_p( 4),
        'GLUT_BITMAP_TIMES_ROMAN_24': ctypes.c_void_p( 5),
        'GLUT_BITMAP_HELVETICA_10': ctypes.c_void_p( 6),
        'GLUT_BITMAP_HELVETICA_12': ctypes.c_void_p( 7),
        'GLUT_BITMAP_HELVETICA_18': ctypes.c_void_p( 8),
    }


    def getGLUTFontPointer( self,constant ):
        """Platform specific function to retrieve a GLUT font pointer

        GLUTAPI void *glutBitmap9By15;
        #define GLUT_BITMAP_9_BY_15		(&glutBitmap9By15)

        Key here is that we want the addressof the pointer in the DLL,
        not the pointer in the DLL.  That is, our pointer is to the
        pointer defined in the DLL, we don't want the *value* stored in
        that pointer.
        """
        return self.GLUT_FONT_CONSTANTS[ constant ]

    @baseplatform.lazy_property
    def GetCurrentContext( self ):
        wglGetCurrentContext = self.GL.wglGetCurrentContext
        wglGetCurrentContext.restype = ctypes.c_void_p
        return wglGetCurrentContext

    def releaseCurrentContext( self ):
        """Release this thread's current WGL or EGL context; True if released

        See
        :meth:`OpenGL.platform.baseplatform.BasePlatform.releaseCurrentContext`
        for why a program using two GL binding APIs needs this.  When an
        application ships ANGLE, Windows has both WGL and EGL, as Linux has
        both GLX and EGL.

        Both APIs are checked, because either may hold the thread.  The checks
        cost little compared with creating a context.
        """
        released = False
        if self._releaseWGL():
            released = True
        if self._releaseEGL():
            released = True
        return released

    def _releaseWGL( self ):
        """Release a current WGL context; True if one was current"""
        if not self.GetCurrentContext():
            return False
        from OpenGL.raw.WGL._types import HDC, HGLRC

        self.GL.wglMakeCurrent( HDC( 0 ), HGLRC( 0 ) )
        return True

    def _releaseEGL( self ):
        """Release a current EGL context; True if one was current

        Runs only when the platform found an EGL library.  The check uses
        :attr:`EGL` rather than an import attempt.  Most machines have no
        ANGLE, this runs before every context a program creates, and Python
        does not cache a failed import.  An import attempt would re-run all of
        ``OpenGL.raw.EGL`` each time.
        """
        if self.EGL is None:
            return False
        from OpenGL import EGL
        if not EGL.eglGetCurrentContext():
            return False
        display = EGL.eglGetCurrentDisplay()
        if not display:                     # pragma: no cover - needs ANGLE
            return False
        EGL.eglMakeCurrent( display, EGL.EGL_NO_SURFACE, EGL.EGL_NO_SURFACE,
                            EGL.EGL_NO_CONTEXT )
        return True

    def entryPointRoutes( self, dll ):
        """The lookups to try for a name on Windows, in order

        Windows splits the entry points across three sources, and the split
        does not follow the declarations.  ``opengl32`` exports GL 1.1 only.
        ``wglGetProcAddress`` returns everything above GL 1.1 and NULL for the
        1.1 set.  The pixel-format calls and SwapBuffers are in gdi32.  Each is
        tried in turn.  The last two routes cover opposite cases: a
        core-declared name the driver offers only as an extension, and an
        extension-declared name in the 1.1 export set.

        ``glGetPointerv`` is an example of the second case, through
        ``GL_KHR_debug``.  A name declared by both a core version and an
        extension is stored once in ``OpenGL.GL``, by whichever module was
        imported last.  The import order must not decide whether the entry
        point works.
        """
        return (
            dict(dll=dll),
            dict(dll=self.GDI32),
            dict(dll=dll, force_extension=True),
            dict(dll=dll, force_base=True),
        )
