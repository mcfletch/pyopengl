"""OpenGL.GLES2.OES.get_program_binary -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray, IntArray, UIntArray

from OpenGL.raw.GLES2._types import *

GL_NUM_PROGRAM_BINARY_FORMATS_OES: int
GL_PROGRAM_BINARY_FORMATS_OES: int
GL_PROGRAM_BINARY_LENGTH_OES: int

def glGetProgramBinaryOES(program: int, bufSize: int, length: IntArray, binaryFormat: UIntArray, binary: AnyArray) -> None: ...
def glProgramBinaryOES(program: int, binaryFormat: int, binary: AnyArray, length: int) -> None: ...

def glInitGetProgramBinaryOES() -> bool: ...

def __getattr__(name: str) -> Any: ...
