"""OpenGL.GL.ATI.envmap_bumpmap -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import FloatArray, FloatArrayResult, IntArray, IntArrayResult

from OpenGL.raw.GL._types import *

GL_BUMP_ENVMAP_ATI: int
GL_BUMP_NUM_TEX_UNITS_ATI: int
GL_BUMP_ROT_MATRIX_ATI: int
GL_BUMP_ROT_MATRIX_SIZE_ATI: int
GL_BUMP_TARGET_ATI: int
GL_BUMP_TEX_UNITS_ATI: int
GL_DU8DV8_ATI: int
GL_DUDV_ATI: int

def glGetTexBumpParameterfvATI(pname: int, param: FloatArray | None = None) -> FloatArrayResult: ...
def glGetTexBumpParameterivATI(pname: int, param: IntArray | None = None) -> IntArrayResult: ...
def glTexBumpParameterfvATI(pname: int, param: FloatArray) -> None: ...
def glTexBumpParameterivATI(pname: int, param: IntArray) -> None: ...

def glInitEnvmapBumpmapATI() -> bool: ...

def __getattr__(name: str) -> Any: ...
