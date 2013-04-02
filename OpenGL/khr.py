"""Data-type definitions for EGL/GLES"""
import ctypes
pointer = ctypes.pointer

EGLBoolean = ctypes.c_uint32
EGLenum = ctypes.c_uint32
EGLint = c_int = ctypes.c_int32

class _Opaque( ctypes.Structure ):
    """An Opaque Structure reference (base class)"""
class _opaque_pointer( ctypes.POINTER( _Opaque ) ):
    _type_ = _Opaque
    @classmethod
    def from_param( cls, value ):
        return ctypes.cast( value, cls )
    @property
    def address( self ):
        return ctypes.addressof( self.contents )
    @property 
    def as_voidp( self ):
        return ctypes.c_voidp( self.address )

def _opaque_pointer_cls( name ):
    """Create an Opaque pointer class for the given name"""
    typ = type( name, (_Opaque,), {} )
    p_typ = type( name+'_pointer', (_opaque_pointer,), {'_type_':typ})
    return p_typ

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

