"""Data-type definitions for EGL/GLES"""
import ctypes
from OpenGL._opaque import opaque_pointer_cls as _opaque_pointer_cls
pointer = ctypes.pointer

EGLBoolean = ctypes.c_uint32
EGLenum = ctypes.c_uint32
EGLint = c_int = ctypes.c_int32

EGLConfig = _opaque_pointer_cls( 'EGLConfig' )
EGLContext = _opaque_pointer_cls( 'EGLContext' )
EGLDisplay = _opaque_pointer_cls( 'EGLDisplay' )
EGLSurface = _opaque_pointer_cls( 'EGLSurface' )
EGLClientBuffer = _opaque_pointer_cls( 'EGLClientBuffer' )
EGLImageKHR = _opaque_pointer_cls( 'EGLImageKHR' )

EGLScreenMESA = ctypes.c_ulong
EGLModeMESA = ctypes.c_ulong

EGLNativeFileDescriptorKHR = ctypes.c_int

EGLSyncKHR = EGLSyncNV = _opaque_pointer_cls( 'EGLSync' )
EGLTimeKHR = EGLTimeNV = ctypes.c_ulonglong
EGLuint64KHR = EGLuint64NV = ctypes.c_ulonglong
EGLStreamKHR = _opaque_pointer_cls( 'EGLStream' )
EGLsizeiANDROID = ctypes.c_size_t

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

    
