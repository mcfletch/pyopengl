"""OSMesa-specific features"""
import ctypes, ctypes.util
from OpenGL.platform import baseplatform, ctypesloader

assert hasattr( ctypes, 'RTLD_GLOBAL' ), """Old ctypes without ability to load .so for global resolution: Get ctypes CVS branch_1_0, not CVS HEAD or released versions!"""


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

    #    glXGetProcAddressARB = GL.glXGetProcAddressARB
    #glXGetProcAddressARB.restype = ctypes.c_void_p
    #getExtensionProcedure = staticmethod( glXGetProcAddressARB )

    baseplatform.BasePlatform.EXPORTED_NAMES += ['OSMesaCreateContext',
        'OSMesaMakeCurrent', 'OSMesaGetCurrentContext', 'OSMesaDestroyContext']

    # export OSMesa functions from osmesa.h
    class struct_osmesa_context(ctypes.Structure):
        __slots__ = [
        ]
    struct_osmesa_context._fields_ = [
        ('_opaque_struct', ctypes.c_int)
    ]
    OSMesaContext = ctypes.POINTER(struct_osmesa_context)

    GLenum = ctypes.c_uint
    GLboolean = ctypes.c_ubyte
    GLsizei = ctypes.c_int

    OSMesaCreateContext = GL.OSMesaCreateContext
    OSMesaCreateContext.argtypes = [GLenum, OSMesaContext]
    OSMesaCreateContext.restype = OSMesaContext

    OSMesaDestroyContext = GL.OSMesaDestroyContext
    OSMesaDestroyContext.argtypes = [OSMesaContext]

    OSMesaMakeCurrent = GL.OSMesaMakeCurrent
    OSMesaMakeCurrent.argtypes = [OSMesaContext, ctypes.POINTER(None),
                                GLenum, GLsizei, GLsizei]
    OSMesaMakeCurrent.restype = GLboolean

    OSMesaGetCurrentContext = GL.OSMesaGetCurrentContext
    #OSMesaGetCurrentContext.restype = OSMesaContext
    GetCurrentContext = CurrentContextIsValid = OSMesaGetCurrentContext

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
