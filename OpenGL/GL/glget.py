"""Implementation of the special "glGet" functions

For comparison, here's what a straightforward implementation looks like:

    def glGetDoublev( pname ):
        "Natural writing of glGetDoublev using standard ctypes"
        output = c_double*sizes.get( pname )
        result = output()
        result = platform.PLATFORM.GL.glGetDoublev( pname, byref(result) )
        return Numeric.array( result )
"""
from OpenGL import wrapper
from OpenGL.raw.GL.VERSION import GL_1_1 as _simple
from OpenGL.raw.GL import _glgets
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

glGetString = _simple.glGetString
glGetString.restype = ctypes.c_char_p
glGetString.__doc__ = """glGetString( constant ) -> Current string value"""

GL_GET_SIZES = _glgets._glget_size_mapping
def addGLGetConstant( constant, arraySize ):
    """Add a glGet* constant to return an output array of correct size"""
    GL_GET_SIZES[ constant ] = arraySize

glGetDouble = glGetDoublev = wrapper.wrapper(_simple.glGetDoublev).setOutput(
    "data",GL_GET_SIZES, "pname", orPassIn=True
)
glGetFloat = glGetFloatv = wrapper.wrapper(_simple.glGetFloatv).setOutput(
    "data",GL_GET_SIZES, "pname", orPassIn=True
)
glGetBoolean = glGetBooleanv = glGetInteger = glGetIntegerv = wrapper.wrapper(_simple.glGetIntegerv).setOutput(
    "data",GL_GET_SIZES, "pname", orPassIn=True
)

GL_GET_LIGHT_SIZES = {
    # glGetLightXv
    _simple.GL_AMBIENT                               : (4,),
    _simple.GL_DIFFUSE                               : (4,),
    _simple.GL_SPECULAR                              : (4,),
    _simple.GL_POSITION                              : (4,),
    _simple.GL_SPOT_DIRECTION                        : (3,),
    _simple.GL_SPOT_EXPONENT                         : (1,),
    _simple.GL_SPOT_CUTOFF                           : (1,),
    _simple.GL_CONSTANT_ATTENUATION                  : (1,),
    _simple.GL_LINEAR_ATTENUATION                    : (1,),
    _simple.GL_QUADRATIC_ATTENUATION                 : (1,),
} # end of sizes
glGetLightfv = wrapper.wrapper(_simple.glGetLightfv).setOutput(
    "params",GL_GET_LIGHT_SIZES, "pname", orPassIn=True
)
glGetLightiv = wrapper.wrapper(_simple.glGetLightiv).setOutput(
    "params",GL_GET_LIGHT_SIZES, "pname", orPassIn=True
)

GL_GET_MATERIAL_SIZES = {
    _simple.GL_AMBIENT: (4,),
    _simple.GL_DIFFUSE: (4,),
    _simple.GL_SPECULAR: (4,),
    _simple.GL_EMISSION: (4,),
    _simple.GL_SHININESS: (1,),
    _simple.GL_COLOR_INDEXES: (3,)
}
glGetMaterialfv = wrapper.wrapper(_simple.glGetMaterialfv).setOutput(
    "params",GL_GET_MATERIAL_SIZES, "pname", orPassIn=True
)
glGetMaterialiv = wrapper.wrapper(_simple.glGetMaterialiv).setOutput(
    "params",GL_GET_MATERIAL_SIZES, "pname", orPassIn=True
)
PIXEL_MAP_SIZE_CONSTANT_MAP = {
    _simple.GL_PIXEL_MAP_A_TO_A: _simple.GL_PIXEL_MAP_A_TO_A_SIZE,
    _simple.GL_PIXEL_MAP_B_TO_B: _simple.GL_PIXEL_MAP_B_TO_B_SIZE,
    _simple.GL_PIXEL_MAP_G_TO_G: _simple.GL_PIXEL_MAP_G_TO_G_SIZE,
    _simple.GL_PIXEL_MAP_I_TO_A: _simple.GL_PIXEL_MAP_I_TO_A_SIZE,
    _simple.GL_PIXEL_MAP_I_TO_B: _simple.GL_PIXEL_MAP_I_TO_B_SIZE,
    _simple.GL_PIXEL_MAP_I_TO_G: _simple.GL_PIXEL_MAP_I_TO_G_SIZE,
    _simple.GL_PIXEL_MAP_I_TO_I: _simple.GL_PIXEL_MAP_I_TO_I_SIZE,
    _simple.GL_PIXEL_MAP_I_TO_R: _simple.GL_PIXEL_MAP_I_TO_R_SIZE,
    _simple.GL_PIXEL_MAP_R_TO_R: _simple.GL_PIXEL_MAP_R_TO_R_SIZE,
    _simple.GL_PIXEL_MAP_S_TO_S: _simple.GL_PIXEL_MAP_S_TO_S_SIZE,
}
def GL_GET_PIXEL_MAP_SIZE( pname ):
    """Given a pname, lookup the size using a glGet query..."""
    constant = PIXEL_MAP_SIZE_CONSTANT_MAP[ pname ]
    return glGetIntegerv( constant )
glGetPixelMapfv = wrapper.wrapper(_simple.glGetPixelMapfv).setOutput(
    "values",GL_GET_PIXEL_MAP_SIZE, "map", orPassIn=True
)
glGetPixelMapuiv = wrapper.wrapper(_simple.glGetPixelMapuiv).setOutput(
    "values",GL_GET_PIXEL_MAP_SIZE, "map", orPassIn=True
)
glGetPixelMapusv = wrapper.wrapper(_simple.glGetPixelMapusv).setOutput(
    "values",GL_GET_PIXEL_MAP_SIZE, "map", orPassIn=True
)

# 32 * 32 bits
POLYGON_STIPPLE_SIZE = (32*32//8,)
glGetPolygonStipple = glGetPolygonStippleub = wrapper.wrapper(_simple.glGetPolygonStipple).setOutput(
    "mask",POLYGON_STIPPLE_SIZE, orPassIn=True
)
GL_GET_TEX_ENV_SIZES = {
    _simple.GL_TEXTURE_ENV_MODE: (1,),
    _simple.GL_TEXTURE_ENV_COLOR: (4,),
}
glGetTexEnvfv = wrapper.wrapper(_simple.glGetTexEnvfv).setOutput(
    "params",GL_GET_TEX_ENV_SIZES, 'pname', orPassIn=True
)
glGetTexEnviv = wrapper.wrapper(_simple.glGetTexEnviv).setOutput(
    "params",GL_GET_TEX_ENV_SIZES, 'pname', orPassIn=True
)
GL_GET_TEX_GEN_SIZES = {
    _simple.GL_TEXTURE_GEN_MODE: (1,),
    _simple.GL_OBJECT_PLANE: (4,),
    _simple.GL_EYE_PLANE: (4,),
}
glGetTexGendv = wrapper.wrapper(_simple.glGetTexGendv).setOutput(
    "params",GL_GET_TEX_GEN_SIZES, 'pname', orPassIn=True
)
glGetTexGenfv = wrapper.wrapper(_simple.glGetTexGenfv).setOutput(
    "params",GL_GET_TEX_GEN_SIZES, 'pname', orPassIn=True
)
glGetTexGeniv = wrapper.wrapper(_simple.glGetTexGeniv).setOutput(
    "params",GL_GET_TEX_GEN_SIZES, 'pname', orPassIn=True
)

glGetTexLevelParameterfv = wrapper.wrapper(_simple.glGetTexLevelParameterfv).setOutput(
    "params",(1,), orPassIn=True
)
glGetTexLevelParameteriv = wrapper.wrapper(_simple.glGetTexLevelParameteriv).setOutput(
    "params",(1,), orPassIn=True
)
TEX_PARAMETER_SIZES = {
    _simple.GL_TEXTURE_MAG_FILTER: (1,),
    _simple.GL_TEXTURE_MIN_FILTER: (1,),
    _simple.GL_TEXTURE_WRAP_S: (1,),
    _simple.GL_TEXTURE_WRAP_T: (1,),
    _simple.GL_TEXTURE_BORDER_COLOR: (4,),
    _simple.GL_TEXTURE_PRIORITY: (1,),
    _simple.GL_TEXTURE_RESIDENT: (1,)
}
def addGLGetTexParameterConstant( constant, arraySize ):
    TEX_PARAMETER_SIZES[constant] = arraySize

glGetTexParameterfv = wrapper.wrapper(_simple.glGetTexParameterfv).setOutput(
    "params",TEX_PARAMETER_SIZES, 'pname', orPassIn=True
)
glGetTexParameteriv = wrapper.wrapper(_simple.glGetTexParameteriv).setOutput(
    "params",TEX_PARAMETER_SIZES, 'pname', orPassIn=True
)
