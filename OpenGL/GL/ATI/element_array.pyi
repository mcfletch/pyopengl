"""OpenGL.GL.ATI.element_array -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray

from OpenGL.raw.GL._types import *

GL_ELEMENT_ARRAY_ATI: int
GL_ELEMENT_ARRAY_POINTER_ATI: int
GL_ELEMENT_ARRAY_TYPE_ATI: int

def glDrawElementArrayATI(mode: int, count: int) -> None: ...
def glDrawRangeElementArrayATI(mode: int, start: int, end: int, count: int) -> None: ...
def glElementPointerATI(type: int, pointer: AnyArray) -> None: ...

def glInitElementArrayATI() -> bool: ...

def __getattr__(name: str) -> Any: ...
