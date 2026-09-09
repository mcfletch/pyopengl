# mypy: ignore-errors
# The names in this module arrive from the declaration tables at import
# time, so a checker reading this file sees calls to things it cannot
# find.  The typed surface is the .pyi stub beside the package.
"""Data-type definitions for EGL/GLES"""
import ctypes
from OpenGL._opaque import opaque_pointer_cls as _opaque_pointer_cls
from OpenGL import platform as _p
from OpenGL import extensions 
from OpenGL._bytes import as_8_bit

class _EGLQuerier( extensions.ExtensionQuerier ):
    prefix = as_8_bit('EGL_')
    assumed_version = [1,0]
    version_prefix = as_8_bit('EGL_VERSION_EGL_')
    def getDisplay( self ):
        """Retrieve the currently-bound, or the default, display"""
        from OpenGL.EGL import (
            eglGetCurrentDisplay, eglGetDisplay, EGL_DEFAULT_DISPLAY,
        )
        return eglGetCurrentDisplay() or eglGetDisplay(EGL_DEFAULT_DISPLAY)
        
    def pullVersion( self ):
        from OpenGL.EGL import (
            eglQueryString, EGL_VERSION
        )
        return eglQueryString( self.getDisplay(), EGL_VERSION )
    def pullExtensions( self ):
        from OpenGL.EGL import eglQueryString, EGL_EXTENSIONS
        return eglQueryString( self.getDisplay(), EGL_EXTENSIONS )
EGLQuerier=_EGLQuerier()

EGLBoolean = ctypes.c_uint32
EGLenum = ctypes.c_uint32
EGLint = c_int = ctypes.c_int32

EGLConfig = _opaque_pointer_cls( 'EGLConfig' )
EGLContext = _opaque_pointer_cls( 'EGLContext' )
EGLDisplay = _opaque_pointer_cls( 'EGLDisplay' )
EGLSurface = _opaque_pointer_cls( 'EGLSurface' )
EGLClientBuffer = _opaque_pointer_cls( 'EGLClientBuffer' )
EGLImageKHR = EGLImage = _opaque_pointer_cls( 'EGLImageKHR' )
EGLDeviceEXT = _opaque_pointer_cls( 'EGLDeviceEXT' )
EGLOutputLayerEXT = _opaque_pointer_cls( 'EGLOutputLayerEXT' )
EGLOutputPortEXT = _opaque_pointer_cls( 'EGLOutputPortEXT' )

EGLScreenMESA = ctypes.c_ulong
EGLModeMESA = ctypes.c_ulong

EGLNativeFileDescriptorKHR = ctypes.c_int

EGLSyncKHR = EGLSyncNV = EGLSync = _opaque_pointer_cls( 'EGLSync' )
EGLTimeKHR = EGLTimeNV = EGLTime = ctypes.c_ulonglong
# EGL_ANDROID_presentation_time and the frame-timestamp extensions
# measure in signed nanoseconds.
EGLnsecsANDROID = ctypes.c_int64

# EGL_KHR_debug and EGL_HI_clientpixmap name these; nothing defined them, so
# the three EGL_KHR_debug entry points could not be declared at all.
EGLLabelKHR = _opaque_pointer_cls( 'EGLLabelKHR' )
EGLObjectKHR = _opaque_pointer_cls( 'EGLObjectKHR' )
#: The debug callback: void (*)(EGLenum, const char *, EGLint, EGLLabelKHR,
#: EGLLabelKHR, const char *).
EGLDEBUGPROCKHR = ctypes.CFUNCTYPE(
    None,
    EGLenum,
    ctypes.c_char_p,
    EGLint,
    EGLLabelKHR,
    EGLLabelKHR,
    ctypes.c_char_p,
)


class EGLClientPixmapHI(ctypes.Structure):
    """The pixmap EGL_HI_clientpixmap hands the driver."""

    _fields_ = [
        ('pData', ctypes.c_void_p),
        ('iWidth', EGLint),
        ('iHeight', EGLint),
        ('iStride', EGLint),
    ]


EGLuint64KHR = EGLuint64NV = ctypes.c_ulonglong
EGLStreamKHR = _opaque_pointer_cls( 'EGLStream' )
EGLsizeiANDROID = ctypes.c_size_t
EGLAttribKHR = EGLAttrib = ctypes.POINTER( ctypes.c_int32 )

class EGLClientPixmapHI( ctypes.Structure):
    _fields_ = [
        ('pData',ctypes.c_voidp),
        ('iWidth',EGLint),
        ('iHeight',EGLint),
        ('iStride',EGLint),
    ]
class wl_display( ctypes.Structure):
    """Opaque structure from Mesa Wayland API"""
    _fields_ = []

# These are X11... no good, really...
EGLNativeDisplayType = _opaque_pointer_cls( 'EGLNativeDisplayType' )
EGLNativePixmapType = _opaque_pointer_cls( 'EGLNativePixmapType' )
EGLNativeWindowType = _opaque_pointer_cls( 'EGLNativeWindowType' )

NativeDisplayType = EGLNativeDisplayType 
NativePixmapType = EGLNativePixmapType
NativeWindowType = EGLNativeWindowType

# Callback types, this is a hack to avoid making the 
# khr module depend on the platform or needing to change generator for now...
CALLBACK_TYPE = _p.PLATFORM.functionTypeFor( _p.PLATFORM.EGL )
EGLSetBlobFuncANDROID = CALLBACK_TYPE( ctypes.c_voidp, EGLsizeiANDROID, ctypes.c_voidp, EGLsizeiANDROID )
EGLGetBlobFuncANDROID = CALLBACK_TYPE( ctypes.c_voidp, EGLsizeiANDROID, ctypes.c_voidp, EGLsizeiANDROID )

EGL_DEFAULT_DISPLAY = EGLNativeDisplayType()
EGL_NO_CONTEXT = EGLContext()
EGL_NO_DISPLAY = EGLDisplay()
EGL_NO_SURFACE = EGLSurface()
EGL_DONT_CARE = -1

if _p.PLATFORM.EGL is not None:
    raw_eglQueryString = _p.PLATFORM.EGL.eglQueryString
    raw_eglQueryString.restype = ctypes.c_char_p
    raw_eglQueryString.__doc__ = """Raw version of eglQueryString that does not check for availability"""
else:
    raw_eglQueryString = _p.PLATFORM.nullFunction(
        'eglQueryString',
        _p.PLATFORM.EGL,
        resultType = ctypes.c_char_p,
        argTypes = ( EGLDisplay, EGLint ),
        argNames = ( 'dpy', 'name' ),
        doc = """Raw version of eglQueryString that does not check for availability""",
    )

_VERSION_PREFIX = 'EGL_VERSION_EGL_'

# A list of type names sat here as a bare expression: built on every import
# and thrown away, because the assignment it belonged to was lost. It cannot
# be restored as `__all__` -- it is missing names the EGL extension modules
# import by name, so exporting only these breaks them.
