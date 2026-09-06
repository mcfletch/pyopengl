"""OpenGL.GLES2.ANGLE.translated_shader_source -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import ByteArray, IntArray

from OpenGL.raw.GLES2._types import *

GL_TRANSLATED_SHADER_SOURCE_LENGTH_ANGLE: int

def glGetTranslatedShaderSourceANGLE(shader: int, bufSize: int, length: IntArray, source: ByteArray) -> None: ...

def glInitTranslatedShaderSourceANGLE() -> bool: ...

def __getattr__(name: str) -> Any: ...
