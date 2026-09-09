"""Windows-specific platform features"""
import ctypes
import platform
from OpenGL.platform import ctypesloader, baseplatform
import sys

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

class Win32Platform( baseplatform.BasePlatform ):
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
    @baseplatform.lazy_property
    def GLUT( self ):
        for possible in ('freeglut%s.%s'%(size,vc,), 'glut%s.%s'%(size,vc,)):
            # Prefer FreeGLUT if the user has installed it, fallback to the included 
            # GLUT if it is installed
            try:
                return ctypesloader.loadLibrary(
                    ctypes.windll, possible, mode = ctypes.RTLD_GLOBAL
                )
            except WindowsError:
                pass
        return None
    @baseplatform.lazy_property
    def GLE( self ):
        for libName in ('gle%s.%s'%(size,vc,), 'opengle%s.%s'%(size,vc,)):
            try:
                GLE = ctypesloader.loadLibrary( ctypes.cdll, libName )
                GLE.FunctionType = ctypes.CFUNCTYPE
                return GLE
            except WindowsError:
                pass
            else:
                break
        return None

    def _optional_library( self, *names ):
        """The first of names that loads, or None if this machine has none

        The ES and EGL libraries are not part of Windows: they arrive with an
        application that ships ANGLE, so their absence is ordinary rather than
        an error.
        """
        for name in names:
            try:
                return ctypesloader.loadLibrary(
                    ctypes.windll, name, mode = ctypes.RTLD_GLOBAL
                )
            except OSError:
                continue
        return None

    # OpenGL-ES and EGL reach Windows through ANGLE, which installs beside the
    # application that ships it (Chromium, Qt and Electron all do) under the
    # names below.  The bare names are the ones an SDK or a driver vendor uses.
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
        """gdi32, where the pixel-format calls and SwapBuffers actually live.

        A WGL program reaches ChoosePixelFormat, DescribePixelFormat,
        GetPixelFormat, SetPixelFormat and SwapBuffers through OpenGL.WGL, but
        they are GDI entry points and opengl32 does not export them. Nor does
        wglGetProcAddress answer for them -- it returns extension entry points,
        and these are not extensions -- so a search that does not know about
        gdi32 finds them nowhere.
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
            """Address for name, noting the error a lookup in a block records

            Every entry point above GL 1.1 is reached through this, so the
            first call to one made inside a glBegin block resolves here -- and
            wglGetProcAddress records GL_INVALID_OPERATION when it is called
            there.  glGetError answers 0 until the block ends, so the error
            would surface out of glEnd, for a call the caller never wrote.
            """
            from OpenGL import error

            if error.inside_begin_block():
                error.note_lookup_inside_block()
            return wglGetProcAddress( name )

        return getExtensionProcedure

    GLUT_FONT_CONSTANTS = {
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
        """Let go of the context this thread holds, WGL's or EGL's

        Answers whether there was one.  See
        :meth:`OpenGL.platform.baseplatform.BasePlatform.releaseCurrentContext`
        for why a program with two GL bindings in it needs this.  Windows has
        the same pair as Linux does whenever an application ships ANGLE, which
        is how OpenGL-ES and EGL reach this platform at all.

        Both are asked, because either may be holding it and asking is cheap
        beside making a context.
        """
        released = False
        if self._releaseWGL():
            released = True
        if self._releaseEGL():
            released = True
        return released

    def _releaseWGL( self ):
        """Release a current WGL context; answer whether there was one"""
        if not self.GetCurrentContext():
            return False
        from OpenGL.raw.WGL._types import HDC, HGLRC

        self.GL.wglMakeCurrent( HDC( 0 ), HGLRC( 0 ) )
        return True

    def _releaseEGL( self ):
        """Release a current EGL context; answer whether there was one

        Only where an EGL library was found, and asked of the platform rather
        than of the import: a machine with no ANGLE beside it is the ordinary
        case here, this is called before every context a program makes, and a
        failed import is not remembered -- so importing to find out would run
        the whole of ``OpenGL.raw.EGL`` again on each one.
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

    def constructFunction(
        self,
        functionName, dll, 
        resultType=ctypes.c_int, argTypes=(),
        doc = None, argNames = (),
        extension = None,
        deprecated = False,
        module = None,
        force_extension = False,
        error_checker = None,
    ):
        """Override construct function to do win32-specific hacks to find entry points

        Windows splits the entry points between two places and the split does
        not follow the declarations.  ``opengl32`` exports GL 1.1 and nothing
        above it; ``wglGetProcAddress`` answers for everything above GL 1.1 and
        returns NULL for the 1.1 set, and the pixel-format calls are in gdi32.
        So each is tried in turn, and the last two are each other's mirror:
        a core-declared name the driver only offers as an extension, and an
        extension-declared name that is in the 1.1 export set.

        The second is what ``GL_KHR_debug`` does to ``glGetPointerv``.  A name
        declared by both a core version and an extension is held once in
        ``OpenGL.GL``, by whichever module imported last, and which one that is
        must not decide whether the entry point works.

        Every route is tried here, so a caller's ``force_extension`` cannot
        change what is found and is not passed on.
        """
        attempts = (
            dict(dll=dll),
            dict(dll=self.GDI32),
            dict(dll=dll, force_extension=True),
            dict(dll=dll, force_base=True),
        )
        for index, attempt in enumerate(attempts):
            try:
                return super().constructFunction(
                    functionName,
                    resultType=resultType, argTypes=argTypes,
                    doc=doc, argNames=argNames,
                    extension=extension,
                    deprecated=deprecated,
                    module=module,
                    error_checker=error_checker,
                    **attempt
                )
            except AttributeError:
                if index == len(attempts) - 1:
                    raise
            
