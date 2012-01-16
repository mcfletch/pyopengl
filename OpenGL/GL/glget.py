"""Implementation of the special "glGet" functions

For comparison, here's what a straightforward implementation looks like:

    def glGetDoublev( pname ):
        "Natural writing of glGetDoublev using standard ctypes"
        output = c_double*sizes.get( pname )
        result = output()
        result = platform.OpenGL.glGetDoublev( pname, byref(result) )
        return Numeric.array( result )
"""
from OpenGL import platform, arrays, error, wrapper, converters
from OpenGL.raw.GL.VERSION import GL_1_1 as simple
import ctypes
GLenum = ctypes.c_uint
GLsize = GLsizei = ctypes.c_int

__all__ = (
    'glGetBoolean','glGetBooleanv','glGetInteger','glGetIntegerv',
    'glGetFloat','glGetFloatv','glGetDouble','glGetDoublev',
    'glGetString',
    'glGetLightfv','glGetLightiv',
    'glGetMaterialfv','glGetMaterialiv',
    'glGetPixelMapfv','glGetPixelMapusv','glGetPixelMapuiv',
    'glGetPolygonStipple', 'glGetPolygonStippleub',
    'glGetTexEnviv','glGetTexEnvfv',
    'glGetTexGenfv','glGetTexGeniv','glGetTexGendv',
    'glGetTexLevelParameteriv',
    'glGetTexLevelParameterfv',
    'glGetTexParameterfv',
    'glGetTexParameteriv',
)

glGetString = simple.glGetString
glGetString.restype = ctypes.c_char_p
glGetString.__doc__ = """glGetString( constant ) -> Current string value"""

GL_GET_SIZES = simple._GLGET_CONSTANTS
def addGLGetConstant( constant, arraySize ):
    """Add a glGet* constant to return an output array of correct size"""
    GL_GET_SIZES[ constant ] = arraySize
glGetDouble = glGetDoublev = wrapper.wrapper(simple.glGetDoublev).setOutput(
    "params",GL_GET_SIZES, "pname",
)
glGetFloat = glGetFloatv = wrapper.wrapper(simple.glGetFloatv).setOutput(
    "params",GL_GET_SIZES, "pname",
)
glGetBoolean = glGetBooleanv = glGetInteger = glGetIntegerv = wrapper.wrapper(simple.glGetIntegerv).setOutput(
    "params",GL_GET_SIZES, "pname",
)

GL_GET_LIGHT_SIZES = {
    # glGetLightXv
    simple.GL_AMBIENT                               : (4,),
    simple.GL_DIFFUSE                               : (4,),
    simple.GL_SPECULAR                              : (4,),
    simple.GL_POSITION                              : (4,),
    simple.GL_SPOT_DIRECTION                        : (3,),
    simple.GL_SPOT_EXPONENT                         : (1,),
    simple.GL_SPOT_CUTOFF                           : (1,),
    simple.GL_CONSTANT_ATTENUATION                  : (1,),
    simple.GL_LINEAR_ATTENUATION                    : (1,),
    simple.GL_QUADRATIC_ATTENUATION                 : (1,),
} # end of sizes
glGetLightfv = wrapper.wrapper(simple.glGetLightfv).setOutput(
    "params",GL_GET_LIGHT_SIZES, "pname",
)
glGetLightiv = wrapper.wrapper(simple.glGetLightiv).setOutput(
    "params",GL_GET_LIGHT_SIZES, "pname",
)

GL_GET_MATERIAL_SIZES = {
    simple.GL_AMBIENT: (4,),
    simple.GL_DIFFUSE: (4,),
    simple.GL_SPECULAR: (4,),
    simple.GL_EMISSION: (4,),
    simple.GL_SHININESS: (1,),
    simple.GL_COLOR_INDEXES: (3,)
}
glGetMaterialfv = wrapper.wrapper(simple.glGetMaterialfv).setOutput(
    "params",GL_GET_MATERIAL_SIZES, "pname",
)
glGetMaterialiv = wrapper.wrapper(simple.glGetMaterialiv).setOutput(
    "params",GL_GET_MATERIAL_SIZES, "pname",
)
PIXEL_MAP_SIZE_CONSTANT_MAP = {
    simple.GL_PIXEL_MAP_A_TO_A: simple.GL_PIXEL_MAP_A_TO_A_SIZE,
    simple.GL_PIXEL_MAP_B_TO_B: simple.GL_PIXEL_MAP_B_TO_B_SIZE,
    simple.GL_PIXEL_MAP_G_TO_G: simple.GL_PIXEL_MAP_G_TO_G_SIZE,
    simple.GL_PIXEL_MAP_I_TO_A: simple.GL_PIXEL_MAP_I_TO_A_SIZE,
    simple.GL_PIXEL_MAP_I_TO_B: simple.GL_PIXEL_MAP_I_TO_B_SIZE,
    simple.GL_PIXEL_MAP_I_TO_G: simple.GL_PIXEL_MAP_I_TO_G_SIZE,
    simple.GL_PIXEL_MAP_I_TO_I: simple.GL_PIXEL_MAP_I_TO_I_SIZE,
    simple.GL_PIXEL_MAP_I_TO_R: simple.GL_PIXEL_MAP_I_TO_R_SIZE,
    simple.GL_PIXEL_MAP_R_TO_R: simple.GL_PIXEL_MAP_R_TO_R_SIZE,
    simple.GL_PIXEL_MAP_S_TO_S: simple.GL_PIXEL_MAP_S_TO_S_SIZE,
}
def GL_GET_PIXEL_MAP_SIZE( pname ):
    """Given a pname, lookup the size using a glGet query..."""
    constant = PIXEL_MAP_SIZE_CONSTANT_MAP[ pname ]
    return glGetIntegerv( constant )
glGetPixelMapfv = wrapper.wrapper(simple.glGetPixelMapfv).setOutput(
    "values",GL_GET_PIXEL_MAP_SIZE, "map",
)
glGetPixelMapuiv = wrapper.wrapper(simple.glGetPixelMapuiv).setOutput(
    "values",GL_GET_PIXEL_MAP_SIZE, "map",
)
glGetPixelMapusv = wrapper.wrapper(simple.glGetPixelMapusv).setOutput(
    "values",GL_GET_PIXEL_MAP_SIZE, "map",
)

# 32 * 32 bits
POLYGON_STIPPLE_SIZE = (32*32//8,)
glGetPolygonStipple = glGetPolygonStippleub = wrapper.wrapper(simple.glGetPolygonStipple).setOutput(
    "mask",POLYGON_STIPPLE_SIZE,
)
GL_GET_TEX_ENV_SIZES = {
    simple.GL_TEXTURE_ENV_MODE: (1,),
    simple.GL_TEXTURE_ENV_COLOR: (4,),
}
glGetTexEnvfv = wrapper.wrapper(simple.glGetTexEnvfv).setOutput(
    "params",GL_GET_TEX_ENV_SIZES, 'pname',
)
glGetTexEnviv = wrapper.wrapper(simple.glGetTexEnviv).setOutput(
    "params",GL_GET_TEX_ENV_SIZES, 'pname',
)
GL_GET_TEX_GEN_SIZES = {
    simple.GL_TEXTURE_GEN_MODE: (1,),
    simple.GL_OBJECT_PLANE: (4,),
    simple.GL_EYE_PLANE: (4,),
}
glGetTexGendv = wrapper.wrapper(simple.glGetTexGendv).setOutput(
    "params",GL_GET_TEX_GEN_SIZES, 'pname',
)
glGetTexGenfv = wrapper.wrapper(simple.glGetTexGenfv).setOutput(
    "params",GL_GET_TEX_GEN_SIZES, 'pname',
)
glGetTexGeniv = wrapper.wrapper(simple.glGetTexGeniv).setOutput(
    "params",GL_GET_TEX_GEN_SIZES, 'pname',
)

glGetTexLevelParameterfv = wrapper.wrapper(simple.glGetTexLevelParameterfv).setOutput(
    "params",(1,)
)
glGetTexLevelParameteriv = wrapper.wrapper(simple.glGetTexLevelParameteriv).setOutput(
    "params",(1,)
)
TEX_PARAMETER_SIZES = {
    simple.GL_TEXTURE_MAG_FILTER: (1,),
    simple.GL_TEXTURE_MIN_FILTER: (1,),
    simple.GL_TEXTURE_WRAP_S: (1,),
    simple.GL_TEXTURE_WRAP_T: (1,),
    simple.GL_TEXTURE_BORDER_COLOR: (4,),
    simple.GL_TEXTURE_PRIORITY: (1,),
    simple.GL_TEXTURE_RESIDENT: (1,)
}
def addGLGetTexParameterConstant( constant, arraySize ):
    TEX_PARAMETER_SIZES[constant] = arraySize

glGetTexParameterfv = wrapper.wrapper(simple.glGetTexParameterfv).setOutput(
    "params",TEX_PARAMETER_SIZES, 'pname',
)
glGetTexParameteriv = wrapper.wrapper(simple.glGetTexParameteriv).setOutput(
    "params",TEX_PARAMETER_SIZES, 'pname',
)
