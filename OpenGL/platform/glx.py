"""GLX (x-windows)-specific platform features"""
import ctypes, ctypes.util
from OpenGL.platform import baseplatform, ctypesloader

class GLXPlatform( baseplatform.BasePlatform ):
    """Posix (Linux, FreeBSD, etceteras) implementation for PyOpenGL"""
    # On Linux (and, I assume, most GLX platforms, we have to load 
    # GL and GLU with the "global" flag to allow GLUT to resolve its
    # references to GL/GLU functions).
    try:
        GL = OpenGL = ctypesloader.loadLibrary(
            ctypes.cdll,
            'GL', 
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
    # GLX doesn't seem to have its own loadable module?
    GLX = GL
    glXGetProcAddressARB = GL.glXGetProcAddressARB
    glXGetProcAddressARB.restype = ctypes.c_void_p
    getExtensionProcedure = staticmethod( glXGetProcAddressARB )
    try:
        GLE = ctypesloader.loadLibrary(
            ctypes.cdll,
            'gle', 
            mode=ctypes.RTLD_GLOBAL 
        )
    except OSError, err:
        GLE = None

    DEFAULT_FUNCTION_TYPE = staticmethod( ctypes.CFUNCTYPE )

    # This loads the GLX functions from the GL .so, not sure if that's
    # really kosher...
    GetCurrentContext = CurrentContextIsValid = staticmethod(
        GL.glXGetCurrentContext
    )


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
