"""OpenGL.GL.ARB.gl_spirv -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import ByteArray, UIntArray

from OpenGL.raw.GL._types import *

GL_SHADER_BINARY_FORMAT_SPIR_V_ARB: int
GL_SPIR_V_BINARY_ARB: int

def glSpecializeShaderARB(shader: int, pEntryPoint: ByteArray, numSpecializationConstants: int, pConstantIndex: UIntArray, pConstantValue: UIntArray) -> None: ...

def glInitGlSpirvARB() -> bool: ...

def __getattr__(name: str) -> Any: ...
