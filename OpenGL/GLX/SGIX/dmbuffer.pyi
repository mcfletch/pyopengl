"""OpenGL.GLX.SGIX.dmbuffer -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray

from OpenGL.raw.GLX._types import *

GLX_DIGITAL_MEDIA_PBUFFER_SGIX: int

def glXAssociateDMPbufferSGIX(dpy: AnyArray, pbuffer: Any, params: AnyArray, dmbuffer: Any) -> int: ...

def glInitDmbufferSGIX() -> bool: ...

def __getattr__(name: str) -> Any: ...
