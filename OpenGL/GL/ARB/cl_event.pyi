"""OpenGL.GL.ARB.cl_event -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray

from OpenGL.raw.GL._types import *

GL_SYNC_CL_EVENT_ARB: int
GL_SYNC_CL_EVENT_COMPLETE_ARB: int

def glCreateSyncFromCLeventARB(context: AnyArray, event: AnyArray, flags: int) -> Any: ...

def glInitClEventARB() -> bool: ...

def __getattr__(name: str) -> Any: ...
