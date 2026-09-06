"""OpenGL.GL.NV.register_combiners2 -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import FloatArray, FloatArrayResult

from OpenGL.raw.GL._types import *

GL_PER_STAGE_CONSTANTS_NV: int

def glCombinerStageParameterfvNV(stage: int, pname: int, params: FloatArray) -> None: ...
def glGetCombinerStageParameterfvNV(stage: int, pname: int, params: FloatArray | None = None) -> FloatArrayResult: ...

def glInitRegisterCombiners2NV() -> bool: ...

def __getattr__(name: str) -> Any: ...
