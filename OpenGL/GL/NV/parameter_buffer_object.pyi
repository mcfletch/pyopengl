"""OpenGL.GL.NV.parameter_buffer_object -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import FloatArray, IntArray, UIntArray

from OpenGL.raw.GL._types import *

GL_FRAGMENT_PROGRAM_PARAMETER_BUFFER_NV: int
GL_GEOMETRY_PROGRAM_PARAMETER_BUFFER_NV: int
GL_MAX_PROGRAM_PARAMETER_BUFFER_BINDINGS_NV: int
GL_MAX_PROGRAM_PARAMETER_BUFFER_SIZE_NV: int
GL_VERTEX_PROGRAM_PARAMETER_BUFFER_NV: int

def glProgramBufferParametersIivNV(target: int, bindingIndex: int, wordIndex: int, count: int, params: IntArray) -> None: ...
def glProgramBufferParametersIuivNV(target: int, bindingIndex: int, wordIndex: int, count: int, params: UIntArray) -> None: ...
def glProgramBufferParametersfvNV(target: int, bindingIndex: int, wordIndex: int, count: int, params: FloatArray) -> None: ...

def glInitParameterBufferObjectNV() -> bool: ...

def __getattr__(name: str) -> Any: ...
