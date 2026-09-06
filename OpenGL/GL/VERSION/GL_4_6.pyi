"""OpenGL.GL.VERSION.GL_4_6 -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray, ByteArray, UIntArray

from OpenGL.raw.GL._types import *

GL_CLIPPING_INPUT_PRIMITIVES: int
GL_CLIPPING_OUTPUT_PRIMITIVES: int
GL_COMPUTE_SHADER_INVOCATIONS: int
GL_CONTEXT_FLAG_NO_ERROR_BIT: int
GL_CONTEXT_RELEASE_BEHAVIOR: int
GL_CONTEXT_RELEASE_BEHAVIOR_FLUSH: int
GL_FRAGMENT_SHADER_INVOCATIONS: int
GL_GEOMETRY_SHADER_INVOCATIONS: int
GL_GEOMETRY_SHADER_PRIMITIVES_EMITTED: int
GL_MAX_TEXTURE_MAX_ANISOTROPY: int
GL_NONE: int
GL_NUM_SPIR_V_EXTENSIONS: int
GL_PARAMETER_BUFFER: int
GL_PARAMETER_BUFFER_BINDING: int
GL_POLYGON_OFFSET_CLAMP: int
GL_PRIMITIVES_SUBMITTED: int
GL_SHADER_BINARY_FORMAT_SPIR_V: int
GL_SPIR_V_BINARY: int
GL_SPIR_V_EXTENSIONS: int
GL_TESS_CONTROL_SHADER_PATCHES: int
GL_TESS_EVALUATION_SHADER_INVOCATIONS: int
GL_TEXTURE_MAX_ANISOTROPY: int
GL_TRANSFORM_FEEDBACK_OVERFLOW: int
GL_TRANSFORM_FEEDBACK_STREAM_OVERFLOW: int
GL_VERTEX_SHADER_INVOCATIONS: int
GL_VERTICES_SUBMITTED: int

def glMultiDrawArraysIndirectCount(mode: int, indirect: AnyArray, drawcount: int, maxdrawcount: int, stride: int) -> None: ...
def glMultiDrawElementsIndirectCount(mode: int, type: int, indirect: AnyArray, drawcount: int, maxdrawcount: int, stride: int) -> None: ...
def glPolygonOffsetClamp(factor: float, units: float, clamp: float) -> None: ...
def glSpecializeShader(shader: int, pEntryPoint: ByteArray, numSpecializationConstants: int, pConstantIndex: UIntArray, pConstantValue: UIntArray) -> None: ...

def glInitGl46VERSION() -> bool: ...

def __getattr__(name: str) -> Any: ...
