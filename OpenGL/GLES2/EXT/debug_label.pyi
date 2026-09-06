"""OpenGL.GLES2.EXT.debug_label -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import ByteArray, IntArray

from OpenGL.raw.GLES2._types import *

GL_BUFFER_OBJECT_EXT: int
GL_PROGRAM_OBJECT_EXT: int
GL_PROGRAM_PIPELINE_OBJECT_EXT: int
GL_QUERY_OBJECT_EXT: int
GL_SAMPLER: int
GL_SHADER_OBJECT_EXT: int
GL_TRANSFORM_FEEDBACK: int
GL_VERTEX_ARRAY_OBJECT_EXT: int

def glGetObjectLabelEXT(type: int, object: int, bufSize: int, length: IntArray, label: ByteArray) -> None: ...
def glLabelObjectEXT(type: int, object: int, length: int, label: ByteArray) -> None: ...

def glInitDebugLabelEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
