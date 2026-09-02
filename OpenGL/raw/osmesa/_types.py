# mypy: ignore-errors
# The names in this module arrive from the declaration tables at import
# time, so a checker reading this file sees calls to things it cannot
# find.  The typed surface is the .pyi stub beside the package.
import ctypes
from OpenGL import _opaque
GLenum = ctypes.c_uint
GLboolean = ctypes.c_ubyte
GLsizei = ctypes.c_int
GLint = ctypes.c_int
OSMesaContext = _opaque.opaque_pointer_cls( 'OSMesaContext' )

__all__ = [
    'OSMesaContext',
]
