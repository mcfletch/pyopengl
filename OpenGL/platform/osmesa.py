"""OSMesa-specific features

To request an OSMesa context, you need to run your script with:

    PYOPENGL_PLATFORM=osmesa

defined in your shell/execution environment.
"""
import ctypes, ctypes.util
from OpenGL.platform import baseplatform, ctypesloader
from OpenGL.constant import Constant

class OSMesaPlatform( baseplatform.BasePlatform ):
    """OSMesa implementation for PyOpenGL"""
    try:
        GL = OpenGL = ctypesloader.loadLibrary(
            ctypes.cdll,
            'OSMesa', 
            mode=ctypes.RTLD_GLOBAL 
        )
    except OSError, err:
        raise ImportError("Unable to load OpenGL library", *err.args)
    try:
        GLU = ctypesloader.loadLibrary(
            ctypes.cdll,
            'GLU',
            mode=ctypes.RTLD_GLOBAL 
        )
    except OSError, err:
        GLU = None
    # glut shouldn't need to be global, but just in case a dependent library makes
    # the same assumption GLUT does...
    try:
        GLUT = ctypesloader.loadLibrary(
            ctypes.cdll,
            'glut', 
            mode=ctypes.RTLD_GLOBAL 
        )
    except OSError, err:
        GLUT = None

    try:
        GLE = ctypesloader.loadLibrary(
            ctypes.cdll,
            'gle', 
            mode=ctypes.RTLD_GLOBAL 
        )
    except OSError, err:
        GLE = None

    DEFAULT_FUNCTION_TYPE = staticmethod( ctypes.CFUNCTYPE )

    GLenum = ctypes.c_uint
    GLboolean = ctypes.c_ubyte
    GLsizei = ctypes.c_int
    GLint = ctypes.c_int

    baseplatform.BasePlatform.EXPORTED_NAMES += ['OSMesaCreateContext',
        'OSMesaCreateContextExt', 'OSMesaMakeCurrent', 'OSMesaGetIntegerv',
        'OSMesaGetCurrentContext', 'OSMesaDestroyContext', 'OSMesaPixelStore',
        'OSMesaGetDepthBuffer', 'OSMesaGetColorBuffer',
        'OSMESA_COLOR_INDEX', 'OSMESA_RGBA', 'OSMESA_BGRA', 'OSMESA_ARGB',
        'OSMESA_RGB', 'OSMESA_BGR', 'OSMESA_BGR', 'OSMESA_ROW_LENGTH',
        'OSMESA_Y_UP', 'OSMESA_WIDTH', 'OSMESA_HEIGHT', 'OSMESA_FORMAT',
        'OSMESA_TYPE', 'OSMESA_MAX_WIDTH', 'OSMESA_MAX_HEIGHT']

    # export OSMesa functions from osmesa.h
    class struct_osmesa_context(ctypes.Structure):
        __slots__ = [
        ]
    struct_osmesa_context._fields_ = [
        ('_opaque_struct', ctypes.c_int)
    ]
    OSMesaContext = ctypes.POINTER(struct_osmesa_context)

    # Values for the format parameter of OSMesaCreateContext()
    OSMESA_COLOR_INDEX = Constant('OSMESA_COLOR_INDEX', 6400)
    OSMESA_RGBA = Constant('OSMESA_RGBA', 6408)
    OSMESA_BGRA = Constant('OSMESA_BGRA', 0x1)
    OSMESA_ARGB = Constant('OSMESA_ARGB', 0x2)
    OSMESA_RGB = Constant('OSMESA_RGB', 6407)
    OSMESA_BGR = Constant('OSMESA_BGR',	0x4)
    OSMESA_RGB_565 = Constant('OSMESA_BGR', 0x5)

    # OSMesaPixelStore() parameters:
    OSMESA_ROW_LENGTH = Constant('OSMESA_ROW_LENGTH', 0x10)
    OSMESA_Y_UP = Constant('OSMESA_Y_UP', 0x11)

    # Accepted by OSMesaGetIntegerv:
    OSMESA_WIDTH = Constant('OSMESA_WIDTH', 0x20)
    OSMESA_HEIGHT = Constant('OSMESA_HEIGHT', 0x21)
    OSMESA_FORMAT = Constant('OSMESA_FORMAT', 0x22)
    OSMESA_TYPE = Constant('OSMESA_TYPE', 0x23)
    OSMESA_MAX_WIDTH = Constant('OSMESA_MAX_WIDTH', 0x24)
    OSMESA_MAX_HEIGHT = Constant('OSMESA_MAX_HEIGHT', 0x25)

    OSMesaCreateContext = GL.OSMesaCreateContext
    OSMesaCreateContext.argtypes = [GLenum, OSMesaContext]
    OSMesaCreateContext.restype = OSMesaContext
    
    OSMesaCreateContextExt = GL.OSMesaCreateContextExt
    OSMesaCreateContextExt.argtypes = [GLenum, GLint, GLint, GLint,
                                       OSMesaContext]
    OSMesaCreateContextExt.restype = OSMesaContext

    OSMesaDestroyContext = GL.OSMesaDestroyContext
    OSMesaDestroyContext.argtypes = [OSMesaContext]

    OSMesaMakeCurrent = GL.OSMesaMakeCurrent
    OSMesaMakeCurrent.argtypes = [OSMesaContext, ctypes.POINTER(None),
                                GLenum, GLsizei, GLsizei]
    OSMesaMakeCurrent.restype = GLboolean

    OSMesaGetCurrentContext = GL.OSMesaGetCurrentContext
    #OSMesaGetCurrentContext.restype = OSMesaContext
    GetCurrentContext = CurrentContextIsValid = OSMesaGetCurrentContext

    OSMesaPixelStore = GL.OSMesaPixelStore
    OSMesaPixelStore.argtypes = [GLint, GLint]
    OSMesaPixelStore.restype = None

    OSMesaGetProcAddress = GL.OSMesaGetProcAddress
    OSMesaGetProcAddress.restype = ctypes.c_void_p
    getExtensionProcedure = staticmethod( OSMesaGetProcAddress )

    def OSMesaGetIntegerv(self, pname):
        value = self.GLint()
        self.GL.OSMesaGetIntegerv(pname, ctypes.byref(value))
        return value.value

    def OSMesaGetDepthBuffer(self, c):
        width, height, bytesPerValue = self.GLint(), self.GLint(), self.GLint()
        buffer = ctypes.POINTER(self.GLint)()

        if self.GL.OSMesaGetDepthBuffer(c, ctypes.byref(width),
                                        ctypes.byref(height),
                                        ctypes.byref(bytesPerValue),
                                        ctypes.byref(buffer)):
            return width.value, height.value, bytesPerValue.value, buffer
        else:
            return 0, 0, 0, None

    def OSMesaGetColorBuffer(self, c):
        # TODO: make output array types which can handle the operation 
        # provide an API to convert pointers + sizes to array instances,
        # e.g. numpy.ctypeslib.as_array( ptr, bytesize ).astype( 'B' ).reshape( height,width )
        width, height, format = self.GLint(), self.GLint(), self.GLint()
        buffer = ctypes.c_void_p()

        if self.GL.OSMesaGetColorBuffer(c, ctypes.byref(width),
                                        ctypes.byref(height),
                                        ctypes.byref(format),
                                        ctypes.byref(buffer)):
            return width.value, height.value, format.value, buffer
        else:
            return 0, 0, 0, None

    def getGLUTFontPointer( self, constant ):
        """Platform specific function to retrieve a GLUT font pointer
        
        GLUTAPI void *glutBitmap9By15;
        #define GLUT_BITMAP_9_BY_15		(&glutBitmap9By15)
        
        Key here is that we want the addressof the pointer in the DLL,
        not the pointer in the DLL.  That is, our pointer is to the 
        pointer defined in the DLL, we don't want the *value* stored in
        that pointer.
        """
        name = [ x.title() for x in constant.split( '_' )[1:] ]
        internal = 'glut' + "".join( [x.title() for x in name] )
        pointer = ctypes.c_void_p.in_dll( self.GLUT, internal )
        return ctypes.c_void_p(ctypes.addressof(pointer))
    
    safeGetError = staticmethod( OpenGL.glGetError )
