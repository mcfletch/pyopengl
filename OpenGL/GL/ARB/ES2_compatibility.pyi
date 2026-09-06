"""OpenGL.GL.ARB.ES2_compatibility -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray, IntArray, IntArrayResult, UIntArray

from OpenGL.raw.GL._types import *

GL_FIXED: int
GL_HIGH_FLOAT: int
GL_HIGH_INT: int
GL_IMPLEMENTATION_COLOR_READ_FORMAT: int
GL_IMPLEMENTATION_COLOR_READ_TYPE: int
GL_LOW_FLOAT: int
GL_LOW_INT: int
GL_MAX_FRAGMENT_UNIFORM_VECTORS: int
GL_MAX_VARYING_VECTORS: int
GL_MAX_VERTEX_UNIFORM_VECTORS: int
GL_MEDIUM_FLOAT: int
GL_MEDIUM_INT: int
GL_NUM_SHADER_BINARY_FORMATS: int
GL_RGB565: int
GL_SHADER_BINARY_FORMATS: int
GL_SHADER_COMPILER: int

def glClearDepthf(d: float) -> None: ...
def glDepthRangef(n: float, f: float) -> None: ...
def glGetShaderPrecisionFormat(shadertype: int, precisiontype: int, range: IntArray | None = None, precision: IntArray | None = None) -> tuple[IntArrayResult, IntArrayResult]: ...
def glReleaseShaderCompiler() -> None: ...
def glShaderBinary(count: int, shaders: UIntArray, binaryFormat: int, binary: AnyArray, length: int) -> None: ...

def glInitEs2CompatibilityARB() -> bool: ...

def __getattr__(name: str) -> Any: ...
