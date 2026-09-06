"""OpenGL.GL.AMD.sample_positions -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import FloatArray

from OpenGL.raw.GL._types import *

GL_SUBSAMPLE_DISTANCE_AMD: int

def glSetMultisamplefvAMD(pname: int, index: int, val: FloatArray) -> None: ...

def glInitSamplePositionsAMD() -> bool: ...

def __getattr__(name: str) -> Any: ...
