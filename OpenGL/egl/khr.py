"""Data-type definitions for EGL/GLES"""
import ctypes
pointer = ctypes.pointer

EGLBoolean = ctypes.c_uint
EGLenum = ctypes.c_uint 
EGLint = ctypes.c_long
EGLConfig = ctypes.c_voidp
EGLContext = ctypes.c_voidp
EGLDisplay = ctypes.c_voidp
EGLSurface = ctypes.c_voidp
EGLClientBuffer = ctypes.c_voidp
EGLImageKHR = ctypes.c_voidp
EGLNativeFileDescriptorKHR = ctypes.c_int

EGLSyncKHR = EGLSyncNV = ctypes.c_voidp
EGLTimeKHR = EGLTimeNV = ctypes.c_ulonglong
EGLuint64KHR = EGLuint64NV = ctypes.c_ulonglong
EGLStreamKHR = ctypes.c_voidp
EGLsizeiANDROID = ctypes.c_ssize_t

class EGLClientPixmapHI( ctypes.Structure):
    _fields_ = [
        ('pData',ctypes.c_voidp),
        ('iWidth',EGLint),
        ('iHeight',EGLint),
        ('iStride',EGLint),
    ]

# These are X11... no good, really...
EGLNativeDisplayType = ctypes.c_voidp # Display *
EGLNativePixmapType = ctypes.c_voidp # Pixmap 
EGLNativeWindowType = ctypes.c_voidp # Window

NativeDisplayType = EGLNativeDisplayType 
NativePixmapType = EGLNativePixmapType
NativeWindowType = EGLNativeWindowType

