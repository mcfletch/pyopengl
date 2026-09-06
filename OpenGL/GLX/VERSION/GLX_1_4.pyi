"""OpenGL.GLX.VERSION.GLX_1_4 -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import UByteArray

from OpenGL.raw.GLX._types import *

GLX_SAMPLES: int
GLX_SAMPLE_BUFFERS: int

def glXGetProcAddress(procName: UByteArray) -> Any: ...

def glInitGlx14VERSION() -> bool: ...

def __getattr__(name: str) -> Any: ...
