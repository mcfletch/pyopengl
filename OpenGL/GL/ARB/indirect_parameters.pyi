"""OpenGL.GL.ARB.indirect_parameters -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray

from OpenGL.raw.GL._types import *

GL_PARAMETER_BUFFER_ARB: int
GL_PARAMETER_BUFFER_BINDING_ARB: int

def glMultiDrawArraysIndirectCountARB(mode: int, indirect: AnyArray, drawcount: int, maxdrawcount: int, stride: int) -> None: ...
def glMultiDrawElementsIndirectCountARB(mode: int, type: int, indirect: AnyArray, drawcount: int, maxdrawcount: int, stride: int) -> None: ...

def glInitIndirectParametersARB() -> bool: ...

def __getattr__(name: str) -> Any: ...
