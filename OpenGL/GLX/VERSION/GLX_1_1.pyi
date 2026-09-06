"""OpenGL.GLX.VERSION.GLX_1_1 -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray

from OpenGL.raw.GLX._types import *

GLX_EXTENSIONS: int
GLX_VENDOR: int
GLX_VERSION: int

def glXGetClientString(dpy: AnyArray, name: int) -> bytes: ...
def glXQueryExtensionsString(dpy: AnyArray, screen: int) -> bytes: ...
def glXQueryServerString(dpy: AnyArray, screen: int, name: int) -> bytes: ...

def glInitGlx11VERSION() -> bool: ...

def __getattr__(name: str) -> Any: ...
