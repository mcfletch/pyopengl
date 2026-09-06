"""OpenGL.GL.AMD.occlusion_query_event -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_OCCLUSION_QUERY_EVENT_MASK_AMD: int
GL_QUERY_ALL_EVENT_BITS_AMD: int
GL_QUERY_DEPTH_BOUNDS_FAIL_EVENT_BIT_AMD: int
GL_QUERY_DEPTH_FAIL_EVENT_BIT_AMD: int
GL_QUERY_DEPTH_PASS_EVENT_BIT_AMD: int
GL_QUERY_STENCIL_FAIL_EVENT_BIT_AMD: int

def glQueryObjectParameteruiAMD(target: int, id: int, pname: int, param: int) -> None: ...

def glInitOcclusionQueryEventAMD() -> bool: ...

def __getattr__(name: str) -> Any: ...
