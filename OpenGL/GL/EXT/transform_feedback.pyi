"""OpenGL.GL.EXT.transform_feedback -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray, ByteArray, ByteArrayResult, IntArray, IntArrayResult, UIntArray, UIntArrayResult

from OpenGL.raw.GL._types import *

GL_INTERLEAVED_ATTRIBS_EXT: int
GL_MAX_TRANSFORM_FEEDBACK_INTERLEAVED_COMPONENTS_EXT: int
GL_MAX_TRANSFORM_FEEDBACK_SEPARATE_ATTRIBS_EXT: int
GL_MAX_TRANSFORM_FEEDBACK_SEPARATE_COMPONENTS_EXT: int
GL_PRIMITIVES_GENERATED_EXT: int
GL_RASTERIZER_DISCARD_EXT: int
GL_SEPARATE_ATTRIBS_EXT: int
GL_TRANSFORM_FEEDBACK_BUFFER_BINDING_EXT: int
GL_TRANSFORM_FEEDBACK_BUFFER_EXT: int
GL_TRANSFORM_FEEDBACK_BUFFER_MODE_EXT: int
GL_TRANSFORM_FEEDBACK_BUFFER_SIZE_EXT: int
GL_TRANSFORM_FEEDBACK_BUFFER_START_EXT: int
GL_TRANSFORM_FEEDBACK_PRIMITIVES_WRITTEN_EXT: int
GL_TRANSFORM_FEEDBACK_VARYINGS_EXT: int
GL_TRANSFORM_FEEDBACK_VARYING_MAX_LENGTH_EXT: int

def glBeginTransformFeedbackEXT(primitiveMode: int) -> None: ...
def glBindBufferBaseEXT(target: int, index: int, buffer: int) -> None: ...
def glBindBufferOffsetEXT(target: int, index: int, buffer: int, offset: int) -> None: ...
def glBindBufferRangeEXT(target: int, index: int, buffer: int, offset: int, size: int) -> None: ...
def glEndTransformFeedbackEXT() -> None: ...
def glGetTransformFeedbackVaryingEXT(program: int, index: int, bufSize: int, length: IntArray | None = None, size: IntArray | None = None, type: UIntArray | None = None, name: ByteArray | None = None) -> tuple[IntArrayResult, ByteArrayResult, IntArrayResult, UIntArrayResult]: ...
def glTransformFeedbackVaryingsEXT(program: int, count: int, varyings: AnyArray, bufferMode: int) -> None: ...

def glInitTransformFeedbackEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
