"""OpenGL.GL.NV.transform_feedback -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import ByteArray, ByteArrayResult, IntArray, IntArrayResult, UIntArray, UIntArrayResult

from OpenGL.raw.GL._types import *

GL_ACTIVE_VARYINGS_NV: int
GL_ACTIVE_VARYING_MAX_LENGTH_NV: int
GL_BACK_PRIMARY_COLOR_NV: int
GL_BACK_SECONDARY_COLOR_NV: int
GL_CLIP_DISTANCE_NV: int
GL_GENERIC_ATTRIB_NV: int
GL_INTERLEAVED_ATTRIBS_NV: int
GL_LAYER_NV: int
GL_MAX_TRANSFORM_FEEDBACK_INTERLEAVED_COMPONENTS_NV: int
GL_MAX_TRANSFORM_FEEDBACK_SEPARATE_ATTRIBS_NV: int
GL_MAX_TRANSFORM_FEEDBACK_SEPARATE_COMPONENTS_NV: int
GL_NEXT_BUFFER_NV: int
GL_PRIMITIVES_GENERATED_NV: int
GL_PRIMITIVE_ID_NV: int
GL_RASTERIZER_DISCARD_NV: int
GL_SEPARATE_ATTRIBS_NV: int
GL_SKIP_COMPONENTS1_NV: int
GL_SKIP_COMPONENTS2_NV: int
GL_SKIP_COMPONENTS3_NV: int
GL_SKIP_COMPONENTS4_NV: int
GL_TEXTURE_COORD_NV: int
GL_TRANSFORM_FEEDBACK_ATTRIBS_NV: int
GL_TRANSFORM_FEEDBACK_BUFFER_BINDING_NV: int
GL_TRANSFORM_FEEDBACK_BUFFER_MODE_NV: int
GL_TRANSFORM_FEEDBACK_BUFFER_NV: int
GL_TRANSFORM_FEEDBACK_BUFFER_SIZE_NV: int
GL_TRANSFORM_FEEDBACK_BUFFER_START_NV: int
GL_TRANSFORM_FEEDBACK_PRIMITIVES_WRITTEN_NV: int
GL_TRANSFORM_FEEDBACK_RECORD_NV: int
GL_TRANSFORM_FEEDBACK_VARYINGS_NV: int
GL_VERTEX_ID_NV: int

def glActiveVaryingNV(program: int, name: ByteArray) -> None: ...
def glBeginTransformFeedbackNV(primitiveMode: int) -> None: ...
def glBindBufferBaseNV(target: int, index: int, buffer: int) -> None: ...
def glBindBufferOffsetNV(target: int, index: int, buffer: int, offset: int) -> None: ...
def glBindBufferRangeNV(target: int, index: int, buffer: int, offset: int, size: int) -> None: ...
def glEndTransformFeedbackNV() -> None: ...
def glGetActiveVaryingNV(program: int, index: int, bufSize: int, length: IntArray | None = None, size: IntArray | None = None, type: UIntArray | None = None, name: ByteArray | None = None) -> tuple[IntArrayResult, ByteArrayResult, IntArrayResult, UIntArrayResult]: ...
def glGetTransformFeedbackVaryingNV(program: int, index: int, location: IntArray | None = None) -> IntArrayResult: ...
def glGetVaryingLocationNV(program: int, name: ByteArray) -> int: ...
def glTransformFeedbackAttribsNV(count: int, attribs: IntArray, bufferMode: int) -> None: ...
def glTransformFeedbackStreamAttribsNV(count: int, attribs: IntArray, nbuffers: int, bufstreams: IntArray, bufferMode: int) -> None: ...
def glTransformFeedbackVaryingsNV(program: int, count: int, locations: IntArray, bufferMode: int) -> None: ...

def glInitTransformFeedbackNV() -> bool: ...

def __getattr__(name: str) -> Any: ...
