"""OpenGL.GL.ARB.get_program_binary -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray, AnyArrayResult, IntArray, IntArrayResult, UIntArray, UIntArrayResult

from OpenGL.raw.GL._types import *

GL_NUM_PROGRAM_BINARY_FORMATS: int
GL_PROGRAM_BINARY_FORMATS: int
GL_PROGRAM_BINARY_LENGTH: int
GL_PROGRAM_BINARY_RETRIEVABLE_HINT: int

def glGetProgramBinary(program: int, bufSize: int, length: IntArray | None = None, binaryFormat: UIntArray | None = None, binary: AnyArray | None = None) -> tuple[AnyArrayResult, UIntArrayResult, IntArrayResult]: ...
def glProgramBinary(program: int, binaryFormat: int, binary: AnyArray, length: int) -> None: ...
def glProgramParameteri(program: int, pname: int, value: int) -> None: ...

def glInitGetProgramBinaryARB() -> bool: ...

def __getattr__(name: str) -> Any: ...
