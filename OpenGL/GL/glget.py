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
from OpenGL.GL.VERSION import GL_1_1 as _simple
import ctypes
GLenum = ctypes.c_uint
GLsize = GLsizei = ctypes.c_int

__all__ = (
    'glGetString',
    'glGetPixelMapfv','glGetPixelMapusv','glGetPixelMapuiv',
)

glGetString = _simple.glGetString
glGetString.restype = ctypes.c_char_p
glGetString.__doc__ = """glGetString( constant ) -> Current string value"""

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
    return _simple.glGetIntegerv( constant )
glGetPixelMapfv = wrapper.wrapper(_simple.glGetPixelMapfv).setOutput(
    "values",GL_GET_PIXEL_MAP_SIZE, "map", orPassIn=True
)
glGetPixelMapuiv = wrapper.wrapper(_simple.glGetPixelMapuiv).setOutput(
    "values",GL_GET_PIXEL_MAP_SIZE, "map", orPassIn=True
)
glGetPixelMapusv = wrapper.wrapper(_simple.glGetPixelMapusv).setOutput(
    "values",GL_GET_PIXEL_MAP_SIZE, "map", orPassIn=True
)
