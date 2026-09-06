"""OpenGL.GL.NV.gpu_program5 -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import UIntArray, UIntArrayResult

from OpenGL.raw.GL._types import *

GL_FRAGMENT_PROGRAM_INTERPOLATION_OFFSET_BITS_NV: int
GL_MAX_FRAGMENT_INTERPOLATION_OFFSET_NV: int
GL_MAX_GEOMETRY_PROGRAM_INVOCATIONS_NV: int
GL_MAX_PROGRAM_SUBROUTINE_NUM_NV: int
GL_MAX_PROGRAM_SUBROUTINE_PARAMETERS_NV: int
GL_MAX_PROGRAM_TEXTURE_GATHER_OFFSET_NV: int
GL_MIN_FRAGMENT_INTERPOLATION_OFFSET_NV: int
GL_MIN_PROGRAM_TEXTURE_GATHER_OFFSET_NV: int

def glGetProgramSubroutineParameteruivNV(target: int, index: int, param: UIntArray | None = None) -> UIntArrayResult: ...
def glProgramSubroutineParametersuivNV(target: int, count: int, params: UIntArray) -> None: ...

def glInitGpuProgram5NV() -> bool: ...

def __getattr__(name: str) -> Any: ...
