"""EGL (cross-platform) platform library"""
import ctypes, ctypes.util
from OpenGL.platform import baseplatform, ctypesloader

class EGLPlatform( baseplatform.BasePlatform ):
    """EGL platform for opengl-es only platforms"""
    try:
        GLES1 = ctypesloader.loadLibrary(
            ctypes.cdll,
            'GLESv1_CM', # ick
            mode=ctypes.RTLD_GLOBAL 
        )
    except OSError as err:
        GLES1 = None
    try:
        GLES2 = ctypesloader.loadLibrary(
            ctypes.cdll,
            'GLESv2', 
            mode=ctypes.RTLD_GLOBAL 
        )
    except OSError as err:
        GLES2 = None
    GLUT = None
    OpenGL = GL = GLES2
    try:
        EGL = ctypesloader.loadLibrary(
            ctypes.cdll,
            'EGL', 
            mode=ctypes.RTLD_GLOBAL 
        )
    except OSError as err:
        raise ImportError("Unable to load EGL library", *err.args)
    eglGetProcAddress = EGL.eglGetProcAddress
    eglGetProcAddress.restype = ctypes.c_void_p
    getExtensionProcedure = staticmethod( eglGetProcAddress )
    try:
        GLE = ctypesloader.loadLibrary(
            ctypes.cdll,
            'gle', 
            mode=ctypes.RTLD_GLOBAL 
        )
    except OSError as err:
        GLE = None

    DEFAULT_FUNCTION_TYPE = staticmethod( ctypes.CFUNCTYPE )

    GetCurrentContext = CurrentContextIsValid = staticmethod(
        EGL.eglGetCurrentContext
    )
    
    safeGetError = staticmethod( OpenGL.glGetError )
