"""OpenGL.GL.AMD.stencil_operation_extended -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_REPLACE_VALUE_AMD: int
GL_SET_AMD: int
GL_STENCIL_BACK_OP_VALUE_AMD: int
GL_STENCIL_OP_VALUE_AMD: int

def glStencilOpValueAMD(face: int, value: int) -> None: ...

def glInitStencilOperationExtendedAMD() -> bool: ...

def __getattr__(name: str) -> Any: ...
