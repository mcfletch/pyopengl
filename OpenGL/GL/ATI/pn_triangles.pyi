"""OpenGL.GL.ATI.pn_triangles -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_MAX_PN_TRIANGLES_TESSELATION_LEVEL_ATI: int
GL_PN_TRIANGLES_ATI: int
GL_PN_TRIANGLES_NORMAL_MODE_ATI: int
GL_PN_TRIANGLES_NORMAL_MODE_LINEAR_ATI: int
GL_PN_TRIANGLES_NORMAL_MODE_QUADRATIC_ATI: int
GL_PN_TRIANGLES_POINT_MODE_ATI: int
GL_PN_TRIANGLES_POINT_MODE_CUBIC_ATI: int
GL_PN_TRIANGLES_POINT_MODE_LINEAR_ATI: int
GL_PN_TRIANGLES_TESSELATION_LEVEL_ATI: int

def glPNTrianglesfATI(pname: int, param: float) -> None: ...
def glPNTrianglesiATI(pname: int, param: int) -> None: ...

def glInitPnTrianglesATI() -> bool: ...

def __getattr__(name: str) -> Any: ...
