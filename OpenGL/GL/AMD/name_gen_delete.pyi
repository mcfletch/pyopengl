"""OpenGL.GL.AMD.name_gen_delete -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import UIntArray, UIntArrayResult

from OpenGL.raw.GL._types import *

GL_DATA_BUFFER_AMD: int
GL_PERFORMANCE_MONITOR_AMD: int
GL_QUERY_OBJECT_AMD: int
GL_SAMPLER_OBJECT_AMD: int
GL_VERTEX_ARRAY_OBJECT_AMD: int

def glDeleteNamesAMD(identifier: int, num: int, names: UIntArray) -> None: ...
def glGenNamesAMD(identifier: int, num: int, names: UIntArray | None = None) -> UIntArrayResult: ...
def glIsNameAMD(identifier: int, name: int) -> int: ...

def glInitNameGenDeleteAMD() -> bool: ...

def __getattr__(name: str) -> Any: ...
